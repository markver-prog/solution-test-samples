'''
Created on Dec 5, 2017

This script intends to restore the partitions based on the config file which been generated before.
Please double check if the adapter IDs are changed in the config file,
if yes, please update the adapter IDs in the config file according to the PCHID Mapping table.

All the partition information will be created simultaneously by multi-threading.
Please double check the restored parameters (processors, memory, vNic, storage groups, device numbers and boot options)
before you start the partition.

@author: mayijie
'''

from CommonAPI.prsm2api import *
from CommonAPI.wsaconst import *
from CommonAPI.hmcUtils import *
from CommonAPI.readConfig import *
import argparse, ConfigParser, threading

hmc = None
cpcID = None

hmcHost = None
cpcName = None
userId = None
password = None
configFile = None
createPass = list()
createFail = list()
sectionDict = dict()

# default SSC partition master password
SSC_MASTER_PASSWORD = 'passw0rd'

PARTITION_API_MAP = {'par_type' : 'type',
                     'par_desc' : 'description',
                     'par_reserveresources' : 'reserve-resources',      # boolean
                     'proc_mode' : 'processor-mode',
                     'proc_type' : None,
                     'proc_num' : ['cp-processors', 'ifl-processors'],
                     'init_mem' : 'initial-memory',
                     'max_mem' : 'maximum-memory',
                     'vnic' : None,
                     'sgdevnum' : None,
                     'sgficon' : None,
                     'zaccelerators' : None,
                     'zcryptos' : None,
                     'zzbootopt' : None
                    }

# additional properties for the SSC partition
SSC_API_MAP = {'par_sschostname' : 'ssc-host-name',
               'par_sscmasteruserid' : 'ssc-master-userid',
               'par_sscmasterpw' : 'ssc-master-pw',
               # following are optional
               'par_sscdns' : 'ssc-dns-servers',                 # Array of string
               'par_sscipv4gw' : 'ssc-ipv4-gateway',
              }

# properties for the nic object
NIC_API_MAP = {'name' : 'name',
               'adapname' : None,
               'adapport' : None,
               'devnum' : 'device-number',
               'desc' : 'description',
               # following properties are for ssc partitions
               'sscipaddr' : 'ssc-ip-address',
               'sscipaddrtype' : 'ssc-ip-address-type',
               'sscmaskprefix' : 'ssc-mask-prefix',
               'vlanid' : 'vlan-id'
              }
# for multi-thread write protection
lock = threading.Lock()

# ------------------------------------------------------------------ #
# ----- Start of parseArgs function -------------------------------- #
# ------------------------------------------------------------------ #
def parseArgs():
    print ">>> parsing the input parameters..."
    global hmcHost, cpcName, userId, password, configFile

    parser = argparse.ArgumentParser(description='restore the partitions by configure file')
    parser.add_argument('-hmc', '--hmcHost', metavar='<HMC host IP>', help='HMC host IP', required=True)
    parser.add_argument('-cpc', '--cpcName', metavar='<cpc name>', help='cpc name', required=True)
    parser.add_argument('-uid', '--userId', metavar='<user id>', help='user id', required=True)
    parser.add_argument('-psw', '--password', metavar='<password>', help='password', required=True)
    parser.add_argument('-config', '--configFile', metavar='<configure file name>',
                        help='indicate configure file name / location', required=True)

    args = vars(parser.parse_args())
    #hmc host
    _hmcHost = assertValue(pyObj=args, key='hmcHost', listIndex=0, optionalKey=True)
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
    #config file
    _configFile = assertValue(pyObj=args, key='configFile', listIndex=0, optionalKey=True)
    configFile = checkValue('configFile', _configFile, configFile)

# ------------------------------------------------------------------ #
# ----- End of parseArgs function ---------------------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of loadConfig function ------------------------------- #
# ------------------------------------------------------------------ #
def loadConfig(configFile):
    print ">>> loading the config file..."
    global sectionDict

    try:
        if configFile == None:
            exc = IOError("Empty file or directory name")
            exc.errno = 2
            raise exc
        if '/' not in configFile:
            configFile = os.path.join(sys.path[0], configFile)
        config = ConfigParser.RawConfigParser()
        config.readfp(open(configFile))

        sections = config.sections()
        for section in sections:
            itemDict = dict()
            items = config.items(section)
            for key, value in items:
                itemDict[key] = value
            sectionDict[section] = itemDict

    except IOError as exc:
        print ">>> Cannot load configuration file [%s]"%(configFile)
        raise exc

