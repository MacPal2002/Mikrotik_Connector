from setuptools import setup, find_packages

setup(
    name='Mikrotik_Connector',
    version='0.2',
    description='A python-based SSH API for MikroTik devices',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='MacPal2002',
    author_email='maciek.palenica@outlook.com',
    url='https://github.com/MacPal2002/Mikrotik_Connector',
    packages=find_packages(),
      install_requires=[
        'paramiko',
        'packaging'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
)
