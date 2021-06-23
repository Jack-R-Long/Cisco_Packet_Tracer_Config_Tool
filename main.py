

class Core_Router:
    def __init__ (self, hostname):
        self.hostname = hostname
        self.configs = {}
    pass

class Dist_Switch:
    def __init__ (self, hostname):
        self.hostname = hostname
        self.configs = {}
        self.lists = []
    pass

class Access_Switch:
    def __init__ (self, hostname):
        self.hostname = hostname
        self.configs = []
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
    
    # Config script for 
    switchDistList = configDistSwitch(switchDistList)

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
        'secretPass' : "",
        'bannerMOTD' : "",
        'ipDomain' : "",
        'consolePass' : "",
        'mgmtVLAN#' : 1,
        'mgmtVLANMask': '',
        'sshUserName': '',
        'sshSecret' : '',
        'sshKeyBitModulus' : 1024,
        'vtpDomain' : '',
        'vtpPassword': '',
    }
    for key in globalConfigs:
        globalConfigs[key] = input(f"{key}: ")
    return globalConfigs


def configDistSwitch(distSwitchList):
    '''
    get user input for dist switches
    '''
    switchConfigsDict = {
        'managment-IP' : "",
        'trunk1-interface' : "",
        'trunk1-description' : "",
        'trunk2-interface' : "",
        'trunk2-description' : "",
    }
    for switch in distSwitchList:
        print(f"\n Config values for Dist Switch {switch.hostname} \n")
        for key in switchConfigsDict:
            switchConfigsDict[key] = input(f"{key}: ")
        switch.configs = switchConfigsDict
    return distSwitchList

def outputTxt(distSwitchList):
    '''
    output config script to a txt file
    '''


if __name__ == '__main__':
    main()