# ------------------------------------------------------------------ #
# ----- End of loadConfig function --------------------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of procSinglePartition function ---------------------- #
# ------------------------------------------------------------------ #
def procSinglePartition(parName):
    global sectionDict
    try:
        if lock.acquire():
            partitionDict = sectionDict[parName]
            (parTemp, vnicDict, sgDevNumDict, ficonList, acceList, cryptoDict, bootOptionDict) = createPartitionTemplate(parName, partitionDict)
            lock.release()
        if lock.acquire():
            partRet = createPartition(hmc, cpcID, parTemp)
            lock.release()
        if lock.acquire():
            if partRet != None:
                createPass.append(parName)
                if len(vnicDict) != 0:
                    constructVnics(partRet, parName, vnicDict)
                if len(sgDevNumDict) != 0:
                    constructStorageGroups(partRet, parName, sgDevNumDict=sgDevNumDict)
                    setDeviceNumber(partRet, parName, sgDevNumDict)
                if len(ficonList) != 0:
                    constructStorageGroups(partRet, parName, ficonList=ficonList)
                if len(acceList) != 0:
                    constructAccelerators(partRet, parName, acceList)
                if len(cryptoDict) != 0:
                    constructCryptos(partRet, parName, cryptoDict)
                if len(bootOptionDict) != 0:
                    couldStart = setBootOption(partRet, parName, bootOptionDict)
            else:
                createFail.append(parName)
            lock.release()
    except Exception as exc:
        print ">>> Create partition failed: ", parName

        createFail.append(parName)
        lock.release()

# ------------------------------------------------------------------ #
# ----- End of procSinglePartition function ------------------------ #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of createPartitionTemplate function ------------------ #
# ------------------------------------------------------------------ #
def createPartitionTemplate(parName, partitionDict):
    global PARTITION_API_MAP
    iProcNum = None
    iProcType = None
    partitionTempl = dict()
    vnicDict = dict()
    sgDevNumDict = dict()
    ficonList = []
    acceList = []
    cryptoDict = dict()
    bootOptionDict = dict()

    try:
        partitionTempl['name'] = parName
        for propertyKey in PARTITION_API_MAP.keys():
            if partitionDict.has_key(propertyKey):
                if (propertyKey == 'par_type'):
                    partitionTempl[PARTITION_API_MAP[propertyKey]] = partitionDict[propertyKey]
                    if (partitionDict[propertyKey] == "ssc"):
                        for sscKey in SSC_API_MAP.keys():
                            if partitionDict.has_key(sscKey):
                                if sscKey == 'par_sscdns':
                                    partitionTempl[SSC_API_MAP[sscKey]] = partitionDict[sscKey].split(',')
                                else:
                                    partitionTempl[SSC_API_MAP[sscKey]] = partitionDict[sscKey]
                            elif sscKey == 'par_sscmasterpw':
                                partitionTempl[SSC_API_MAP[sscKey]] = SSC_MASTER_PASSWORD
                            else:
                                pass
                elif (propertyKey == 'proc_mode' or propertyKey == 'par_desc'):
                    partitionTempl[PARTITION_API_MAP[propertyKey]] = partitionDict[propertyKey]
                elif (propertyKey == 'par_reserveresources'):
                    partitionTempl[PARTITION_API_MAP[propertyKey]] = True if (partitionDict[propertyKey].lower() == 'true') else False
                elif (propertyKey == 'init_mem' or propertyKey == 'max_mem'):
                    if (int(partitionDict[propertyKey]) < 1024):
                        partitionTempl[PARTITION_API_MAP[propertyKey]] = int(partitionDict[propertyKey]) * 1024
                    else:
                        partitionTempl[PARTITION_API_MAP[propertyKey]] = int(partitionDict[propertyKey])
                elif (propertyKey == 'proc_type'):
                    if iProcNum == None:
                        iProcType = partitionDict[propertyKey].lower()
                    else:
                        if partitionDict[propertyKey].lower() == 'cp':
                            partitionTempl[PARTITION_API_MAP['proc_num'][0]] = iProcNum
                        elif partitionDict[propertyKey].lower() == 'ifl':
                            partitionTempl[PARTITION_API_MAP['proc_num'][1]] = iProcNum
                        else:
                            exc = Exception("The procType should either be 'cp' or be 'ifl', other values invalid!")
                            raise exc
                elif (propertyKey == 'proc_num'):
                    if iProcType == None:
                        iProcNum = int(partitionDict[propertyKey])
                    else:
                        if iProcType == "cp":
                            partitionTempl[PARTITION_API_MAP['proc_num'][0]] = int(partitionDict[propertyKey])
                        elif iProcType == "ifl":
                            partitionTempl[PARTITION_API_MAP['proc_num'][1]] = int(partitionDict[propertyKey])
                        else:
                            exc = Exception("The procType should either be 'cp' or be 'ifl', other values invalid!")
                            raise exc
                elif (propertyKey == 'sgdevnum'):
                    vhbaList = eval(partitionDict[propertyKey])
                    for vhba in vhbaList:
                        vhbaProp = vhba.split(':')
                        if sgDevNumDict.has_key(vhbaProp[0]):
                            sgDevNumDict[vhbaProp[0]].append(vhbaProp[1])
                        else:
                            sgDevNumDict[vhbaProp[0]] = [vhbaProp[1]]
                elif (propertyKey == 'sgficon'):
                    ficonList = eval(partitionDict[propertyKey])
                elif (propertyKey == 'zaccelerators'):
                    acceList = eval(partitionDict[propertyKey])
                elif (propertyKey == 'zcryptos'):
                    cryptoDict = eval(partitionDict[propertyKey])
                elif (propertyKey == 'zzbootopt'):
                    bootOptionDict = eval(partitionDict[propertyKey])

                else:
                    # parse vNIC
                    pass
            elif propertyKey == 'vnic':
                for key in partitionDict.keys():
                    if re.match('^vnic\d-*', key):
                        vnicDict[key] = partitionDict[key]
            else:
                pass

    except  Exception as exc:
        print ">>> Create partition template failed!"
        raise exc
    return (partitionTempl, vnicDict, sgDevNumDict, ficonList, acceList, cryptoDict, bootOptionDict)

