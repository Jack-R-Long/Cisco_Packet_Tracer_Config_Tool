hostName = ""
secretPass = ""
bannerMOTD = ""
ipDomain = ""
consolePass = ""
mgmtVLAN = 1
mgmtVLANMask= ""
vlanDesc = ""
sshUserName= ""
sshSecret = ""
sshKeyBitModulus = 1024
vtpDomain = ""
vtpPassword = ""


distSwitchScript = [
    "enable",
    "configure t",
    "hostname " + hostName,
    "enable secret " + secretPass,
    "banner motd " + bannerMOTD,
    "ip domain-name " + ipDomain,
    "no ip domain-lookup",
    "service timestamps log datetime msec",
    "service timestamps debug datetime msec",

    "line console 0",
    "password " + consolePass,
    "login",
    "exec-timeout 5",
    "logging synchronous",

    "interface vlan1",
    "ip address " + mgmtVLAN + " " + mgmtVLANMask,
    "description VLANDESC",
    "no shutdown",

    "configure t",
    "username SSH_NAME secret SSH_SECRET",

    "line vty 0 15",
    "login local",
    "exec-timeout 5",
    "logging synchronous",
    "transport input ssh",
    "exit",

    "crypto key generate rsa",
    "y",
    "BIT_MOD",


    "configure t",
    "interface TEMP",
    "switchport trunk encapsulation dot1q",
    "switchport mode trunk",
    "description TRUNK1DESC",

    "interface FastEthernet0/10",
    "switchport trunk encapsulation dot1q",
    "switchport mode trunk",
    "description AS01",

    "interface FastEthernet0/9",
    "switchport trunk encapsulation dot1q",
    "switchport mode trunk",
    "description AS02",

    "interface range FastEthernet0/2-8",
    "switchport mode access",
    "switchport access vlan 111",
    "shutdown",

    "interface GigabitEthernet0/1",
    "switchport mode access",
    "switchport access vlan 111",
    "shutdown",
    "exit",

    "configure t",
    "vtp domain cyberforce.us.mil",
    "vtp password Dominate!",
    "vtp mode client",

    "configure t",
    "spanning-tree vlan 101 priority 12288",
    "spanning-tree vlan 6 priority 12288",

    "spanning-tree vlan 1 priority 16384",
    "spanning-tree vlan 33 priority 16384",

    "configure t",
    "int vlan 101",
    "description Space Force1",
    "ip address 112.11.22.132 255.255.255.128",

    "configure t",
    "ip access-list standard 37",
    "permit 201.98.56.17 0.0.0.0",
    "permit 129.44.57.16 0.0.0.255",
    "exit",

    "line vty 0 15",
    "access-class 37 in",
    "exit",
    "w"
]