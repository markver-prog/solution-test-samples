'''
Created on Mar 30, 2018

This script intends to restore the storage groups based on the config file which been generated before.
The storage groups include the FCP and FICON storage groups.

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
emailList = None
createPass = list()
createFail = list()
sectionDict = dict()

# for multi-thread write protection
lock = threading.Lock()

# ------------------------------------------------------------------ #
# ----- Start of parseArgs function -------------------------------- #
# ------------------------------------------------------------------ #
def parseArgs():
    print ">>> parsing the input parameters..."
    global hmcHost, cpcName, userId, password, configFile, emailList

    parser = argparse.ArgumentParser(description='restore the storage groups by configure file')
    parser.add_argument('-hmc', '--hmcHost', metavar='<HMC host IP>', help='HMC host IP', required=True)
    parser.add_argument('-cpc', '--cpcName', metavar='<cpc name>', help='cpc name', required=True)
    parser.add_argument('-uid', '--userId', metavar='<user id>', help='user id', required=True)
    parser.add_argument('-psw', '--password', metavar='<password>', help='password', required=True)
    parser.add_argument('-config', '--configFile', metavar='<configure file name>', help='indicate configure file name / location', required=True)
    parser.add_argument('-email', '--emailList', metavar='<storage admin email address list>', help='split the email addresses with comma', required=True)

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
    #storage admin email list
    _emailList = assertValue(pyObj=args, key='emailList', listIndex=0, optionalKey=True)
    emailList = checkValue('emailList', _emailList , emailList)


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
# ----- Start of procSingleStorageGroup function ------------------- #
# ------------------------------------------------------------------ #
def procSingleStorageGroup(sgName):
    global sectionDict
    try:
        if lock.acquire():
            sgDict = sectionDict[sgName]
            sgTemp = constructSgTemplate(sgName, sgDict)
            if sgTemp == None:
                print ">>> Create storage group template failed!!!", sgName
            lock.release()
        if lock.acquire():
            sgRet = createStorageGroup(hmc, sgTemp)
            createPass.append(sgName)
            lock.release()
    except Exception as exc:
        print ">>> Create storage group failed!!!", sgName

        createFail.append(sgName)
        lock.release()

# ------------------------------------------------------------------ #
# ----- End of procSingleStorageGroup function --------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of constructSgTemplate function ---------------------- #
# ------------------------------------------------------------------ #
def constructSgTemplate(sgName, sgDict):
    global cpcURI, emailList
    sgTempl = dict()

    try:
        sgTempl['name'] = sgName
        sgTempl['cpc-uri'] = cpcURI
        if (sgDict.has_key('sgdesc') and sgDict['sgdesc'] != ''):
            sgTempl['description'] = sgDict['sgdesc']
        sgTempl['type'] = sgDict['stortype']

        if (sgDict['sgshared'] == "True"):
            sgTempl['shared'] = True
        else:
            sgTempl['shared'] = False

        if (sgTempl['type'] == 'fcp'):
            sgTempl['max-partitions'] = int(sgDict['maxnumofpars'])

        sgTempl['connectivity'] = int(sgDict['numofpaths'])
        svsTempl = constructSvTemplate(sgName, eval(sgDict['sgstorvolscfg']))
        sgTempl['storage-volumes'] = svsTempl
        sgTempl['email-to-addresses'] = emailList.split(',')
    except  Exception as exc:
        print ">>> Construct storage group template failed: ", sgName
        raise exc
    return sgTempl

# ------------------------------------------------------------------ #
# ----- End of constructSgTemplate function ------------------------ #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of constructSvTemplate function --------table 10------ #
# ------------------------------------------------------------------ #
def constructSvTemplate(sgName, svCfgList):
    svsTempl = list()

    try:
        for sv in svCfgList:
            svTempl = dict()
            svTempl['operation'] = 'create'
            if (sv.has_key('storVolDesc') and sv['storVolDesc'] != ''):
                svTempl['description'] = sv['storVolDesc']

            if (sv.has_key('storVolSize')):
                svTempl['size'] = float(sv['storVolSize'])
            svTempl['usage'] = sv['storVolUse']

            if sv.has_key('storVolModel'):
                svTempl['model'] = sv['storVolModel']

            if sv.has_key('storVolDevNum'):
                svTempl['device-number'] = sv['storVolDevNum']

            svsTempl.append(svTempl)
    except  Exception as exc:
        print ">>> Construct storage volume template failed: ", sgName
        raise exc
    return svsTempl

# ------------------------------------------------------------------ #
# ----- End of constructSvTemplate function ------------------------ #
# ------------------------------------------------------------------ #

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
    for sgName in sectionDict.keys():
        t = threading.Thread(target=procSingleStorageGroup, args=(sgName,))
        print ">>> Constructing Storage Group: " + sgName + "..."
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

except IOError as exc:
    print ">>> Configure file read error!"
except Exception as exc:
    print exc.message

finally:
    if hmc != None:
        hmc.logoff()
    if (len(createPass) != 0):
        print "Here are the storage group(s) been created successfully:", createPass
    if (len(createFail) != 0):
        print "Here are the storage group(s) been created failed:", createFail
    print "Script run completed!!!"