# ------------------------------------------------------------------ #
# ----- End of createPartitionTemplate function -------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of createPartition function -------------------------- #
# ------------------------------------------------------------------ #
def createPartition(hmc, cpcID, parTemp):
    try:
        httpBody = json.dumps(parTemp)
        resp = getHMCObject(hmc,
                            WSA_URI_PARTITIONS_CPC%cpcID,
                            "Create Partition",
                            httpMethod = WSA_COMMAND_POST,
                            httpBody = httpBody,
                            httpGoodStatus = 201,           # HTTP created
                            httpBadStatuses = [400, 403, 404, 409, 503])
        return assertValue(pyObj=resp, key='object-uri')

    except Exception as exc:
        print ">>> Create partition failed while HTTP requesting."
        raise exc

# ------------------------------------------------------------------ #
# ----- End of createPartition function ---------------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of constructVnics function --------------------------- #
# ------------------------------------------------------------------ #
def constructVnics(partUri, partName, vnicDict):
    global hmc, cpcID
    vnicNameSet = set()
    partID = partUri.replace('/api/partitions/','')
    try:
        for key in vnicDict.keys():
            if re.match('.*_name$', key):
                vnicNameSet.add(key)

        for vnicName in vnicNameSet:
            vnicPrefix = vnicName[:5]
            vnicPrefixDict = dict()
            for key in vnicDict.keys():
                pattern = '^'+vnicPrefix
                if re.match(pattern, key):
                    vnicPrefixDict[key[6:]] = vnicDict[key]
            if (vnicPrefixDict.has_key("adapname")):
                adapterDict = selectAdapter(hmc, vnicPrefixDict["adapname"], cpcID)
                vsUri = selectVirtualSwitch(hmc, cpcID, adapterDict[KEY_ADAPTER_URI], vnicPrefixDict["adapport"])
                nicTempl = dict()
                nicTempl[NIC_API_MAP['name']] = vnicPrefixDict['name']
                nicTempl['virtual-switch-uri'] = vsUri
                if vnicPrefixDict.has_key('devnum'):
                    nicTempl[NIC_API_MAP['devnum']] = vnicPrefixDict['devnum']
                if vnicPrefixDict.has_key('desc'):
                    nicTempl[NIC_API_MAP['desc']] = vnicPrefixDict['desc']
                if vnicPrefixDict.has_key('sscipaddr'):
                    nicTempl['ssc-management-nic'] = True
                    nicTempl[NIC_API_MAP['sscipaddr']] = vnicPrefixDict['sscipaddr']
                    nicTempl[NIC_API_MAP['sscipaddrtype']] = vnicPrefixDict['sscipaddrtype']
                    nicTempl[NIC_API_MAP['sscmaskprefix']] = vnicPrefixDict['sscmaskprefix']
                    if vnicPrefixDict.has_key('vlanid'):
                        nicTempl[NIC_API_MAP['vlanid']] = int(vnicPrefixDict['vlanid'])
                        nicTempl['vlan-type'] = None
                nicRet = createNIC(hmc, partID, nicTempl)
                print ">>> Create vNIC for %s successfully: %s" %(partName, vnicPrefixDict["name"])
            else:
                print ">>> Create vNIC for %s failed: %s, only support OSA card this time" %(partName, vnicPrefixDict["name"])

    except Exception as exc:
        print ">>> Create vNIC for %s failed!" %partName

