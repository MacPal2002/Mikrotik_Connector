<h1 align="center">
<img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" width="100" />
<br>Mikrotik_Connector
</h1>

<p align="center">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style&logo=Python&logoColor=white" alt="Python" />
</p>



The `MikrotikDevice` class provides a set of methods to interact with MikroTik devices using SSH. It allows you to connect to the device, execute commands, retrieve configuration information, and perform various tasks related to network administration.

## Dependencies

- `paramiko`
- `packaging`

Make sure you have these dependencies installed before using the `Mikrotik_Connector`

## Example of usage

Here's an example of how to use the `MikrotikDevice` class to interact with a MikroTik device:

```python
from Mikrotik_Connector import MikrotikDevice


# Create an instance of MikrotikDevice
device = MikrotikDevice()

# Connect to the MikroTik device
device.connect(ip_address="192.168.88.1", username="admin", password="your_password", port="22")

# Retrieve the device's identity
identity = device.get_identity()
print("Device Identity:", identity)

# Get the license level of RouterOS
license_level = device.get_license_level()
print("License Level:", license_level)

# Retrieve information about a wireless LAN interface
wlan_info = device.get_wlan_info(interface="wlan1", value="frequency")
print("Wireless Info:", wlan_info)

# Retrieve IP addresses assigned to interfaces
ip_addresses = device.get_ip_addresses()
print("IP Addresses:", ip_addresses)

# Retrieve information about system resources
resources = device.get_resources()
print("System Resources:", resources)


# Disconnect from the device
device.disconnect()
```


<br><br><br><br>
# All methods:
<br><br>

## GET methods:

These methods are used to retrieve information from the Mikrotik device.

### `get_export_configuration(self, sensitive=false)`
Retrieve the device's configuration.

- `sensitive`: Show sesitive TRUE|FALSE (optional).


### `get_identity(self)`

Retrieve the device's identity (hostname).

### `get_license_level(self)`

Get the license level of Router OS.

### `get_wlan_info(self, interface, value)`

Retrieve information about the device's wireless LAN.

- `interface`: Name of the wireless LAN interface.
- `value`: The value to retrieve from the interface configuration.

### `get_wlan_sec(self, profile_name)`

Retrieve the security settings for the specified WLAN profile.

- `profile_name`: Name of the WLAN security profile.

### `get_interfaces(self)`

Retrieve details about the device's interfaces.

### `get_ip_addresses(self)`

Retrieve IP addresses assigned to interfaces.

### `get_resources(self)`

Retrieve information about system resources.

### `get_routes(self)`

Retrieve information about IP routes.

### `get_services(self)`

Retrieve information about active services.

### `get_users(self)`

Retrieve information about system users.

For detailed information on each method and their parameters, refer to the source code.

<br><br>

## UPDATE methods:
These methods are used to update various settings on the Mikrotik device.

### `update_address_pool(pool_name, addresses=None, next_pool=None, new_pool_name=None)`

Updates an IP address pool.

- `pool_name`: Name of the pool to update.
- `addresses`: New ranges of IP addresses for the pool.
- `next_pool`: Name of the next pool.
- `new_pool_name`: New name for the pool.

### `update_dhcp_client(interface, disabled, add_default_route, route_distance, use_peer_dns, use_peer_ntp)`

Updates DHCP client settings.

- `interface`: Interface name.
- `disabled`: Whether the DHCP client is disabled (True or False).
- `add_default_route`: Whether to add the default route.
- `route_distance`: Default route distance.
- `use_peer_dns`: Whether to use peer DNS.
- `use_peer_ntp`: Whether to use peer NTP.

### `update_dhcp_server_server(interface, disabled=None, name=None, lease_time=None, address_pool=None)`

Updates DHCP server settings for a specific interface.

- `interface`: Interface name.
- `disabled`: Whether the DHCP server is disabled (True or False).
- `name`: Server name.
- `lease_time`: Lease time for addresses.
- `address_pool`: Address pool name.

### `update_dhcp_server_network(address, gateway=None, netmask=None, dns_server=None, ntp_server=None)`

Updates DHCP server network settings for a specific address.

- `address`: Network address.
- `gateway`: Gateway address.
- `netmask`: Subnet mask.
- `dns_server`: DNS server address.
- `ntp_server`: NTP server address.

### `update_identity(name)`

Updates the device identity (hostname).

- `name`: New identity name.

