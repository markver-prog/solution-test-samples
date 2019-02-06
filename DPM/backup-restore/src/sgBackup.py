'''
This script intends to generally back up Storage Groups configurations on a CPC and save them
into a config file for later restoration.

@author: Daniel Wu <yongwubj@cn.ibm.com> 03/21/2018
'''

from CommonAPI.prsm2api import *
from CommonAPI.wsaconst import *
from CommonAPI.hmcUtils import *
from CommonAPI.readConfig import *
import argparse, ConfigParser

# General params 
hmcHost = None
cpcName = None
userId = None
password = None

# Dirs to save backup file
backupDir = None


# ------------------------------------------------------------------ #
# --------- Start of parseArgs function ---------------------------- #
# ------------------------------------------------------------------ #
def parseArgs():
    '''
    - parse arguments input for this script
    '''
    global hmcHost, cpcName, userId, password, backupDir
    parser = argparse.ArgumentParser(description="Back up basic configs for all storage groups on specified CPC")
    parser.add_argument('-hmc', '--hmc', metavar='<HMC host IP>', help='HMC host IP', required=True)
    parser.add_argument('-cpc', '--cpcName', metavar='<cpc name>', help='cpc name', required=True)
    parser.add_argument('-uid', '--userId', metavar='<user id>', help='user id', required=True)
    parser.add_argument('-psw', '--password', metavar='<password>', help='password', required=True)
    parser.add_argument('-bakDir', '--backupDir', metavar='<backup directory>',
                        help='Directory to save backup file')

    args = vars(parser.parse_args())
    #hmc host
    _hmcHost = assertValue(pyObj=args, key='hmc', listIndex=0, optionalKey=True)
    hmcHost = checkValue('hmcHost', _hmcHost , hmcHost)
    #cpc name
    _cpcName = assertValue(pyObj=args, key='cpcName', listIndex=0, optionalKey=True)
    cpcName = checkValue('cpcName', _cpcName, cpcName)
    #user id
    _userId = assertValue(pyObj=args, key='userId', listIndex=0, optionalKey=True)
    userId = checkValue('userId', _userId, userId)
    #user password
    _password = assertValue(pyObj=args, key='password', listIndex=0, optionalKey=True)
    password = checkValue('password', _password, password)
    #Backup directory
    _backupDir = assertValue(pyObj=args, key='backupDir', listIndex=0, optionalKey=True)
    backupDir = checkValue('backupDir', _backupDir, backupDir)

# ------------------------------------------------------------------ #
# --------- End of parseArgs function ------------------------------ #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of printParams function -------------------------- #
# ------------------------------------------------------------------ #
def printParams():
    global backupDir
    print("\tParameters were input:")
    print("\tHMC system IP\t%s"%hmcHost)
    print("\tCPC name\t%s"%cpcName)
    if backupDir:
        print("\tBackup Directory --> %s"%backupDir)
    else:
        currentPath = os.getcwd()
        backupDir = currentPath
        print("\tBackup Directory --> %s"%currentPath)

# ------------------------------------------------------------------ #
# --------- End of printParams function ---------------------------- #
# ------------------------------------------------------------------ #


# Start main from here
hmc = None
# configuration for all Storage Groups on specified CPC
bakSGsConfig = dict()