# ------------------------------------------------------------------ #
# ----- End of constructVnics function ----------------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of constructStorageGroups function ------------------- #
# ------------------------------------------------------------------ #
def constructStorageGroups(partUri, parName, sgDevNumDict=None, ficonList=None):
    global hmc
    partID = partUri.replace('/api/partitions/','')
    sgNameList = []
    if sgDevNumDict != None:
        sgNameList = sgDevNumDict.keys()
    elif ficonList != None:
        sgNameList = ficonList
    else:
        exc = Exception("sgDevNumDict and ficonList should have at least one is not None!")
        raise exc

    try:
        for sgName in sgNameList:
            sgUri = selectStorageGroup(hmc, sgName)
            if (sgUri == None):
                exc = Exception("The indicated storage group name: " + sgName + " not exist in the system, please double check!")
                raise exc
            sgTempl = dict()
            sgTempl['storage-group-uri'] = sgUri
            sgRet = attachStorageGroup(hmc, partID, sgTempl)
            print ">>> Construct storage group for %s successfully: %s" %(parName, sgName)
    except Exception as exc:
        print ">>> Attach storage group for %s failed!" %parName

# ------------------------------------------------------------------ #
# ----- End of constructStorageGroups function --------------------- #
# ------------------------------------------------------------------ #

def constructAccelerators(partUri, parName, acceList):
    global hmc, cpcID
    partID = partUri.replace('/api/partitions/','')

    try:
        for acceDict in acceList:
            adapterName = acceDict.pop('adapter-name')
            adapterUri = selectAdapter(hmc, adapterName, cpcID)[KEY_ADAPTER_URI]
            acceDict['adapter-uri'] = adapterUri

            vfRet = createVirtualFunction(hmc, partID, acceDict)
            print ">>> Construct accelerator virtual function for %s successfully: %s" %(parName, acceDict['name'])
    except Exception as exc:
        print ">>> Construct accelerator failed!"


def constructCryptos(partUri, parName, cryptoDict):
    global hmc, cpcID
    partID = partUri.replace('/api/partitions/','')

    try:
        adapterNameList = cryptoDict.pop('crypto-adapter-names')
        adapterUriList = []
        for adapterName in adapterNameList:
            adapterUri = selectAdapter(hmc, adapterName, cpcID)[KEY_ADAPTER_URI]
            adapterUriList.append(adapterUri)
        cryptoDict['crypto-adapter-uris'] = adapterUriList

        increaseCryptoConfiguration(hmc, partID, cryptoDict)
        print ">>> Construct cryptos for %s successfully: %s" %(parName, adapterNameList)
    except Exception as exc:
        print ">>> Construct cryptos for %s failed!" %parName


# ------------------------------------------------------------------ #
# ----- Start of setDeviceNumber function -------------------------- #
# ------------------------------------------------------------------ #
def setDeviceNumber(partUri, parName, sgDevNumDict):
    global hmc
    partID = partUri.replace('/api/partitions/','')
    try:
        for sgName in sgDevNumDict.keys():
            sgUri = selectStorageGroup(hmc, sgName)
            if (sgUri == None):
                exc = Exception("The indicated storage group name: " + sgName + " not exist in the system, please double check!")
                raise exc
            sgID = sgUri.replace('/api/storage-groups/', '')
            vsrList = listVirtualStorageResourcesOfStorageGroup(hmc, sgID)

            for vsr in vsrList:
                if vsr['partition-uri'] == partUri:
                    vsrTempl = dict()

                    vsrTempl['device-number'] = sgDevNumDict[sgName].pop()
                    if updateVirtualStorageResourceProperties(hmc, str(vsr['element-uri']), vsrTempl):
                        print ">>> Set device number for %s successfully: %s" %(sgName, vsrTempl['device-number'])
    except Exception as exc:
        print ">>> Device number set for %s failed!" %parName
