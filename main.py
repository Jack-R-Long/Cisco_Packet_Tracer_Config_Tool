import csv
import sys


class Device:
    def __init__ (self, hostname, columnIndex):
        self.hostname = hostname
        self.column = columnIndex
        self.router = False
        self.dist_switch = False
        self.access_switch = False
        self.vlans = {}
        self.globalConfigs = {}
        self.ports = {}
        self.configScript = []
    
    def assignVlans(self, vlanList):
        '''
        Assign vlan data to object
        '''
        for vlan in vlanList:
            vlanDict = {}
            vlanDict['id'] = vlan[0]
            vlanDict['name'] = vlan[1]
            vlanDict['subnet'] = vlan[2]
            vlanDict['mask'] = vlan[3][5:-1]
            vlanDict['ip'] = vlan[self.column]
            self.vlans[vlan[0]] = vlanDict
    
    def assignPorts(self, portconfigs):
        '''
        Assign port configs 
        '''
        for portDict in portconfigs:
            if portDict['hostname'] == self.hostname:
                self.ports = portDict
    
    def printTxt(self):
        '''
        Print out the config script
        '''
        f = open(self.hostname + ".txt", "w")
        # Write to file, each list index a new line
        f.writelines("%s\n" % line for line in self.configScript)
        f.close()


def main():
    '''
    Main function
    '''
    # Verify user supplied csv
    if (len(sys.argv) != 3):
        print("Invalid input\nUsage `python main.py network_data.csv device_data.csv`")
        return

    # Read csv data
    devices, vlans, globalConfigs= readNetworkCSV(sys.argv[1])
    portConfigs = readDeviceCSV(sys.argv[2])

    # Create devices
    deviceList = createDevices(devices)
    
    # Assign config data to each device
    for device in deviceList:
        device.assignVlans(vlans)
        device.assignPorts(portConfigs)
        device.globalConfigs = globalConfigs

    # Create script
    writeInitialConfigs(deviceList)
    for device in deviceList:
        device.printTxt()


def readNetworkCSV(networkData):
    '''
    Parse data from network csv
    '''
    with open(networkData, newline='') as csvfile:
        reader = csv.reader(csvfile)
        line_count = 0
        vlans = []
        globalConfigs = {}
        for row in reader:
            # First row
            if line_count == 0:
                devices = row[4:]
            # VLANs
            elif line_count < 14 and row[1] != '':
                vlans.append(row)
            # Global data 
            elif row[0] != '':
                globalConfigs[row[0]] = row[1]
            line_count += 1
        return devices, vlans, globalConfigs


def readDeviceCSV(deviceFile):
    '''
    Parse data from device csv
    '''
    with open(deviceFile, newline='') as csvfile:
        reader = csv.reader(csvfile)
        devices = []
        outputData = []
        line_count = 0
        for row in reader:
            # Devices
            if line_count == 0:
                devices = row[1:]
                # devices = [i for i in devices if i]
                for x in range(len(devices)):
                    if devices[x]:
                        outputData.append({
                            'hostname' : devices[x],
                            'index' : x + 1
                        })
            # Port data
            elif line_count > 1:
                for dictX in outputData:
                    # Interface description and trunk
                    dictX[row[0]] = [row[dictX['index']], row[dictX['index'] + 1]]
            # Increment
            line_count += 1
        return outputData


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


def createDevices(deviceList):
    '''
    create network device object
    '''
    listOut = []
    columnIndex = 4
    for device in deviceList:
        # Instantiate device object
        deviceObject = Device(hostname=device, columnIndex = columnIndex)
        deviceType = userInputInt(f"What type of device is {device}?\n1. Core router\n2. Dist switch\n3. Access switch\n Enter 1, 2, or 3: ", min=1, max=3)
        if deviceType == 1:
            deviceObject.router = True
        elif deviceType == 2:
            deviceObject.dist_switch = True
        else:
            deviceObject.access_switch = True
        listOut.append(deviceObject)
        columnIndex += 1
    return listOut


def writeInitialConfigs(deviceList):
    '''
    Write initial config script for each device
    '''
    # Get user input for managment VLAN ID
    mgmtVlanID = str(userInputInt("VLAN ID for the Management VLAN: ", 1, 1000))
    for device in deviceList:
        lastMGMTOctet = device.vlans[mgmtVlanID]['id']
        mgmtIP = device.vlans[mgmtVlanID]['subnet'][:-(len(lastMGMTOctet)-1)] + lastMGMTOctet[2:]
        print(mgmtIP)
        initialConfigScript = [
        "! 1 CONFIGS **************",
        "enable",
        "configure t",
        "hostname " + device.hostname,
        "enable secret " + device.globalConfigs['Enable Secret'],
        "banner motd " + device.globalConfigs['Banner'],
        "ip domain-name " + device.globalConfigs['IP Domain'],
        "no ip domain-lookup",
        "service timestamps log datetime msec",
        "service timestamps debug datetime msec",
        "line console 0",
        "password " + device.globalConfigs['Console Password'],
        "login",
        "exec-timeout 5",
        "logging synchronous",
        ]
        if device.router == True:
            initialConfigScript += [
                'interface GigabitEthernet0/0.' + mgmtVlanID,
                'description Management',
                'encapsulation dot1q ' + mgmtVlanID,
                'ip address ' + mgmtIP + ' ' + device.vlans[mgmtVlanID]['mask'],
            ]
        else :
            initialConfigScript += [
            "interface vlan" + device.vlans[mgmtVlanID]['id'],
            "ip address " + mgmtIP + " " + device.vlans[mgmtVlanID]['mask'],
            "description Management",
            "no shutdown",
            ]
        initialConfigScript += [
        "! 2 SSH CONFIGS **************",
        "configure t",
        "username " + device.globalConfigs['Username'] + " secret " + device.globalConfigs['Secret'],
        "line vty 0 15",
        "login local",
        "exec-timeout 5",
        "logging synchronous",
        "transport input ssh",
        "exit",
        "crypto key generate rsa",
        "y",
        device.globalConfigs['Bit Modulus'],
        ]
        device.configScript = initialConfigScript
    return deviceList


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