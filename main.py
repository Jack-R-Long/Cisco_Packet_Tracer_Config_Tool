

class Core_Router:
    def __init__ (self, hostname):
        self.hostname = hostname
        self.configs = {}
        self.globalConfigs = {}
        self.vlans = {}

    pass

class Dist_Switch:
    def __init__ (self, hostname):
        self.hostname = hostname
        self.configs = {}
        self.globalConfigs = {}
        self.vlans = {}
    pass

class Access_Switch:
    def __init__ (self, hostname):
        self.hostname = hostname
        self.configs = {}
        self.globalConfigs = {}
    pass

def main():
    '''
    Main function
    '''

    # Get initial network design
    numRouters = userInputInt("Number of core routers (2911s):")
    routerList = createDevice(Core_Router, numRouters)
    numSwitchesDist = userInputInt("Number of distribution switches (3560s): ")
    switchDistList = createDevice(Dist_Switch, numSwitchesDist)
    numSwitchesAccess = userInputInt("Number of access switches (2960s): ")
    switchAcessList = createDevice(Access_Switch, numSwitchesAccess)

    # Get global configs
    globalConfigs = getGlobalConfigs()

    # Get VLAN data
    vlanDict = getVLANs()
    
    # Config script for 
    switchDistList = configDistSwitch(switchDistList, globalConfigs, vlanDict)

    # Output config script
    outputTxt(switchDistList)


def userInputInt(prompt, min = 1, max = 10):
    '''
    Get int from user and validate
    '''
    num = min
    invalidInput = True
    while (invalidInput):
        num = input(prompt)
        try:
            num = int(num)
            if num < min or num > max:
                print("Invalid input")
            else:
                invalidInput = False
        except ValueError:
            print("Invalid input")
    return num


def createDevice(type, number):
    '''
    create network device object
    '''
    deviceList = []
    for x in range(number):
        hostName = input(f"Name for device {x}: ")
        deviceList.append(type(hostName))
    
    return deviceList


def getGlobalConfigs():
    '''
    Get global configs for all devices
    '''
    print("\n\nInput global configs for all devices\n")
    globalConfigs = {
        'secretPass' : '',
        'bannerMOTD' : '',
        'ipDomain' : '',
        'consolePass' : '',
        'mgmtVLAN#' : 1,
        'mgmtNetworkID' : '',
        'mgmtVLANMask': '',
        'shutdownVlan#' : 999,
        'sshUserName': '',
        'sshSecret' : '',
        'sshKeyBitModulus' : 1024,
        'vtpDomain' : '',
        'vtpPassword': '',
    }
    for key in globalConfigs:
        globalConfigs[key] = input(f"{key}: ")
    return globalConfigs

def getVLANs():
    '''
    Get VLAN data
    '''
    numVLANs = userInputInt("\n*********\nVLAN Config\nNumber of VLANs: ")
    vlanDict = {}
    for num in range(1, 1 + numVLANs):
        vlanName = input(f"Name of VLAN {num}: ")
        subnet = input(f"{vlanName} subnet (ex: 10.1.1.1): ")
        vlanDict[vlanName] = subnet
    return vlanDict


