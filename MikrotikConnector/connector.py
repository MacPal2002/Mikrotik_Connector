import re, time, paramiko, tempfile, os
from datetime import datetime
from packaging.version import Version, InvalidVersion
import socket


class MikrotikDevice:
    def __init__(self):
        self.client = None
        self.now = datetime.now()
        self.current_datetime = self.now.strftime("%d-%m-%Y_%H-%M-%S")
        self.last_backup = {}
        self.last_export = {}
        self.tempdir = tempfile.gettempdir().replace("\\", "/") + "/"


    def connect(self, ip_address, username, password, port=22):

        # Establish an SSH connection to the Mikrotik device.

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(ip_address, username=username, password=password, port=port, timeout=5, allow_agent=False, look_for_keys=False)

        except paramiko.AuthenticationException:
            raise ValueError("Authentication failed. Check username and password")
        except socket.timeout:
            raise ConnectionError("Connection timed out")
        except Exception as e:
            raise ConnectionError(f"Connection failed. Details: {str(e)}")


    def disconnect(self):
        # Close the SSH connection.
        if self.client:
            self.client.close()

    def send_command(self, command, wait_time=1, max_attempts=10):

        if not self.client:
            raise ConnectionError("Not connected to the device")
        
        # Execute a command on the Mikrotik device and return the result.

        stdin, stdout, stderr = self.client.exec_command(command)

        attempts = 0
        while not stdout.channel.recv_ready() and attempts < max_attempts:

            # If there's an error or the command has finished executing, break
            
            if stderr.channel.recv_ready() or stdout.channel.exit_status_ready():
                break
            
            time.sleep(wait_time)
            attempts += 1

        if attempts == max_attempts:
            raise TimeoutError("Command execution timed out")

        return stdout.read().decode('utf-8').strip()



    def get_export_configuration(self):
        
        # Retrieve the device's configuration.

        return self.send_command("/export terse")

    def get_identity(self):

        # Retrieve the device's identity (hostname).

        output = self.send_command("/system identity print")
        for line in output.splitlines():
            parsed = re.sub(" +", "", line).strip().split(":")
            if parsed:
                return parsed[1]
            
    def get_license_level(self):

        # Get the license level of Router OS

        ros_license_level = self.send_command(":put [/system license get nlevel]")
        if "input does not match" in ros_license_level:
            ros_license_level = self.send_command(":put [/system license get level]")
        return int(ros_license_level)

    def get_wlan_info(self, interface, value):
        
        # Retrieve information about the device's wireless LAN.

        command = f':put [/interface wireless get [find default-name={interface}] {value}]'
        return self.send_command(command)

    def get_wlan_sec(self, profile_name):

        # Retrieve the security settings for the specified WLAN profile.

        command = f':put [/interface wireless security-profiles get [find name={profile_name}] wpa2-pre-shared-key]'
        return self.send_command(command)
    
    def get_interfaces(self):

        # Retrieve details about the device's interfaces.

        return self.parse_interfaces(self.send_command("/interface print detail without-paging"))
    

    def get_ip_addresses(self):

        self.ip_addresses = []
        self.output = self.send_command("/ip addr print without-paging")
        print(self.output)

        for line in self.output.splitlines():
            ip_address = {}
            # Sprawdzamy, czy linia zaczyna się od cyfry (czy jest to wpis z adresem IP)

            if re.search("^\d", line):
                ip_address["address"] = self.search_attribute(line, r"(\d+\.\d+\.\d+\.\d+/\d+)")
                ip_address["network"] = self.search_attribute(line, r"(\d+\.\d+\.\d+\.\d+)\s+")
                ip_address["interface"] = self.search_attribute(line, r"\s([^\s]+)$")

                # Sprawdzamy, czy jest flaga DYNAMIC

                if "D" in line.split()[1]:
                    ip_address["flag"] = "DYNAMIC"
                else:
                    ip_address["flag"] = "STATIC"
                self.ip_addresses.append(ip_address)

        return self.ip_addresses
    
    def get_resources(self):

        self.resources = {}
        self.output = self.send_command("/system resource print")        

        for line in self.output.splitlines():            
            parsed = line.replace(": ", ":").replace("MiB", " MiB").replace("KiB", " KiB").replace("MHz", " MHz").replace("%", " %").strip().split(":")

            if parsed[0] != "":
                if parsed[0] == "uptime":
                    parsed[1] = parsed[1].replace("y", "y ").replace("w", "w ").replace("d", "d ").replace("h", "h ").replace("m", "m ")
                    self.resources[parsed[0]] = parsed[1]

                if parsed[0] == "build-time":
                    self.resources[parsed[0]] = parsed[1] + ":" + parsed[2] + ":" + parsed[3]

                else:
                    self.resources[parsed[0]] = parsed[1]

        return self.resources
    
    def get_routes(self):

        print("*** INFO ***: This process may take some time to get info depending on how many routes have in your device. Please wait...")

        self.routes = []
        filename = f"routes_{self.get_identity()}.txt"

        self.send_command(f"/ip route print detail terse without-paging file={filename}", max_attempts=40)
        self.download_file(filename, self.tempdir)

        with open(self.tempdir + filename, "r") as routes:

            for line in routes:
                parsed = re.sub(" +", " ", line).strip()            

                if re.search("^([0-9]|[1-9][0-9]{1,5}|[1-7][0-9]{6}|8000000)", parsed):
                    route = {}

                    route_line = parsed.split(" ")

                    route['flags'] = route_line[1]
                    route["destination"] = self.search_attribute(parsed, r'dst-address=(.*?) [a-z]')
                    route["gateway"] = self.search_attribute(parsed, r'gateway=(.*?) [a-z]') or ""
                    route["distance"] = self.search_attribute(parsed, r'distance=(.*?) [a-z]')

                    self.routes.append(route)

        self.send_command(f"/file remove {filename}")
        os.remove(self.tempdir + filename)

        return self.routes

    
        
    def get_services(self):

        self.services = []        
        self.output = self.send_command("/ip service print without-paging")        

        for line in self.output.splitlines():
            service = {}

            parsed = re.sub(" +", " ", line).strip().split(" ")            

            if re.search("^([0-9]|1[0-9]|2[0-9])", parsed[0]):
                if re.search("[XI]", parsed[1]):
                    service['enabled'] = False
                    service["name"] = parsed[2]
                    service["port"] = parsed[3]
                else:
                    service['enabled'] = True
                    service["name"] = parsed[1]
                    service["port"] = parsed[2]
                
                self.services.append(service)

        return self.services
    

    def get_users(self):

        self.users = []
        self.output = self.send_command("/user print")        

        for line in self.output.splitlines():
            user = {}
            parsed = re.sub(" +", " ", line).strip().split(" ")

            if re.search("^([0-9]|1[0-9]|2[0-9])", parsed[0]):
                user["username"] = parsed[1]
                user["group"] = parsed[2]            
                self.users.append(user)

        return self.users 


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> UPDATE methods

    def update_address_pool(self, pool_name, addresses=None, next_pool=None, new_pool_name=None):
 
        self.cmd = f"/ip pool set {pool_name}"

        if new_pool_name is not None:
            self.cmd += f" name={new_pool_name}"

        if addresses is not None:
            self.cmd += f" ranges={addresses}"

        if next_pool is not None:
            self.cmd += f" next-pool={next_pool}"

        return self.check_result(self.send_command(self.cmd))
    
    def update_dhcp_client(self, interface, disabled, add_default_route, route_distance, use_peer_dns, use_peer_ntp):
  
        return self.check_result(self.send_command(f"/ip dhcp-client set numbers=[find interface=\"{interface}\"] disabled={disabled} add-default-route={add_default_route} default-route-distance={route_distance} use-peer-dns={use_peer_dns} use-peer-ntp={use_peer_ntp}"))
    

    def update_dhcp_server_server(self, interface, disabled=None, name=None, lease_time=None, address_pool=None):
        
        self.cmd = f"/ip dhcp-server set numbers=[find interface=\"{interface}\"]"

        if disabled is not None:
            self.cmd += f" disabled={disabled}"

        if name is not None:
            self.cmd += f" name={name}"

        if lease_time is not None:
            self.cmd += f" lease-time={lease_time}"

        if address_pool is not None:
            self.cmd += f" address-pool={address_pool}"

        return self.check_result(self.send_command(self.cmd))
    
    def update_dhcp_server_network(self, address, gateway=None, netmask=None, dns_server=None, ntp_server=None):
        
        get_networks = self.send_command("/ip dhcp-server network print")

        network_match = False
        network_count = 0

        for network in get_networks.splitlines():
            parsed_line = re.sub(" +", " ", network).strip().split(" ")

            if re.search("^\d+", parsed_line[0]):
                network_count += 1

                if parsed_line[1] == address:
                    network_match = True

                    self.cmd = f"/ip dhcp-server network set numbers=[find address=\"{address}\"]"

                    if gateway is not None:
                        self.cmd += f" gateway={gateway}"

                    if netmask is not None:
                        self.cmd += f" netmask={netmask}"

                    if dns_server is not None:
                        self.cmd += f" dns-server={dns_server}"

                    if ntp_server is not None:
                        self.cmd += f" ntp-server={ntp_server}"                    

                    return self.check_result(self.send_command(self.cmd))

        if network_count == 0:
            return "ERROR: There are not any created network. Please, create it first"

        if network_match == False:
            return "ERROR: There are not any network with specified address"
        
    
    def update_identity(self, name):
        
        return self.check_result(self.send_command(f"/system identity set name={name}"))
    
    def update_ip_address(self, interface, address, disabled="no"):
        
        return self.check_result(self.send_command(f"/ip address set address={address} disabled={disabled} [find interface=\"{interface}\"]"))
    
    def update_services(self, service, disabled, port=None, address=None):
        
        self.cmd = f"/ip service set {service} disabled={disabled}"

        if port != None:
            self.cmd += f" port={port}"
        
        if address != None:
            self.cmd += f" address={address}"

        return self.check_result(self.send_command(self.cmd))
    
    def update_user(self, username, password, group):
        
        self.cmd = f"/user set {username}"        

        if password != "":
            self.cmd += f" password={password}"

        if group != "":
            self.cmd += f" group={group}"

        return self.check_result(self.send_command(self.cmd))



    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CREATE methods
    def create_address_pool(self, name, range, next_pool="none"):
        
        return self.check_result(self.send_command(f"/ip pool add name={name} ranges={range} next-pool={next_pool}"))
    
    def create_dhcp_client(self, interface, disabled="no", add_default_route="yes", route_distance=1, use_peer_dns="yes", use_peer_ntp="yes"):
        
        return self.check_result(self.send_command(f"""
            /ip dhcp-client add interface=\"{interface}\" disabled={disabled} add-default-route={add_default_route} default-route-distance={route_distance} use-peer-dns={use_peer_dns} use-peer-ntp={use_peer_ntp}
            """))
    
    def create_dhcp_server(self, interface, network_address=None, disabled="no", name="dhcp_server", address_pool="static-only", lease_time="00:10:00", dns_server="1.1.1.1,9.9.9.9"):

        server_cmd = self.check_result(self.send_command(f"/ip dhcp-server add disabled={disabled} interface=\"{interface}\" name={name} address-pool={address_pool} lease-time={lease_time}"))
        
        if server_cmd != True:
            return server_cmd

        ip_addresses = self.get_ip_addresses()
        available_ip_addresses = [ip for ip in ip_addresses if ip['interface'] == interface]
        
        if len(available_ip_addresses) == 0 and not network_address:
            raise ValueError(f"ERROR: No IP address provided as 'network_address' and none is assigned to the interface '{interface}'.")

        if len(available_ip_addresses) == 1 or network_address:
            if not network_address:
                ip_address = available_ip_addresses[0]
            else:
                ip_address = {'address': network_address, 'network': network_address.split('/')[0]}

            network, prefix = ip_address['address'].split('/')
            address = ip_address['network'] + "/" + prefix
            gateway = ip_address['address'].split('/')[0]

            network_cmd = self.check_result(self.send_command(f"/ip dhcp-server network add address={address} gateway={gateway} dns-server={dns_server}"))

            if network_cmd != True:
                return network_cmd
        else:
            raise ValueError(f"ERROR: Multiple IP addresses assigned to the interface '{interface}'. Specify 'network_address' or ensure only one IP is assigned. IPs: {[ip['address'] for ip in available_ip_addresses]}")

        return True
    
    def create_ip_address(self, ip_address, interface):
        
        return self.check_result(self.send_command(f"/ip address add address={ip_address} interface=\"{interface}\""))
    
    def create_route(self, dst_address, gateway, distance, disabled="no"):
        
        return self.check_result(self.send_command(f"/ip route add dst-address={dst_address} gateway={gateway} distance={distance} disabled={disabled}"))
    
    def create_user(self, username, password, group):
        
        return self.check_result(self.send_command(f"/user add name={username} password={password} group={group}"))
    
    def configure_wlan_security(self, profile_name, password):

        security_settings = (f'/interface wireless security-profiles add name={profile_name} mode=dynamic-keys authentication-types=wpa2-psk,wpa2-eap unicast-ciphers=aes-ccm,tkip group-ciphers=aes-ccm,tkip wpa2-pre-shared-key="{password}"')
        self.send_command(security_settings)
    
    def configure_wlan(self, ssid, password, country="south africa"):
        
        self.reset_wireless_config()
        self.send_command("/interface wireless security-profiles remove auto_wlan")
        self.configure_wlan_security('auto_wlan', password)

        radio_mode = "bridge" if self.get_license_level() < 4 else "ap-bridge"

        detail_lines = self.send_command("/interface wireless print detail").splitlines()

        interfaces = []

        for line in detail_lines:
            if "name" in line:
                interface_name = self.search_attribute(r'name="([^"]+)"', line)
                hw_info = self.send_command(f"/interface wireless info hw-info {interface_name}")
                ranges = re.search(r"ranges: (\d+)-(\d+)/\d/(.*)", hw_info)
                if ranges:
                    lower_freq, _, channel_info = ranges.groups()

                    if 2300 <= int(lower_freq) <= 2500:
                        freq_band = '2ghz'
                    elif 4920 <= int(lower_freq) <= 6100:
                        freq_band = '5ghz'

                    channel_width_val = self.search_attribute(r"(\d+)", channel_info.split(',')[-1])

                    width_map = {
                        '': (f'{freq_band}-onlyn', '20/40mhz-XX'),
                        '20': (f'{freq_band}-onlyn', '20/40mhz-XX'),
                        '40': (f'{freq_band}-onlyn', '20/40mhz-XX'),
                        '80': (f'{freq_band}-n/ac', '20/40/80mhz-XXXX'),
                        '160': (f'{freq_band}-ac', '20/40/80/160mhz-XXXXXXX')
                    }

                    band, channel_width = width_map.get(channel_width_val, (None, None))
                    interfaces.append((interface_name, band, channel_width))

        results = []

        for interface in interfaces:
            cmd = (f'/interface wireless set {interface[0]} disabled=no ssid="{ssid}" mode={radio_mode} security-profile=auto_wlan band={interface[1]} channel-width={interface[2]} frequency=auto wireless-protocol=802.11 wps-mode=disabled frequency-mode=superchannel country="{country}" installation=any')
            output = self.send_command(cmd)
            result = self.check_result(output)
            if result == True:
                results.append(f"{interface[0]} configured successfully!")
            else:
                results.append(f"ERROR with {interface[0]}: {output}")

        results_string = '\n'.join(map(str, results))
        return results_string
    
    def reset_wireless_config(self):
        
        return (self.check_result(self.send_command("/int wireless reset-configuration [find]")) and self.check_result(self.send_command("/interface wireless security-profiles reset default")))


    
    def download_backup(self, local_path, filename=None):
        
        if filename == None:
            if self.make_backup():
                return self.download_file(self.last_backup['name'], local_path)
        else:
            return self.download_file(filename, local_path)
        

    def download_export(self, local_path):
        
        print("*** INFO ***: This process may take some time to get info depending on how many config are in your device. Please wait...")

        self.last_export['name'] = "export_" + self.get_identity() + "_" + self.current_datetime + ".rsc"
        self.send_command(f"/export terse file={self.last_export['name']}")
        self.download_file(self.last_export['name'], local_path)
        self.send_command(f"/file remove {self.last_export['name']}")
        
        return "Operation successful. The file has been saved."
    
    def download_file(self, filename, local_path):

        try:
            sftp = self.client.open_sftp()

            remote_path = "/" + filename
            local_full_path = os.path.join(local_path, filename)

            # Check if the remote file exists before downloading
            sftp.stat(remote_path)
            
            sftp.get(remotepath=remote_path, localpath=local_full_path)

            return local_full_path

        except IOError as e:
            if e.errno == 13:
                print(f"ERROR: Permission denied in local folder {local_full_path}")
            elif e.errno == 2:
                print(f"ERROR: File '{remote_path}' not found. Please make sure the file exists on the remote device.")
            else:
                print(f"ERROR: {str(e)}")
            return False


    def enable_cloud_dns(self):
        
        self.send_command("/ip cloud set ddns-enabled=yes")
        time.sleep(2)
        return self.send_command(":put [/ip cloud get dns-name]")
    

    def make_backup(self, name="backup", password=None, encryption="aes-sha256", dont_encrypt="yes"):
        
        self.last_backup['name'] = name + "_" + self.get_identity() + "_" + self.current_datetime + ".backup"

        base_cmd = f"/system backup save name={self.last_backup['name']} encryption={encryption} dont-encrypt={dont_encrypt}"

        if password is not None:
            base_cmd += f" password={password}"
        
        self.output = self.send_command(base_cmd)

        if "backup saved" in self.output:
            return True
        else:
            return False
    

    def update_system(self, channel="stable"):
        
        print("Checking RouterOS updates...")
        self.send_command(f"/system package update set channel={channel}")
        self.send_command(f"/system routerboard settings set auto-upgrade=yes")        

        self.send_command("/system package update check-for-updates once")
        time.sleep(3)

        current_package_version = self.send_command("/system package update print")

        current_version_str = ""
        latest_version_str = ""

        for line in current_package_version.splitlines():
            if line != "":
                parsed_line = line.strip().replace(" ", "")

                if parsed_line.split(":")[0] == "installed-version":
                    current_version_str = parsed_line.split(":")[1]

                if parsed_line.split(":")[0] == "latest-version":
                    latest_version_str = parsed_line.split(":")[1]
                
                if parsed_line.split(":")[0] == "status":
                    update_status = parsed_line.split(":")[1]

        if update_status == "No version available in this channel".strip().replace(" ", ""):
            return "No version available in this channel"
        
        try:
            current_version = Version(current_version_str)
            latest_version = Version(latest_version_str)

        except InvalidVersion:  
            return "Invalid version retrieved from RouterOS."
        
        if latest_version > current_version:            
            self.send_command("/system package update install")
            return "Update available!. Updating RouterOS device..."
        else:
            return "Device is up to date!"





    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Auxiliary methods
    
    def parse_interfaces(self, raw_interfaces):
        self.interfaces = []
        status_mapping = {
            "R": "running",
            "X": "disabled",
            "D": "dynamic",
            "S": "slave",
            "RS": "running-slave",
            "XS": "disabled-slave",
            "DRS": "dynamic-running-slave"
        }

        for line in raw_interfaces.splitlines():
            interface = {}
            parsed = re.sub(" +", " ", line).strip()

            if re.search(r"^\d+", parsed):
                status = parsed.split(" ")[1]
                interface["status"] = status_mapping.get(status, "not_connected")
                interface["name"] = self.search_attribute(parsed, 'name="(.*?)"')
                interface["default-name"] = self.search_attribute(parsed, 'default-name="(.*?)"')
                interface["type"] = self.search_attribute(parsed, 'type="(.*?)"')
                interface["mtu"] = self.search_attribute(parsed, 'actual-mtu=(.*?) [a-z]')
                interface["mac_address"] = self.search_attribute(parsed, 'mac-address=(.*?) [a-z]')

                self.interfaces.append(interface)

        return self.interfaces

    def search_attribute(self, pattern, string):
        match = re.search(pattern, string)
        return match.group(1) if match else ""
    
    def check_result(self, command_output):
            if command_output != "":
                return False
            else:
                return True

        

    
    