# ------------------------------------------------------------------ #
# ----- End of setDeviceNumber function ---------------------------- #
# ------------------------------------------------------------------ #

def setBootOption(partUri, parName, bootOptionDict):
    global hmc

    try:
        if bootOptionDict['boot_device'] != 'storage-volume':
            # only set the boot option when boot from SAN
            print ">>> Set boot option for ", parName,  "failed: only support boot from SAN!"
            return False

        bootTempl = dict()
        bootTempl['boot-timeout'] = int(bootOptionDict['boot-timeout'])

        bootSgName = bootOptionDict['storage_group_name']
        bootSgUri = selectStorageGroup(hmc, bootSgName)
        if bootSgUri == None:
            print ">>> Set boot option for %s failed: the boot storage group %s not exist!" %(parName, bootSgName)
            return False
        sgRet = getStorageGroupProperties(hmc, sgURI=bootSgUri)
        if assertValue(pyObj=sgRet, key='fulfillment-state') != 'complete':
            print ">>> Set boot option for %s failed: the boot storage group is in %s state!" %(parName, assertValue(pyObj=sgRet, key='fulfillment-state'))
            return False

        for sgVolUri in assertValue(pyObj=sgRet, key='storage-volume-uris'):
            svRet = getStorVolProperties(hmc, sgVolUri)
            if assertValue(pyObj=sgRet, key='type') == 'fcp':
                if svRet['usage'] == 'boot' and svRet['uuid'] == bootOptionDict['fcp-volume-uuid']:
                    bootTempl['boot-storage-volume'] = sgVolUri
                    bootTempl['boot-configuration-selector'] = int(bootOptionDict['fcp-boot-configuration-selector'])
                    break
            elif assertValue(pyObj=sgRet, key='type') == 'fc':
                ctrlUnitUri = assertValue(pyObj=svRet, key='control-unit-uri')
                ctrlUnitRet = getStorageControlUnitProperties(hmc, ctrlUnitUri)
                if svRet['usage'] == 'boot' and svRet['eckd-type'] == 'base' and assertValue(pyObj=ctrlUnitRet, key='logical-address') == bootOptionDict['fc-logical-address'] and svRet['unit-address'] == bootOptionDict['fc-unit-address']:
                    bootTempl['boot-storage-volume'] = sgVolUri
                    break
            else:
                pass

        if 'boot-storage-volume' in bootTempl:
            if updatePartitionProperties(hmcConn=hmc, parURI=partUri, parProp=bootTempl):
                print ">>> Set boot option for", parName,  "successfully!!!"
                bootTempl2 = dict()
                bootTempl2['boot-device'] = 'storage-volume'
                updatePartitionProperties(hmcConn=hmc, parURI=partUri, parProp=bootTempl2)
                return True
            else:
                print ">>> Set boot option for", parName, "failed!!!"
                return False
        else:
            print ">>> Set boot option for", parName, "failed: couldn't find the target storage volume!!!"
            return False


    except Exception as exc:
        print ">>> Boot option set for %s failed!" %parName


# main function
try:
    parseArgs()
    loadConfig(configFile)

    # Access HMC system and create HMC connection
    print ">>> Creating HMC connection..."
    hmc = createHMCConnection(hmcHost=hmcHost, userID=userId, userPassword=password)
    cpc = selectCPC(hmc, cpcName)
    cpcURI = assertValue(pyObj=cpc, key=KEY_CPC_URI)
    cpcName = assertValue(pyObj=cpc, key=KEY_CPC_NAME)
    cpcStatus = assertValue(pyObj=cpc, key=KEY_CPC_STATUS)

    # Get CPC UUID
    cpcID = cpcURI.replace('/api/cpcs/','')
    print ">>> HMC connection created!"
    threads = []
    for parName in sectionDict.keys():
        t = threading.Thread(target=procSinglePartition, args=(parName,))
        print ">>> Creating partition: " + parName + "..."
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
except IOError as exc:
    print "Configure file read error!", exc
except Exception as exc:
    print exc.message

finally:
    if hmc != None:
        hmc.logoff()
    if (len(createPass) != 0):
        print "Here are the partition(s) been created successfully:", createPass
    if (len(createFail) != 0):
        print "Here are the partition(s) been created failed:", createFail
    print "Script run completed!!!"