### `update_ip_address(interface, address, disabled="no")`

Updates an IP address assigned to an interface.

- `interface`: Interface name.
- `address`: New IP address.
- `disabled`: Whether the IP address is disabled (yes or no).

### `update_services(service, disabled, port=None, address=None)`

Updates service settings.

- `service`: Service name.
- `disabled`: Whether the service is disabled (True or False).
- `port`: New port number for the service (optional).
- `address`: New IP address for the service (optional).

### `update_user(username, password, group)`

Updates user settings.

- `username`: Username of the user to update.
- `password`: New password for the user.
- `group`: New group for the user.

For detailed information on each method and their parameters, refer to the source code.

<br><br>

##  CREATE methods:

These methods are used to create and configure various settings on the Mikrotik device.

### `create_address_pool(name, range, next_pool="none")`

Creates an IP address pool.

- `name`: Name of the pool.
- `range`: IP address range for the pool.
- `next_pool`: Name of the next pool.

### `create_dhcp_client(interface, disabled="no", add_default_route="yes", route_distance=1, use_peer_dns="yes", use_peer_ntp="yes")`

Creates a DHCP client configuration.

- `interface`: Interface name.
- `disabled`: Whether the DHCP client is disabled (yes or no).
- `add_default_route`: Whether to add the default route (yes or no).
- `route_distance`: Route distance.
- `use_peer_dns`: Whether to use peer DNS (yes or no).
- `use_peer_ntp`: Whether to use peer NTP (yes or no).

### `create_dhcp_server(interface, network_address=None, disabled="no", name="dhcp_server", address_pool="static-only", lease_time="00:10:00", dns_server="1.1.1.1,9.9.9.9")`

Creates a DHCP server configuration.

- `interface`: Interface name.
- `network_address`: Network address for the server.
- `disabled`: Whether the DHCP server is disabled (yes or no).
- `name`: Server name.
- `address_pool`: Address pool name.
- `lease_time`: Lease time for addresses.
- `dns_server`: DNS server addresses.

### `create_ip_address(ip_address, interface)`

Creates an IP address on a specific interface.

- `ip_address`: IP address to be created.
- `interface`: Interface name.

### `create_route(dst_address, gateway, distance, disabled="no")`

Creates a static IP route.

- `dst_address`: Destination address.
- `gateway`: Gateway address.
- `distance`: Route distance.
- `disabled`: Whether the route is disabled (yes or no).

### `create_user(username, password, group)`

Creates a user.

- `username`: Username for the new user.
- `password`: Password for the new user.
- `group`: Group for the new user.

### `configure_wlan_security(profile_name, password)`

Configures security settings for a WLAN profile.

- `profile_name`: Name of the WLAN profile.
- `password`: Password for the security profile.

### `configure_wlan(ssid, password, country="south africa")`

Configures a wireless LAN (WLAN) interface.

- `ssid`: SSID for the WLAN.
- `password`: Password for the WLAN.
- `country`: Country code for WLAN configuration.

### `reset_wireless_config()`

Resets wireless configuration for all interfaces.

### `download_backup(local_path, filename=None)`

Downloads a backup file from the Mikrotik device.

- `local_path`: Local path to save the downloaded file.
- `filename`: Optional filename for the backup file.

### `download_export(local_path, sensitive=false)`

Downloads the configuration export file from the Mikrotik device.

- `local_path`: Local path to save the downloaded file.
- `sensitive`: Show sesitive TRUE|FALSE (optional).

### `download_file(filename, local_path)`

Downloads a file from the Mikrotik device to the local system.

- `filename`: Filename of the remote file.
- `local_path`: Local path to save the downloaded file.

### `enable_cloud_dns()`

Enables Cloud DNS and returns the DNS name.

### `make_backup(name="backup", password=None, encryption="aes-sha256", dont_encrypt="yes")`

Creates a backup of the Mikrotik device.

- `name`: Name of the backup.
- `password`: Password for the backup (optional).
- `encryption`: Encryption algorithm (default: aes-sha256).
- `dont_encrypt`: Whether to not encrypt the backup (yes or no).

### `update_system(channel="stable")`

Updates the RouterOS system to the latest version.

- `channel`: Update channel (default: stable).

<br><br><br>
<hr>

### *Mikrotik_Connector by MacPal2002* <br>
*This project is based on the original work by [d4vidcn](https://github.com/d4vidcn). Special thanks for their contributions and efforts.*