def configDistSwitch(distSwitchList, globalConfigs, vlanDict):
    '''
    get user input for dist switches
    '''
    switchConfigsDict = {
        'managment-IP' : "",
        'trunks' : [],
        'closed-fa-ports' : [],
        'closed-ga-ports' : [],
        'vtp-mode' : 'client'
        
    }
    for switch in distSwitchList:
        # Apply global configs
        switch.globalConfigs = globalConfigs

        # Get config values for dist switches
        print(f"\n Config values for Dist Switch {switch.hostname} \n")
        for key in switchConfigsDict:
            if key == 'closed-fa-ports' or key == 'closed-ga-ports':
                numClosedPorts = userInputInt(f"Number of {key}: ", 1, 24)
                for x in range(numClosedPorts):
                    closedPort = userInputInt(f"Closed {key[7:9]} port: ", 1, 24)
                    switchConfigsDict[key].append(closedPort)
            elif key == 'trunks':
                numTrunks = userInputInt(f"Number of trunk connections: ")
                for x in range(1, 1 + numTrunks):
                    trunkDict = {}
                    trunkDict['trunk-interface'] = input('trunk' + str(x) + '-interface: ')
                    trunkDict['trunk-description'] = input('trunk' + str(x) + '-description: ')
                    # append trunk dict to list of trunks
                    switchConfigsDict[key].append(trunkDict)
            else:
                switchConfigsDict[key] = input(f"{key}: ")
        switch.configs = switchConfigsDict
        
        # Get VLAN IP
        for key in vlanDict:
            switch.vlans[key] = input(f"Device {switch.hostname} IP address in {key} VLAN (subnet = {vlanDict[key]}): ")
    
    return distSwitchList

def outputTxt(distSwitchList):
    '''
    output config script to a txt file
    '''
    for switch in distSwitchList:
        # Create output txt file
        f = open(switch.hostname + ".txt", "w")
        # Config script
        distSwitchScript = [
        "! 1 CONFIGS **************",
        "enable",
        "configure t",
        "hostname " + switch.hostname,
        "enable secret " + switch.globalConfigs['secretPass'],
        "banner motd " + switch.globalConfigs['bannerMOTD'],
        "ip domain-name " + switch.globalConfigs['ipDomain'],
        "no ip domain-lookup",
        "service timestamps log datetime msec",
        "service timestamps debug datetime msec",
        "line console 0",
        "password " + switch.globalConfigs['consolePass'],
        "login",
        "exec-timeout 5",
        "logging synchronous",
        "interface vlan" + switch.globalConfigs['mgmtVLAN#'],
        "ip address " + switch.configs['managment-IP'] + " " + switch.globalConfigs['mgmtVLANMask'],
        "description VLANDESC",
        "no shutdown",
        "! 2 SSH CONFIGS **************",
        "configure t",
        "username " + switch.globalConfigs['sshUserName'] + " secret " + switch.globalConfigs['sshSecret'],
        "line vty 0 15",
        "login local",
        "exec-timeout 5",
        "logging synchronous",
        "transport input ssh",
        "exit",
        "crypto key generate rsa",
        "y",
        switch.globalConfigs['sshKeyBitModulus'],
        ]
        # Config trunks
        distSwitchScript = distSwitchScript + ["configure t"]
        for trunkDict in switch.configs['trunks']:
            trunk = [
                "interface " + trunkDict['trunk-interface'],
                "switchport trunk encapsulation dot1q",
                "switchport mode trunk",
                "description " + trunkDict['trunk-description'],
                ]
            distSwitchScript = distSwitchScript + trunk

        # Append shutdown port commands
        for x in range(len(switch.configs['closed-fa-ports'])):
            distSwitchScript.append("interface FastEthernet0/" + str(switch.configs['closed-fa-ports'][x]))
            distSwitchScript.append("switchport mode access")
            distSwitchScript.append("switchport access vlan" + str(switch.globalConfigs['shutdownVlan#']))
            distSwitchScript.append("shutdown")
        for x in range(len(switch.configs['closed-ga-ports'])):
            distSwitchScript.append("interface g0/" + str(switch.configs['closed-ga-ports'][x]))
            distSwitchScript.append("switchport mode access")
            distSwitchScript.append("switchport access vlan" + str(switch.globalConfigs['shutdownVlan#']))
            distSwitchScript.append("shutdown")

        distSwitchScript + [
        "exit",

        "configure t",
        "vtp domain " + switch.globalConfigs['vtpDomain'],
        "vtp password " + switch.globalConfigs['vtpPassword'],
        "vtp mode " + switch.configs['vtp-mode'],

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
        # Write to file, each list index a new line
        f.writelines("%s\n" % line for line in distSwitchScript)
        f.close()


if __name__ == '__main__':
    main()