try:
    parseArgs()
    
    print "*****************************************************"
    print "Back up all Storage Groups on specified CPC"
    printParams()
    print "*****************************************************"
    # initiate hmc connection 
    hmc = createHMCConnection(hmcHost=hmcHost, userID=userId, userPassword=password)
    cpc = selectCPC(hmc, cpcName)
    cpcURI = assertValue(pyObj=cpc, key=KEY_CPC_URI)
    cpcName = assertValue(pyObj=cpc, key=KEY_CPC_NAME)
    
    sgURIListByCPC = []
    sgNameListByCPC = []
    sgList = getStorageGroupList(hmc)
    for sg in sgList:
        if sg['cpc-uri'] == cpcURI:
            sgURIListByCPC.append(sg['object-uri'])
            sgNameListByCPC.append(sg['name'])
    
    for sgName in sgNameListByCPC:
        # Dict to store configuration data for single storage group
        bakSGCfg = {'sgDesc':None, #storage group description
                    'storType':None, #storage type eg: fcp or ficon
                    'sgShared':None, # Boolean, True for shared and False for dedicated
                    'numOfPaths':None, # number of connectivity paths aka "active adapter count". 
                    'maxNumOfPars':None, # maximum number of shared partitions.
                    'sgStorVolsCfg':None, # an array to store storage volumes config in current SG.
                    }
        
        sgURI = sgURIListByCPC[sgNameListByCPC.index(sgName)]
        sgProps = getStorageGroupProperties(hmc, sgURI=sgURI)
        sgStorType = assertValue(pyObj=sgProps, key='type')

        bakSGCfg['sgDesc'] = assertValue(pyObj=sgProps, key='description')
        bakSGCfg['storType'] = assertValue(pyObj=sgProps, key='type')
        bakSGCfg['sgShared'] = assertValue(pyObj=sgProps, key='shared')
        bakSGCfg['numOfPaths'] = assertValue(pyObj=sgProps, key='connectivity')
        
        if sgStorType == 'fcp':
            bakSGCfg['maxNumOfPars'] = assertValue(pyObj=sgProps, key='max-partitions')
        
        sgStorVolsCfg = []
        sgStorVolURIDict = getStorVolListOfSG(hmc, sgURI)
        sgStorVolURIList = sgStorVolURIDict['storage-volumes']
        

        
        for sgStorVolDict in sgStorVolURIList:
            bakStorVolCfg = {
                        #'storVolName':None, #storage volume name
                         'storVolDesc':None, #storage volume description
                         'storVolSize':None, #storage volume size
                         'storVolUse':None,  #two choices, data or bootNone
                         'storVolModel':None, # for FICON only
                         'storVolDevNum':None, # for FICON only
                         'storVolECKDtype':None # for FICON only
                         }
            sgStorVolURI = sgStorVolDict['element-uri']
            sgStorVolProp = getStorVolProperties(hmc, sgStorVolURI)
            #bakStorVolCfg['storVolName'] = assertValue(pyObj=sgStorVolProp, key='name')
            bakStorVolCfg['storVolDesc'] = assertValue(pyObj=sgStorVolProp, key='description')
            bakStorVolCfg['storVolUse'] = assertValue(pyObj=sgStorVolProp, key='usage')
            bakStorVolCfg['storVolSize'] = assertValue(pyObj=sgStorVolProp, key='size')

            if sgStorType == 'fc':
                if assertValue(pyObj=sgStorVolProp, key='eckd-type') != 'base':
                    continue
                bakStorVolCfg['storVolModel'] = assertValue(pyObj=sgStorVolProp, key='model')
                if bakStorVolCfg['storVolModel'] != 'EAV':
                    bakStorVolCfg.pop('storVolSize')
                bakStorVolCfg['storVolDevNum'] = assertValue(pyObj=sgStorVolProp, key='device-number')
                

            for k, v in bakStorVolCfg.items():
                if v == None: bakStorVolCfg.pop(k)
            sgStorVolsCfg.append(bakStorVolCfg)
        bakSGCfg['sgStorVolsCfg'] = sgStorVolsCfg

        print "[%s] -> %s storage group backup is Done." % (sgName, sgStorType)
        bakSGsConfig[sgName] = bakSGCfg
                 
    # Generate backup config file 
    sgConfig = ConfigParser.ConfigParser(allow_no_value=True)
    for key1 in sorted(bakSGsConfig.keys()):
        sgConfig.add_section(key1)
        for key2 in sorted(bakSGsConfig[key1].keys()):
            if bakSGsConfig[key1][key2] != None:
                if "sgDesc" in key2:
                    sgConfig.set(key1, '#Storage Group Description')
                    sgConfig.set(key1, key2 ,bakSGsConfig[key1][key2])
                elif "storType" in key2:
                    sgConfig.set(key1, '#Storage Group Type')
                    sgConfig.set(key1, key2 ,bakSGsConfig[key1][key2])
                elif "sgShared" in key2:
                    sgConfig.set(key1, '#Storage Group shared or not')
                    sgConfig.set(key1, key2 ,bakSGsConfig[key1][key2])
                elif "numOfPaths" in key2:
                    sgConfig.set(key1, '#Number of paths or adapters')
                    sgConfig.set(key1, key2 ,bakSGsConfig[key1][key2])
                elif "maxNumOfPars" in key2:
                    sgConfig.set(key1, '#Maximum number of partitions')
                    sgConfig.set(key1, key2 ,bakSGsConfig[key1][key2])
                elif "sgStorVolsCfg" in key2:
                    sgConfig.set(key1, '#Storage volume configs')
                    sgConfig.set(key1, key2 ,bakSGsConfig[key1][key2])

    if os.path.exists(backupDir) is False:
        os.makedirs(backupDir)
    
    # Write backup configs into a file
    filePath = backupDir + '/' + cpcName + '-StorGroups-' + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + '.cfg'

    with open(filePath, 'wb') as configfile:
        sgConfig.write(configfile)
    
    if sgConfig :
        print "\nAbove %s Storage-Groups on %s were saved into below file successfully."%(len(sgNameListByCPC),cpcName)
        print "%s"%filePath
    else:
        print "\nStorage Group backup failed, please check the environment manually."
    
except Exception as exc:
    if exc.message != None:
        print exc.message
  
finally:
    # cleanup
    if hmc != None:
        hmc.logoff()    
    
    
    


    
    