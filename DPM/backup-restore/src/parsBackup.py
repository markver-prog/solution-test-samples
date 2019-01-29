'''
This script intends to back up general partition settings and configurations on a CPC and save them
into a config file for partition restore use.

@author: Daniel Wu <yongwubj@cn.ibm.com>
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
    parser = argparse.ArgumentParser(description="Back up basic configs for all partitions on specified CPC")
    parser.add_argument('-hmc', '--hmc', metavar='<HMC host IP>', help='HMC host IP', required=True)
    parser.add_argument('-cpc', '--cpcName', metavar='<cpc name>', help='cpc name', required=True)
    parser.add_argument('-uid', '--userId', metavar='<user id>', help='user id', required=True)
    parser.add_argument('-psw', '--password', metavar='<password>', help='password', required=True)
    parser.add_argument('-bakDir', '--backupDir', metavar='<backup directory>',
                        help='Directory to save backup file', required=False)

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


# start _main_ from here
hmc = None
allParNamesList = []
allParURIsList = []

allParsCfg = {} 
vHBAsCfg = {}

success = True

try:
    parseArgs()
    
    print "********************************************************"
    print "Back up basic configs for all partitions on specified CPC"
    printParams()
    print "********************************************************"

    # Access HMC system and create HMC connection 
    hmc = createHMCConnection(hmcHost=hmcHost, userID=userId, userPassword=password)
    cpc = selectCPC(hmc, cpcName)
    cpcURI = assertValue(pyObj=cpc, key=KEY_CPC_URI)
    cpcName = assertValue(pyObj=cpc, key=KEY_CPC_NAME)
    
    # HMC version check
    apiMajVer = hmc.apiMajorVer
    apiMinVer = hmc.apiMinorVer
    
    if apiMinVer >= 22:
        sgIsAvai = True
    else: 
        sgIsAvai = False
        
    cpcID = cpcURI.replace('/api/cpcs/','')
    
    sgURIListByCPC = []
    sgNameListByCPC = []
    sgList = getStorageGroupList(hmc)
    for sg in sgList:
        if sg['cpc-uri'] == cpcURI:
            sgURIListByCPC.append(sg['object-uri'])
            sgNameListByCPC.append(sg['name'])

    attachedSGs = {}
    for sgName in sgNameListByCPC:
        sgURI = sgURIListByCPC[sgNameListByCPC.index(sgName)]
        sgProps = getStorageGroupProperties(hmc, sgURI=sgURI)

        sgStorType = assertValue(pyObj=sgProps, key='type')
        
        if sgStorType == 'fcp':

            sgVSRsResp = getVSRsOfSG(hmc, sgURI)
            sgVSRsPropList = assertValue(pyObj=sgVSRsResp, key='virtual-storage-resources')

            attachedParDevList = []
            if sgVSRsPropList != None:

                for sgVSR in sgVSRsPropList:
                    parURI = assertValue(pyObj=sgVSR, key='partition-uri')
                    devNum = assertValue(pyObj=sgVSR, key='device-number')
                    parProp = getPartitionProperties(hmc, parURI=parURI)
                    parName = assertValue(pyObj=parProp, key='name')

                    attachedParDevList.append(parName+':'+devNum)
                attachedSGs[sgName] = attachedParDevList
        elif sgStorType == 'fc':
            # FICON couldn't get the attached partition information here, will handle in the later part.
            pass
  
    attachedSGDevList = []
    attachedParList = []
          
    for k,v in attachedSGs.items():
        for parDev in v:
            attachedParList.append(parDev.split(':')[0])
            attachedSGDevList.append(k+':'+parDev.split(':')[1])
    
    parResObj = getCPCPartitionsList(hmc, cpcID)

    # Generate all partitions list on this CPC
    for parInfo in parResObj:
        _parName = assertValue(pyObj=parInfo,key='name')
        _parURI = assertValue(pyObj=parInfo,key='object-uri')
        allParNamesList.append(_parName)
        allParURIsList.append(_parURI)
        
    # Retrieve Processor and Memeory settings for all partitions
    for parName in allParNamesList:

        parBasicCfg = dict()
        parIndex = allParNamesList.index(parName)
        parURI = allParURIsList[parIndex]
        # Get partition properties
        parProp = getPartitionProperties(hmc, parURI=parURI)

        parBasicCfg['par_desc'] = assertValue(pyObj=parProp, key='description').replace("\n", "")
        parBasicCfg['par_type'] = assertValue(pyObj=parProp, key='type')
        parBasicCfg['par_status'] = assertValue(pyObj=parProp, key='status')
        parBasicCfg['par_reserveResources'] = assertValue(pyObj=parProp, key='reserve-resources')

        # if ssc partition add following settings
        if assertValue(pyObj=parProp, key='type') == 'ssc':
            parBasicCfg['par_sscHostName'] = assertValue(pyObj=parProp, key='ssc-host-name')
            parBasicCfg['par_sscMasterUserid'] = assertValue(pyObj=parProp, key='ssc-master-userid')
            
            # Failed to get user pwd since it's protected and 'default' pwd returned for customization 
            parBasicCfg['par_sscMasterPW'] = ''
          
            if assertValue(pyObj=parProp, key='ssc-ipv4-gateway'):
                parBasicCfg['par_sscIPv4GW'] = assertValue(pyObj=parProp, key='ssc-ipv4-gateway')

            if assertValue(pyObj=parProp, key='ssc-dns-servers'):
                parBasicCfg['par_sscDNS'] = ','.join(assertValue(pyObj=parProp, key='ssc-dns-servers'))

        ifl_proc_num = assertValue(pyObj=parProp, key='ifl-processors')
        cp_proc_num = assertValue(pyObj=parProp, key='cp-processors')
        if ifl_proc_num > 0:
            proc_type = 'ifl'
            proc_num = ifl_proc_num
        elif cp_proc_num > 0:
            proc_type = 'cp'
            proc_num = cp_proc_num
        parBasicCfg['proc_type'] = proc_type
        parBasicCfg['proc_mode'] = assertValue(pyObj=parProp, key='processor-mode')
        parBasicCfg['proc_num'] = proc_num
        
        parBasicCfg['init_mem'] = assertValue(pyObj=parProp, key='initial-memory')
        parBasicCfg['max_mem'] = assertValue(pyObj=parProp, key='maximum-memory')

        #vNIC
        nicURIs = assertValue(pyObj=parProp, key='nic-uris')
        vNICsCfg = dict()
        i=0
        for nicURI in nicURIs:
            nicCfg = dict()
            i+=1
            nicProp = getNICProperties(hmc, nicURI=nicURI)
            
            nicCfg['name'] = assertValue(pyObj=nicProp, key='name')
            nicCfg['desc'] = assertValue(pyObj=nicProp, key='description').replace("\n", "")
            nicCfg['devNum'] = assertValue(pyObj=nicProp, key='device-number')
             
            if assertValue(pyObj=parProp, key='type') == 'ssc':
                if bool(assertValue(pyObj=nicProp, key='ssc-management-nic')) == True:
                    nicCfg['sscIPAddrType'] = assertValue(pyObj=nicProp, key='ssc-ip-address-type')
                    nicCfg['sscIPAddr'] = assertValue(pyObj=nicProp, key='ssc-ip-address')
                    nicCfg['sscMaskPrefix'] = assertValue(pyObj=nicProp, key='ssc-mask-prefix')
                   
                    if assertValue(pyObj=nicProp, key='vlan-id'):
                        nicCfg['vlanID'] = assertValue(pyObj=nicProp, key='vlan-id')

            if assertValue(pyObj=nicProp, key='type') == 'osd':
                vsProp = getVirtualSwitchProperties(hmc, vsURI=assertValue(pyObj=nicProp, key='virtual-switch-uri'))
                adapURI = assertValue(pyObj=vsProp, key='backing-adapter-uri')
                nicCfg['adapPort'] = assertValue(pyObj=vsProp, key='port')
                adapProp = getAdapterProperties(hmc, adaURI=adapURI)
                nicCfg['adapName'] = assertValue(pyObj=adapProp, key='name')
            vNICsCfg['vNIC'+ str(i)] = nicCfg
        parBasicCfg['vNICs'] = vNICsCfg
        
        #Identify HMC version that Storage Group feature was available. 
        if sgIsAvai == True:
            parSGDevList = []
            for i,v in enumerate(attachedParList):
                if v == parName: 
                    parSGDevList.append(str(attachedSGDevList[i]))

            # write SG-DevNum into current partition backup config.
            parBasicCfg['sgDevNum'] = parSGDevList
            
            # the FICON part
            parFICONList = []
            parSGUriList = assertValue(pyObj=parProp, key='storage-group-uris')
            for parSGUri in parSGUriList:
                sgProperties = getStorageGroupProperties(hmc, sgURI=parSGUri)
                if assertValue(pyObj=sgProperties, key='type') == 'fc':
                    parFICONList.append(assertValue(pyObj=sgProperties, key='name'))
            parBasicCfg['sgFICON'] = parFICONList            
            
        elif sgIsAvai == False:

            hbaURIs = assertValue(pyObj=parProp, key='hba-uris')
            vHBAsCfg = dict()
            i=0
            for hbaURI in hbaURIs:

                hbaCfg = dict()
                i+=1

                hbaProp = getHBAProperties(hmc, hbaURI=hbaURI)
                
                hbaCfg['name'] = assertValue(pyObj=hbaProp, key='name')
                hbaCfg['desc'] = assertValue(pyObj=hbaProp, key='description').replace("\n", "")
                hbaCfg['devNum'] = assertValue(pyObj=hbaProp, key='device-number')
                adapPortURI = assertValue(pyObj=hbaProp, key='adapter-port-uri')

                storPortProp = getStorPortProperties(hmc, storPortURI=adapPortURI)
                adapURI = assertValue(pyObj=storPortProp, key='parent')

                adapProp = getAdapterProperties(hmc, adaURI=adapURI)
                hbaCfg['adapName'] = assertValue(pyObj=adapProp, key='name')
                
                vHBAsCfg['vHBA'+ str(i)] = hbaCfg
            parBasicCfg['vHBAs'] = vHBAsCfg
            
        virtualFuncUriList = assertValue(pyObj=parProp, key='virtual-function-uris')
        vfCfgList = []
        for vfUri in virtualFuncUriList:
            vfRet = getVirtFuncProperties(hmc, vfUri)
            vfCfg = dict()
            vfCfg['name'] = assertValue(pyObj=vfRet, key='name')
            vfCfg['description'] = assertValue(pyObj=vfRet, key='description')
            vfCfg['device-number'] = assertValue(pyObj=vfRet, key='device-number')
            
            adapProp = getAdapterProperties(hmc, adaURI=assertValue(pyObj=vfRet, key='adapter-uri'))
            vfCfg['adapter-name'] = assertValue(pyObj=adapProp, key='name')
            vfCfgList.append(vfCfg)
        parBasicCfg['zAccelerators'] = vfCfgList
        
        # add the crypto-configuration for crypto
        cryptoCfg = []
        if assertValue(pyObj=parProp, key='crypto-configuration') != None:
            cryptoCfg = assertValue(pyObj=parProp, key='crypto-configuration')
            adapNameList = []
            for cryptoAdapterUri in cryptoCfg['crypto-adapter-uris']:
                adapProp = getAdapterProperties(hmc, adaURI=cryptoAdapterUri)
                adapNameList.append(assertValue(pyObj=adapProp, key='name'))
            
            cryptoCfg.pop('crypto-adapter-uris')
            cryptoCfg['crypto-adapter-names'] = adapNameList
        parBasicCfg['zCryptos'] = cryptoCfg
        
        # add for the boot option (for boot_device is "storage group")
        bootOptCfg = dict()
        bootOptCfg['boot_device'] = assertValue(pyObj=parProp, key='boot-device')
        if bootOptCfg['boot_device'] == 'storage-volume':
            bootOptCfg['boot-timeout'] = assertValue(pyObj=parProp, key='boot-timeout')

            bootStorVolUri = assertValue(pyObj=parProp, key='boot-storage-volume')
            storVolRet = getStorVolProperties(hmc, bootStorVolUri)
            
            bootOptCfg['volume_description'] = assertValue(pyObj=storVolRet, key='description')
            bootOptCfg['volume_size'] = assertValue(pyObj=storVolRet, key='size')
            
            bootStorGroupUri = bootStorVolUri.split('/storage-volumes/')[0]
            storGroupRet = getStorageGroupProperties(hmc, sgURI=bootStorGroupUri)
            bootOptCfg['storage_group_name'] = assertValue(pyObj=storGroupRet, key='name')
            bootOptCfg['storage_group_type'] = assertValue(pyObj=storGroupRet, key='type')
            
            if assertValue(pyObj=storGroupRet, key='type') == 'fcp':
                bootOptCfg['fcp-boot-configuration-selector'] = assertValue(pyObj=parProp, key='boot-configuration-selector')
                bootOptCfg['fcp-volume-uuid'] = assertValue(pyObj=storVolRet, key='uuid')
            elif assertValue(pyObj=storGroupRet, key='type') == 'fc':
                ctrlUnitUri = assertValue(pyObj=storVolRet, key='control-unit-uri')
                ctrlUnitRet = getStorageControlUnitProperties(hmc, ctrlUnitUri)
                
                bootOptCfg['fc-logical-address'] = assertValue(pyObj=ctrlUnitRet, key='logical-address')
                bootOptCfg['fc-unit-address'] = assertValue(pyObj=storVolRet, key='unit-address')
            else:
                # error
                pass
            
        parBasicCfg['zzBootOpt'] = bootOptCfg
        
        print "%s backup is Done."%parName
        allParsCfg[parName] = parBasicCfg     

    # Generate backup config file
    allConfig = ConfigParser.ConfigParser(allow_no_value=True)
    for key1 in sorted(allParsCfg.keys()):
        allConfig.add_section(key1)
        for key2 in sorted(allParsCfg[key1].keys()):
            if "par" in key2:
                allConfig.set(key1, '#partition')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])
            elif "proc" in key2:
                allConfig.set(key1, '#processor')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])
            elif "mem" in key2:
                allConfig.set(key1, '#memory')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])
            elif "sgDevNum" in key2:
                allConfig.set(key1, '#FCP Storage-Groups')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])
            elif "sgFICON" in key2:
                allConfig.set(key1, '#FICON Storage-Groups')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])
            elif "vNICs" in key2:
                allConfig.set(key1, '#virtual NICs')
                for key3 in sorted(allParsCfg[key1][key2].keys()):
                    for key4 in sorted(allParsCfg[key1][key2][key3].keys()):
                        allConfig.set(key1, key3 + '_' + key4, allParsCfg[key1][key2][key3][key4])
            elif "vHBAs" in key2:
                allConfig.set(key1, '#virtual HBAs')
                for key3 in sorted(allParsCfg[key1][key2].keys()):
                    for key4 in sorted(allParsCfg[key1][key2][key3].keys()):
                        allConfig.set(key1, key3 + '_' + key4, allParsCfg[key1][key2][key3][key4])
            elif "zAccelerators" in key2:
                allConfig.set(key1, '#accelerator virtual functions')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])
            elif "zCryptos" in key2:
                allConfig.set(key1, '#cryptos')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])
            elif "zzBootOpt" in key2:
                allConfig.set(key1, '#boot option')
                allConfig.set(key1, key2 ,allParsCfg[key1][key2])

    if os.path.exists(backupDir) is False:
        os.makedirs(backupDir)
            
    # Write backup configs into a file
    filePath = backupDir + '/' + cpcName + '-Partitions-' + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + '.cfg'

    with open(filePath, 'wb') as configfile:
        allConfig.write(configfile)
    
    if allConfig :
        print ("\n%s partitions' configuration were saved in below file successfully."%cpcName)
        print filePath
    else:
        print "Partition backup failed, please check the environment manually."
        
except Exception as exc:
    if exc.message != None:
        print exc.message
  
finally:
    # cleanup
    if hmc != None:
        hmc.logoff()
