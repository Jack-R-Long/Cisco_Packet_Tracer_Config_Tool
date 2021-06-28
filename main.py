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
        self.vtp_mode = 'client'
        self.stp_root = []
        self.stp_secondary = []
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
        filename = self.hostname.replace("/", "")
        f = open(filename + ".txt", "w+")
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
    devices, vlans, globalConfigs, vtpData, stpData = readNetworkCSV(sys.argv[1])
    portConfigs = readDeviceCSV(sys.argv[2])

    # Create devices
    deviceList = createDevices(devices, vtpData, stpData)
    
    # Assign config data to each device
    for device in deviceList:
        device.assignVlans(vlans)
        device.assignPorts(portConfigs)
        device.globalConfigs = globalConfigs

    # Create script
    writeInitialConfigs(deviceList)
    writePortConfigs(deviceList)
    writeVLANs(deviceList)
    writeSTP(deviceList)
    writePortSecurity(deviceList)
    writeRoutingDistSwitches(deviceList)
    for device in deviceList:
        device.printTxt()
        # print('done')


def readNetworkCSV(networkData):
    '''
    Parse data from network csv
    '''
    with open(networkData, newline='') as csvfile:
        reader = csv.reader(csvfile)
        line_count = 0
        vlans = []
        globalConfigs = {}
        vtpData = []
        stpData = []
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
            # Routing data
            elif row[3] == 'VTP Mode':
                vtpData = [i for i in row[4:] if i]
            # STP data
            elif row[3] == 'Spanning Tree Root Primary':
                stpData = [i for i in row[4:] if i]
                for x in range(len(stpData)):
                    stpData[x] = stpData[x].replace(',', '').split()
                    
            line_count += 1
                    
        return devices, vlans, globalConfigs, vtpData, stpData


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


def createDevices(deviceList, vtpData, stpData):
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
    # Add VTP data (only switches (i.e. first 4))
    for x in range(len(vtpData)):
        listOut[x].vtp_mode = vtpData[x]
    # Add STP to dist switches
    indexNeeded = 1
    for device in listOut:
        if device.dist_switch == True:
            device.stp_root = stpData[indexNeeded -1 ]
            device.stp_secondary = stpData[indexNeeded]
            indexNeeded = 0
            
    return listOut


def writeInitialConfigs(deviceList):
    '''
    Write initial config script for each device
    '''
    # Get user input for managment VLAN ID
    mgmtVlanID = str(userInputInt("VLAN ID for the Management VLAN: ", 1, 1000))
    routerPort = str(userInputInt("Port connects the routers to the switches: G0/", 1, 4))
    for device in deviceList:
        lastMGMTOctet = device.vlans[mgmtVlanID]['ip']
        mgmtIP = device.vlans[mgmtVlanID]['subnet'][:-(len(lastMGMTOctet))] + lastMGMTOctet
        initialConfigScript = [
        "! 1 CONFIGS **************",
        "enable",
        "configure t",
        "hostname " + device.hostname,
        "enable secret " + device.globalConfigs['Enable Secret'],
        "banner motd " + device.globalConfigs['MOTD'],
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
                "interface GigabitEthernet0/" + routerPort + "." + mgmtVlanID,
                "description " + device.vlans[mgmtVlanID]['name'],
                "encapsulation dot1q " + mgmtVlanID,
                "ip address " + mgmtIP + ' ' + device.vlans[mgmtVlanID]['mask'],
            ]
        else :
            initialConfigScript += [
            "interface vlan" + device.vlans[mgmtVlanID]['id'],
            "ip address " + mgmtIP + " " + device.vlans[mgmtVlanID]['mask'],
            "description " + device.vlans[mgmtVlanID]['name'],
            "no shutdown",
            ]
        initialConfigScript += [
        "exit",
        "exit",
        "w",
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
        "exit",
        "w",
        ]
        device.configScript = initialConfigScript
    return deviceList


def writePortConfigs(deviceList):
    '''
    Create port config script for each device
    '''
    shutdownVLANID = str(userInputInt("VLAN ID for the Shutdown VLAN: ", 1, 1000))
    for device in deviceList:
        if device.dist_switch == True or device.access_switch == True:
            # Trunk congfigs for switches
            closedPortsScript = []
            device.configScript += ['! 3 TRUNKS AND CLOSE PORTS **************', 'config t']
            for key in device.ports:
                if (key != 'hostname' and key != 'index'):
                    # Trunks
                    if (device.ports[key][1]):
                        device.configScript += [
                            '',
                            'interface ' + key,
                            'switchport trunk encapsulation dot1q',
                            'switchport mode trunk',
                            'description ' + device.ports[key][0],
                        ]
                    # Close unused ports
                    elif (device.ports[key][0] == ''):
                            closedPortsScript += [
                            '',
                            'interface ' + key,
                            'switchport mode access',
                            'switchport access vlan ' + device.vlans[shutdownVLANID]['id'],
                            'shutdown',
                        ]
            # Add usused port commands after trunks
            device.configScript += closedPortsScript

            # vtp config
            device.configScript += ['exit', '', '! 4 VTP SETUP **********',
            'vtp domain ' + device.globalConfigs['VTP Domain'],
            'vtp password ' + device.globalConfigs['VTP Password'],
            'vtp mode ' + device.vtp_mode,
            'vtp version 2', '']


def writeVLANs(deviceList):
    '''
    Write VLAN configs on VTP server and configure accees switch vlans
    '''
    for device in deviceList:
        # Config VLAN table on VTP server
        if device.vtp_mode == 'Server':
            device.configScript += ['! 5 VLAN SETUP **********']
            for key in device.vlans:
                # Skip VLANs that don't have id
                if 'x' not in key:
                    device.configScript += [
                        '',
                        'vlan ' + key,
                        'name ' + device.vlans[key]['name'],
                        'exit',
                    ]
        # Config access ports on access swtiche
        elif device.access_switch == True:
            device.configScript += ['! 5 VLAN SETUP **********']
            for key in device.ports:
                # Get fa ports that have description
                if 'fa' in key and device.ports[key][0]:
                    device.configScript += [
                        '',
                        'int ' + key,
                        'switchport access vlan ' + device.ports[key][0],
                        'switchport mode access',
                    ]


def writeSTP(deviceList):
    '''
    Write Spanning Tree Protocol configs
    '''
    rootPriority = userInputInt('STP root priority value (ex. 4096): ', 1, 10000)
    secPriority = userInputInt('STP secondary priority value (ex. 8192): ', 1, 10000)

    for device in deviceList:
         if device.dist_switch == True:
            device.configScript += ['', '! 6 STP SETUP **********']
            for vlanID in device.stp_root:
                device.configScript += [
                    'spanning-tree vlan ' + vlanID + ' priority ' + str(rootPriority)
                ]
            for vlanID in device.stp_secondary:
                device.configScript += ['',
                    'spanning-tree vlan ' + vlanID + ' priority ' + str(secPriority)
                ]


def writePortSecurity(deviceList):
    '''
    Write port security for access layer switches
    '''
    for device in deviceList:
     if device.access_switch == True:
        #  Hard code this because I am lazy
        device.configScript += ['', '! 7 PORT SECURITY **********',
            'interface range FastEthernet0/1-24',
            'switchport mode access',
            'switchport port-security',

            'switchport port-security violation shutdown',
            'switchport port-security maximum 2',
            'switchport port-security mac-address sticky',
        ]


def writeRoutingDistSwitches(deviceList):
    '''
    Create a layer 3 presence for each dist switch using SVIs
    '''
    for device in deviceList:
        if device.dist_switch == True:
            device.configScript += ['', '! 8 SVI SWITCH ROUTING **********']
            for key in device.vlans:
                # Skip VLANs that don't have id and shutdown
                if 'x' not in key and device.vlans[key]['name'] != 'Shutdown':
                    lastOctet = device.vlans[key]['ip']
                    device.vlans[key]['ip_address'] = device.vlans[key]['subnet'][1:-(len(lastOctet))] + lastOctet[1::]
                    device.configScript += ['',
                        'int vlan ' + key,
                        'description ' + device.vlans[key]['name'],
                        'ip address ' + device.vlans[key]['ip_address'] + ' ' + device.vlans[key]['subnet'],
                    ]


if __name__ == '__main__':
    main()