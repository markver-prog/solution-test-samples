#! /usr/bin/env python

# ------------------------------------------------------------------- #
# - This file provides common modules about the use of PRSM2 partition
# - in a CPC which includs VSM (Virtual Server Management), SVM (Storage
# - Virtualization Management) , NVM(Network Virtualization Management),
# - Dashboard Metrics, etc.
# ------------------------------------------------------------------- #
# Author: Daniel Wu (yongwubj@cn.ibm.com) at 09/23/2015
# ------------------------------------------------------------------- #

from wsaconst import *
from hmcUtils import *

import json
import pickle
import re
from subprocess import Popen, PIPE
from sys import exc_info

# logger object
log = logging.getLogger(HMC_API_LOGGER)
logUpd = logging.getLogger(HMC_API_SHORT_LOGGER)

# ======= CONSTANTS =========
KEY_CPC_NAME = 'cpc-name'
KEY_CPC_URI = 'cpc-uri'
KEY_CPC_STATUS = 'cpc-status'
KEY_ADAPTER_STATUS = 'adapter-status'
KEY_ADAPTER_NAME = 'adapter-name'
KEY_ADAPTER_TYPE = 'adapter-type'
KEY_ADAPTER_URI = 'adapter-uri'
UNIQUE_LIST1_VALUES = 'unique-list1-values'
UNIQUE_LIST2_VALUES = 'unique-list2-values'
KEY_ERROR_MSG = 'error-message'
KEY_EXCEPTION = 'exception'
KEY_RETURN_STATUS = 'status'
KEY_DIRECTORY_NAME = 'directory-name'
KEY_FILE_NAME = 'file-name'
KEY_CPC_CONFIG_FILE = 'cpc-config-file'

KEY_VF_NAME = 'virtual-function-name'
KEY_VF_URI = 'virtual-function-uri'
KEY_VF_DEV_NUM = 'virtual-function-device-number'
KEY_VF_ADAPTER_URI = 'virtual-function-adapter-uri'

KEY_ACCESS_MODE = 'access-mode'
KEY_DOMAIN_INDEX = 'domain-index'

YES_OPTION = 'yes'
NO_OPTION = 'no'
YES_NO_OPTIONS = [YES_OPTION, NO_OPTION]
YES_NO_WARNING = "Correct answer is y(yes) or n(no)"
BREAK_OPTION = 'break'
CONTINUE_OPTION = 'continue'
CONT_BREAK_OPTIONS = [CONTINUE_OPTION, BREAK_OPTION]
CONT_BREAK_WARNING = "Correct answer is c(continue) or b(break)"
REPLACE_OPTION = 'replace'
ASK_OPTION = 'ask'
SKIP_OPTION = 'skip'
REPLACE_SKIP_OPTIONS = [REPLACE_OPTION, SKIP_OPTION]
REPLACE_SKIP_WARNING = "Correct answer is r(replace) or s(skip)"
REPLACE_ASK_SKIP_OPTIONS = [REPLACE_OPTION, ASK_OPTION, SKIP_OPTION]
REPLACE_ASK_SKIP_WARNING = "Correct answer is r(replace), a(ask) or s(skip)"
# ======= CONSTANTS =========


def createHMCConnection(hmcHost=None,       # HMC host name or ip address
                        defHost=None,       # default HMC host name or ip address
                        userID=None,        # user ID to be used for HMC authentication
                        userPassword=None   # user password to be used for HMC authentication
                        ):
    log.debug("Entered")
    keys = HMCs.keys()
    if defHost == None or defHost not in keys:
        defHost = keys[0]
    if hmcHost == None:
        questMsg = 'Please, select system name'
        warnMsg = 'Available system names are: %s' % keys
        ans = getValue('System Name', defHost, availValues=keys,
                       promptMsg=questMsg, warnMsg=warnMsg,
                       printSelValue=False, ignoreCase=True,
                       printAvailValues=True)
        hmcHost = HMCs[ans]
    elif hmcHost in keys:
        hmcHost = HMCs[hmcHost]
# create HMC connection object
    hmc = HMCConnection(hmcHost=hmcHost, hmcPort=HMC_API_SSL_port)
# set user ID/password if defined
    if userID != None and userPassword != None:
        hmc.setUserCredential(userid=userID, password=userPassword)
    log.debug("Completed")
    return hmc

# Checks HTTP response code and returns back this 'good' HTTPResponse.status or generates an HMCException


def assertHttpResponse(response,                # HTTPResponse object to be checked
                       methodName,              # Method name to be passed to HMCException in the case of error
                       actionDesc=None,       # Operation description to be added to failure description message
                       goodHttpStatus=200,    # HTTPResponse.status, which assumes as a 'good' response
                       badStatuses=[400, 404],  # 'Bad' HTTPResponse.status(es)
                       exceptionLogLevel=logging.ERROR
                       ):
    log.debug("Entered")
    try:
        # check response status code
        if response.status == goodHttpStatus:         # OK
            return goodHttpStatus
    # known bad statuses
        knownBadHTTPStatuses = [400, 403, 404, 409, 503]
        failMsg = "HTTP Error[status=%s, reason='%s'] happened" % (response.status, response.reason)
        if (response.status not in badStatuses) or (response.status not in knownBadHTTPStatuses):
            failMsg = "Unknown %s" % (failMsg)
        if actionDesc != None:
            failMsg = "%s while doing %s" % (failMsg, actionDesc)
        failMsg = "%s. HTTP good status should be %s" % (failMsg, goodHttpStatus)

        msgBody = response.read()
#    log.error("HMC Error Details: %s", msgBody)
        log.log(exceptionLogLevel, "HMC Error Details: %s", msgBody)
        exc = HMCException(methodName, failMsg, httpResponse=msgBody)
    # print HTTP Response before raising an exception
        log.debug("\tHTTP Response: %s", msgBody)
    # raise an exception
        raise exc
    finally:
        log.debug("Completed")


def assertValue(jsonObj=None,
                #                arrayObj = None,
                pyObj=None,
                key=None,
                listIndex=None,
                optionalKey=False
                ):
    log.debug("Entered")
    if jsonObj != None:
        log.debug("\tjsonObj=%s", jsonObj)
    if pyObj != None:
        log.debug("\tpyObj=%s", pyObj)
    if key != None:
        log.debug("\tkey=%s", key)
    try:
        # check if input object is a JSON object, decode it and return as a python object
        if jsonObj != None:
            try:
                if jsonObj == {} or jsonObj == [] or jsonObj == '':
                    decodedObj = None
                else:
                    decodedObj = json.loads(jsonObj)
                    if key != None:
                        decodedObj = decodedObj[key]
                #decodedObj = json.JSONDecoder().decode(jsonObj)
                return decodedObj
            except ValueError as exc:           # incorrect JSON object have been returned
                exc = HMCException("assertValue",
                                   "Incorrect JSON object: %s" % jsonObj,
                                   origException=exc)
                raise exc
            except KeyError as exc:           # no such key in json object
                if not optionalKey:
                    exc = HMCException("assertValue",
                                       "Key '%s' should be presented in '%s' JSON object" % (key, jsonObj),
                                       origException=exc)
                    raise exc
    # checks if pyObj has key value and returns it. Otherwise raises HMCException
        if pyObj != None and key != None:
            try:
                retObj = pyObj[key]
                if type(retObj) == list and listIndex != None:
                    if listIndex >= len(retObj):
                        log.warn("assertValue: List index (%d) should be less then %d",
                                 listIndex, len(retObj))
                    else:
                        retObj = retObj[listIndex]
                if type(retObj) == unicode:
                    retObj = str(retObj)
                return retObj
            except KeyError as exc:           # no such key in python object
                if not optionalKey:
                    exc = HMCException("assertValue",
                                       "Key '%s' should be presented in '%s' object" % (key, pyObj),
                                       origException=exc)
                    raise exc
#  # checks if pyObj has key value and returns it. Otherwise raises HMCException
#    if arrayObj != None and key != None:
    finally:
        log.debug("Completed")
    return None


def getValue(paramName,       # name of parameter to be read
             defValue,        # default value for parameter
             availValues=None,  # list of parameter's values
             valueType=None,  # type of parameter (int,bool,float,str)
             minValue=None,   # minimum value (for int and float types)
             maxValue=None,   # maximum value (for int and float types)
             promptMsg=None,  # prompt message to be used instead of default
             warnMsg=None,    # warning message to be used instead of default
             printSelValue=True,  # print entered value or not
             maxStrLength=None,   # maximum length of the value
             ignoreCase=False,    # ignore case (if availValues != None)
             printAvailValues=False,
             ):
    log.debug("Entered")
    try:
        while True:
            msg = ''
            if availValues != None and len(availValues) > 0:
                msg = ((("%s" % availValues).replace('[', '{')).replace(']', '} '))
                if defValue not in availValues:
                    defValue = availValues[0]
            if promptMsg != None:
                if printAvailValues:
                    value = raw_input('%s %s[%s]: ' % (promptMsg, msg, defValue))
                else:
                    value = raw_input('%s [%s]: ' % (promptMsg, defValue))
            else:
                value = raw_input('%s %s[%s]: ' % (paramName, msg, defValue))
            if value != '':
                # remove any quotes from input string
                value = value.replace('"', '')
                value = value.replace("'", "")
            else:
                # use default value
                value = defValue

        # convert value to appropriate type
            if valueType != None:
                # boolean type
                if valueType == bool:
                    if type(value) != bool:
                        if "true".startswith(value.lower()):
                            value = True
                        elif "false".startswith(value.lower()):
                            value = False
            # integer type
                elif valueType == int:
                    try:
                        value = int(value)
                    # check value ranges
                        if minValue != None and value < minValue:
                            print 'Valid value for "%s" should be greater than %s' % (paramName, minValue)
                            continue
                        if maxValue != None and value > maxValue:
                            print 'Valid value for "%s" should be less than %s' % (paramName, maxValue)
                            continue
                        return value
                    except:
                        None
            # float type
                elif valueType == float:
                    try:
                        value = float(value)
                    # check value ranges
                        if minValue != None and value < minValue:
                            print 'Valid value for "%s" should be greater than %s' % (paramName, minValue)
                            continue
                        if maxValue != None and value > maxValue:
                            print 'Valid value for "%s" should be less than %s' % (paramName, maxValue)
                            continue
                        return value
                    except:
                        None
            # unknown type
                else:
                    log.warn("Cannot convert value '%s' to %s type. Returning string value...",
                             value, valueType)
                    return value

        # check if value have been converted
            if valueType != None and type(value) != valueType:
                print 'Valid value for "%s" should have %s type' % (paramName, valueType)
                continue

            if availValues != None and len(availValues) > 0:
                selValues = list()
                for av in availValues:
                    # equal values -> break
                    if (ignoreCase and av.lower() == value.lower()) or av == value:
                        selValues = [av]
                        break
                    if (ignoreCase and av.lower().startswith(value.lower())) or av.startswith(value):
                        selValues += [av]
                if len(selValues) == 0:
                    if warnMsg != None:   # print special warning message
                        print warnMsg
                    else:                 # print default warning message
                        print 'Please select valid value for "%s" from %s' % (paramName, availValues)
                    continue
                elif len(selValues) > 1:
                    print "Several matches found %s for your input ('%s')." % (selValues, value)
                    print "Please select one of them."
                    continue
            # only one value matched
                value = selValues[0]
        # check value length
            if maxStrLength != None and len(value) > maxStrLength:
                print 'Length of "%s" value (%s) should be not greater than %s' % (paramName, value, maxStrLength)
                continue

        # print selected value
            if printSelValue and value != defValue:
                print "%s: %s" % (paramName, value)
            return value
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getValue")
        raise exc
    except (KeyboardInterrupt, EOFError) as exc:
        exc = HMCException("getValue",
                           "Script have been interrupted by user request",
                           origException=exc)
        raise exc
    except Exception as exc:
        exc = HMCException("getValue",
                           "Unknown failure happened",
                           origException=exc)
        raise exc
    finally:
        log.debug("Completed")


def checkValue(paramName,       # name of parameter to be read
               value,           # value to be checked
               defValue,        # default value for parameter
               availValues=None,  # list of parameter's values
               valueType=None,  # type of parameter (int,bool,float,str)
               minValue=None,   # minimum value (for int and float types)
               maxValue=None,   # maximum value (for int and float types)
               maxStrLength=None,   # maximum length of the value
               ignoreCase=False,    # ignore case (if availValues != None)
               printAvailValues=False
               ):
    # use default value if None
    if value == None:
        value = defValue

# convert value to appropriate type
    if valueType != None:
        # boolean type
        if valueType == bool:
            if type(value) != bool:
                if "true".startswith(value.lower()):
                    value = True
                elif "false".startswith(value.lower()):
                    value = False
                else:
                    log.warn('Incorrect value for %s: %s. Will use default value (%s)',
                             paramName, value, defValue)
                    value = defValue
    # integer type
        elif valueType == int:
            try:
                value = int(value)
            # check value ranges
                if minValue != None and value < minValue:
                    defValue = max(defValue, minValue)
                    log.warn('Incorrect value (%s) for "%s". It should be greater than %s. Will use default value (%s)',
                             value, paramName, minValue, defValue)
                    value = defValue
                if maxValue != None and value > maxValue:
                    defValue = min(defValue, maxValue)
                    log.warn('Incorrect value (%s) for "%s". It should not be greater than %s. Will use default value (%s)',
                             value, paramName, maxValue, defValue)
                    value = defValue
                return value
            except:
                if defValue != None:
                    return defValue
                return None
    # float type
        elif valueType == float:
            try:
                value = float(value)
            # check value ranges
                if minValue != None and value < minValue:
                    defValue = max(defValue, minValue)
                    log.warn('Incorrect value (%s) for "%s". It should be greater than %s. Will use default value (%s)',
                             value, paramName, minValue, defValue)
                    value = defValue
                if maxValue != None and value > maxValue:
                    defValue = min(defValue, maxValue)
                    log.warn('Incorrect value (%s) for "%s". It should not be greater than %s. Will use default value (%s)',
                             value, paramName, maxValue, defValue)
                    value = defValue
                return value
            except:
                None
    # unknown type
        else:
            log.warn("Cannot convert value '%s' to %s type. Returning string value...",
                     value, valueType)
            return value

# check if value have been converted
    if valueType != None and type(value) != valueType:
        log.warn('Valid value for "%s" should have %s type',
                 paramName, valueType, defValue)
        return defValue

    if availValues != None and len(availValues) > 0:
        selValues = list()
        for av in availValues:
            # equal values -> break
            if (ignoreCase and av.lower() == value.lower()) or av == value:
                selValues = [av]
                break
            if (ignoreCase and av.lower().startswith(value.lower())) or av.startswith(value):
                selValues += [av]
        if len(selValues) == 0:
            log.warn('Incorrect value (%s) for "%s" from %s list. Will use default value (%s)',
                     value, paramName, availValues, defValue)
            return defValue
        elif len(selValues) > 1:
            log.warn("Several matches found %s for your input ('%s'). Will use default value (%s)",
                     selValues, value, defValue)
            return defValue
    # only one value matched
        value = selValues[0]
# check value length
    if value != None and maxStrLength != None and len(value) > maxStrLength:
        log.warn('Length of "%s" value (%s) should be not greater than %s. Will use default value (%s)',
                 paramName, value, maxStrLength, defValue)
        value = defValue

    return value

# ----------------------------------------------------------------- #
# ----------- Common functions ------------------------------------ #
# ----------------------------------------------------------------- #
def getHMCObject(hmcConn,
                 httpPath,
                 actionDesc,
                 httpMethod=WSA_COMMAND_GET,
                 httpBody=None,
                 httpGoodStatus=200,
                 httpBadStatuses=[400, 404],
                 returnJsonObj=False,
                 returnXMLObj=False,
                 exceptionLogLevel=logging.ERROR,
                 httpHeaders={"Content-type": "application/json", "Accept": "*/*"}
                 ):
    log.debug("Entered")
    response = None
    obj = None
    try:
        # get list from HMC by path and httpBody
        response = hmcConn.makeRequest(method=httpMethod,
                                       path=httpPath, body=httpBody, headers=httpHeaders)
    # check HTTP response status code
        assertHttpResponse(response, "getHMCObject", actionDesc,
                           goodHttpStatus=httpGoodStatus,
                           badStatuses=httpBadStatuses,
                           exceptionLogLevel=exceptionLogLevel)
    # parse HTTP response body
        respBody = response.read()

        if returnXMLObj:            # return XML object 'as-is'
            obj = respBody
        elif not returnJsonObj:     # decode JSON object
            obj = assertValue(jsonObj=respBody)
        else:                       # just check if returned object is correct JSON
            assertValue(jsonObj=respBody)
            obj = respBody

    except HMCException as exc:   # raise HMCException
        exc.setMethod("getHMCObject")
        raise exc
    except Exception as exc:
        exc = HMCException("getHMCObject",
                           "Unknown failure happened",
                           httpResponse=response,
                           origException=exc)
        raise exc
    finally:
        log.debug("Completed")
    return obj


def getHMCObjectList(hmcConn,
                     httpPath,
                     actionDesc,
                     responseKey,
                     httpMethod=WSA_COMMAND_GET,
                     httpBody=None,
                     httpGoodStatus=200,
                     httpBadStatuses=[400, 404]
                     ):
    log.debug("Entered")
    response = None
    objArray = []
    try:
        # get list from HMC by path and httpBody
        response = hmcConn.makeRequest(method=httpMethod,
                                       path=httpPath, body=httpBody)
        # check HTTP response status code
        assertHttpResponse(response, "getHMCObjectList", actionDesc,
                           goodHttpStatus=httpGoodStatus,
                           badStatuses=httpBadStatuses)

        # parse HTTP response body
        respBody = response.read()
        # decode JSON object
        respObj = assertValue(jsonObj=respBody)
        # check/extract JSON response
        objArray = assertValue(pyObj=respObj, key=responseKey)

    except HMCException as exc:   # raise HMCException
        exc.setMethod("getHMCObjectList")
#    request = HTTPRequest(httpMethod=httpMethod, httpPath=httpPath,
#                          httpBody=httpBody)
#    exc.setHTTPRequest(request)
        raise exc
    except Exception as exc:
        exc = HMCException("getHMCObjectList",
                           "Unknown failure happened",
                           httpResponse=response,
                           origException=exc)
        raise exc
    finally:
        log.debug("Completed")
    return objArray



# ------------------------------------------------------------------ #
# -------------- Start of createPartition function ----------------- #
# ------------------------------------------------------------------ #

def createPartition(hmcConn,  # HMCConnection object
                    cpcID,   # CPC ID
                    parTempl  # Partition object (stored in JSON notation) to be used as a template
                    ):
    log.debug("Entered")
    try:
        # prepare HTTP body as JSON
        httpBody = json.dumps(parTempl)
        # create partition
        resp = getHMCObject(hmcConn,
                            WSA_URI_PARTITIONS_CPC % cpcID,
                            "Create Partition",
                            httpMethod=WSA_COMMAND_POST,
                            httpBody=httpBody,
                            httpGoodStatus=201,           # HTTP created
                            httpBadStatuses=[400, 403, 404, 409, 503])
        return assertValue(pyObj=resp, key='object-uri')
    except HMCException as exc:   # raise HMCException
        exc.setMethod("createPartition")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------- End of createPartition function ---------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# -------------- Start of getCPCsList function --------------------- #
# ------------------------------------------------------------------ #
def getCPCsList(hmcConn):
    log.debug("Entered")
    try:
        URI = WSA_URI_CPCS
        # get CPCs list
        return getHMCObjectList(hmcConn, URI,
                                "List CPCs",
                                "cpcs",
                                httpBadStatuses=[400])
    except HMCException as exc:  # raise HMCException
        exc.setMethod("getCPCsList")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# -------------- End of getCPCsList function ----------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# -------------- Start of selectCPC function ----------------------- #
# ------------------------------------------------------------------ #
def selectCPC(hmcConn,
              cpcName=None):
    log.debug("Entered")
    try:
        log.debug("Getting CPCs list..")
        # check input parameters
        if hmcConn == None:
            exc = HMCException("selectCPC",
                               "You should specify hmcConn parameter!")
            raise exc
        # get CPCs list
        cpcs = getCPCsList(hmcConn)
        # check CPCs list
        if len(cpcs) == 0:
            if cpcName != None:
                msg = "No such CPC %s. Exiting..." % (cpcName)
            else:
                msg = "No CPC found. Exiting..."
            log.warning(msg)
            return None

        # prepare CPCs list..
        cpcURIs = []
        cpcNames = []
        cpcStatuses = []
        for cpcInfo in cpcs:
            _cpcName = assertValue(pyObj=cpcInfo, key='name')
            _cpcURI = assertValue(pyObj=cpcInfo, key='object-uri')
            _cpcStatus = assertValue(pyObj=cpcInfo, key='status')
            # append cpc name , URI, Status into array
            cpcURIs.append(_cpcURI)
            cpcNames.append(_cpcName)
            cpcStatuses.append(_cpcStatus)

        if cpcName != None:
            if cpcName in cpcNames:
                index = cpcNames.index(cpcName)
                cpcURI = cpcURIs[index]
                cpcStatus = cpcStatuses[index]
            else:
                exc = HMCException("selectCPC",
                                   "Cannot find CPC '%s' in available CPCs list %s!" % (cpcName, cpcNames))
                raise exc

    except HMCException as exc:   # raise HMCException
        exc.setMethod("selectCPC")
        raise exc
    except Exception as exc:
        exc = HMCException("selectCPC",
                           "An exception caught while selecting CPC",
                           origException=exc)
        raise exc
    finally:
        log.debug("Completed")
    return {KEY_CPC_NAME: cpcName, KEY_CPC_URI: cpcURI, KEY_CPC_STATUS: cpcStatus}
# ------------------------------------------------------------------ #
# ---------------- End of selectCPC function ----------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ------- Start of getCPCPartitionsList function ------------------- #
# ------------------------------------------------------------------ #
def getCPCPartitionsList(hmcConn,
                         cpcID
                         ):
    log.debug("Entered")
    try:
        # get partition list of a cpc
        return getHMCObjectList(hmcConn,
                                WSA_URI_PARTITIONS_CPC % cpcID,
                                "List Partitions of a CPC",
                                "partitions",
                                httpBadStatuses=[400])
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getCPCPartitionsList")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# --------- End of getCPCPartitionsList function ------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of getPartitionProperties function --------------- #
# ------------------------------------------------------------------ #
def getPartitionProperties(hmcConn,
                           parID=None,
                           parURI=None):
    log.debug("Entered")
    try:
        # check input params
        if parURI != None:
            URI = parURI
        elif parID != None:
            URI = WSA_URI_PARTITION % parID
        else:
            exc = HMCException("getPartitionProperties",
                               "You should specify either parURI or parID parameters")
            raise exc
        # get partition properties
        return getHMCObject(hmcConn, URI,
                            "Get Partition Properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getPartitionProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------- End of getPartitionProperties function --------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of getStorageGroupProperties function ------------ #
# ------------------------------------------------------------------ #
def getStorageGroupProperties(hmcConn,
                              sgID=None,
                              sgURI=None):
    log.debug("Entered")
    try:
        # check input params
        if sgID != None:
            URI = WSA_URI_STORAGE_GROUP_PROPERTIES % sgID
        elif sgURI != None:
            URI = sgURI
        else:
            exc = HMCException("getStorageGroupProperties",
                               "You should specify either sgID or sgURI parameters")
            raise exc
        # get partition properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get Storage Group Properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getStorageGroupProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------- End of getStorageGroupProperties function ------------ #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of getVirtualStorageResourceProperties function -- #
# ------------------------------------------------------------------ #
def getVirtualStorageResourceProperties(hmcConn,
                                        vsrUri=None):
    log.debug("Entered")
    try:
        # check input params
        if vsrUri != None:
            URI = vsrUri
        else:
            exc = HMCException("getVirtualStorageResourceProperties",
                               "You should specify either URI parameters")
            raise exc
        # get partition properties
        return getHMCObject(hmcConn, URI,
                            "Get Virtual Storage Resource Properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getVirtualStorageResourceProperties")
        #raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------- End of getVirtualStorageResourceProperties function -- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of updatePartitionProperties function ------------ #
# ------------------------------------------------------------------ #
def updatePartitionProperties(hmcConn,
                              parID=None,
                              parURI=None,
                              parProp=None):
    log.debug("Entered")
    updateSuccess = False
    try:
                # check input params
        if parID == None and parURI != None:
            parID = parURI.replace('/api/partitions/', '')
        elif parID == None and parURI == None:
            exc = HMCException("updatePartitionProperties",
                               "you should specify either parURI or parID parameter")
            raise exc
        if parProp != None:
            # update partition properties
            newParProp = parProp
            # prepare HTTP body as JSON
            httpBody = json.dumps(newParProp)
            # update new properties
            getHMCObject(hmcConn,
                         httpPath=WSA_URI_PARTITION % parID,
                         actionDesc='Update Partition Properties',
                         httpMethod=WSA_COMMAND_POST,
                         httpBody=httpBody,
                         httpGoodStatus=204,
                         httpBadStatuses=[400, 403, 404, 409, 503])
            updateSuccess = True
        else:
            exc = HMCException("updatePartitionProperties",
                               "you should specify parProp for partition update")
    except HMCException as exc:   # raise HMCException
        updateSuccess = False
        exc.setMethod("updatePartitionProperties")
        raise exc
    except Exception as exc:
        exc = HMCException("getHMCObject",
                           "Unknown failure happened",
                           httpResponse=response,
                           origException=exc)
    finally:
        log.debug("Completed")
        return updateSuccess
# ------------------------------------------------------------------ #
# ----------- End of updatePartitionProperties function ------------ #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------------- Start of createNIC function ---------------------- #
# ------------------------------------------------------------------ #
def createNIC(hmcConn,
              parID=None,
              nicProp=None):
    log.debug("Entered")
    try:
        # check input params
        if parID == None:
            exc = HMCException("createNIC",
                               "you should specify parID parameter")
            raise exc
        else:
            if nicProp != None:
                # Prepare httpbody as JSON
                httpBody = json.dumps(nicProp)
                # create NIC
                resp = getHMCObject(hmcConn,
                                    WSA_URI_NICS_PARTITION % parID,
                                    "Create NIC",
                                    httpMethod=WSA_COMMAND_POST,
                                    httpBody=httpBody,
                                    httpGoodStatus=201,           # HTTP created
                                    httpBadStatuses=[400, 403, 404, 409, 503])
                return assertValue(pyObj=resp, key='element-uri')
    except HMCException as exc:   # raise HMCException
        exc.setMethod("createNIC")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------------- End of createNIC function ---------------------- #
# ------------------------------------------------------------------ #


# ------------------------------------------------------------------ #
# ----------------- Start of getHBAProperties ---------------------- #
# ------------------------------------------------------------------ #
def getHBAProperties(hmcConn,
                     hbaURI=None,
                     hbaID=None,
                     parID=None):
    log.debug("Entered")
    try:
        # Check input params
        if hbaURI != None:
            URI = hbaURI
        elif hbaID != None and parID != None:
            URI = WSA_URI_HBA%parID%hbaID
        else:
            exc = HMCException("getHBAProperties",
                               "you should specify either hbaURI or both hbaID and parID")
        # get NIC properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get HBA properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getHBAProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ------------------- End of getHBAProperties ---------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ------------ Start of getStorPortProperties ---------------------- #
# ------------------------------------------------------------------ #
def getStorPortProperties(hmcConn,
                     storPortURI=None,
                     adapID=None,
                     storPortID=None):
    log.debug("Entered")
    try:
        # Check input params
        if storPortURI != None:
            URI = storPortURI
        elif adapID != None and storPortID != None:
            URI = WSA_URI_STORAGE_PORT%adapID%storPortID
        else:
            exc = HMCException("getStorPortProperties",
                               "you should specify either storPortURI or both adapID and storPortID")
        # get NIC properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get Storage Port properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getStorPortProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ------------------- End of getStorPortProperties ----------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ------------------Start of getVSRsOfSG function ------------------ #
# ------------------------------------------------------------------ #
def getVSRsOfSG(hmcConn=None,
                sgURI=None):
    log.debug("Entered")
    try:
        if sgURI != None:
            URI = "%s/virtual-storage-resources"%sgURI
        else:
             exc = HMCException("getVSRsOfSG",
                               "You should specify sgURI parameter")
             raise exc
        # get storage volume properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get virtual storage resources list of a Storage Group")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getVSRsOfSG")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ------------------End of getVSRsOfSG function -------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------------- Start of attachStorageGroup function ------------- #
# ------------------------------------------------------------------ #
def attachStorageGroup(hmcConn,
                       partID=None,
                       sgProp=None):
    log.debug("Entered")
    try:
        # check input params
        if partID == None:
            exc = HMCException("attachStorageGroup",
                               "you should specify partition ID parameter")
            raise exc
        else:
            if sgProp != None:
                # Prepare httpbody as JSON
                httpBody = json.dumps(sgProp)
                # attach the storage group
                resp = getHMCObject(hmcConn,
                                    WSA_URI_ATTACH_STORAGE_GROUP % partID,
                                    "Attach storage group",
                                    httpMethod=WSA_COMMAND_POST,
                                    httpBody=httpBody,
                                    httpGoodStatus=204,           # HTTP created
                                    httpBadStatuses=[400, 403, 404, 409, 503])
                return assertValue(pyObj=resp, key='element-uri')
    except HMCException as exc:   # raise HMCException
        exc.setMethod("attachStorageGroup")
        raise exc
    finally:
        log.debug("attachStorageGroup")
# ------------------------------------------------------------------ #
# ----------------- End of attachStorageGroup function ------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----------------- Start of getNICProperties ---------------------- #
# ------------------------------------------------------------------ #
def getNICProperties(hmcConn,
                     nicURI=None,
                     nicID=None,
                     parID=None):
    log.debug("Entered")
    try:
        # Check input params
        if nicURI != None:
            URI = nicURI
        elif nicID != None and parID != None:
            URI = WSA_URI_NIC % parID % nicID
        else:
            exc = HMCException("getNICProperties",
                               "you should specify either nicURI or both nicID and parID")
        # get NIC properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get NIC properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getNICProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ------------------- End of getNICProperties ---------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------------------- Start of createVirtualFunction ------------- #
# ------------------------------------------------------------------ #
def createVirtualFunction(hmcConn,
                          partID=None,
                          virtFuncTemp=None):
    log.debug("Entered")
    try:
        # check the input params
        if partID == None or virtFuncTemp == None:
            exc = HMCException("createVirtualFunction",
                               "you should specify partID and virtFuncTemp")
        # prepare HTTP body as JSON
        httpBody = json.dumps(virtFuncTemp)
        # create virtual function
        resp = getHMCObject(hmcConn,
                            WSA_URI_VIRT_FUNCS_PARTITION % partID,
                            "Create Virtual Function",
                            httpMethod=WSA_COMMAND_POST,
                            httpBody=httpBody,
                            httpGoodStatus=201,
                            httpBadStatuses=[400, 403, 404])
        return assertValue(pyObj=resp, key='element-uri')
    except HMCException as exc:   # raise HMCException
        exc.setMethod("createVirtualFunction")
        raise exc
    finally:
        log.debug("Completed")

# ------------------------------------------------------------------ #
# --------------- Start of increaseCryptoConfiguration ------------- #
# ------------------------------------------------------------------ #
def increaseCryptoConfiguration(hmcConn,
                                partID=None,
                                cryptoCfg=None):
    log.debug("Entered")
    try:
        # check the input params
        if partID == None or cryptoCfg == None:
            exc = HMCException("increaseCryptoConfiguration",
                               "you should specify partID and cryptoCfg")
        # prepare HTTP body as JSON
        httpBody = json.dumps(cryptoCfg)
        # create virtual function
        getHMCObject(hmcConn,
                    WSA_URI_INCREASE_CRYPTO_CONFIGURATION % partID,
                    "Increase Crypto Configuration",
                    httpMethod=WSA_COMMAND_POST,
                    httpBody=httpBody,
                    httpGoodStatus=204,
                    httpBadStatuses=[400, 403, 404, 409, 503])
    except HMCException as exc:   # raise HMCException
        exc.setMethod("increaseCryptoConfiguration")
        raise exc
    finally:
        log.debug("Completed")


# ------------------------------------------------------------------ #
# ----------------- Start of getVirtFuncProperties ----------------- #
# ------------------------------------------------------------------ #
def getVirtFuncProperties(hmcConn,
                          virtFuncURI=None):
    log.debug("Entered")
    try:
        # Check input params
        if virtFuncURI == None:
            exc = HMCException("getVirtFuncProperties",
                               "you should specify virtFuncURI to locate the virtual function")
            raise exc
        else:
            URI = virtFuncURI
            return getHMCObject(hmcConn,
                               URI,
                               "Get Virtual-Function properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getVirtFuncProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ------------------- End of getVirtFuncProperties ----------------- #
# ------------------------------------------------------------------ #


# ------------------------------------------------------------------ #
# ----------------------- Start of selectAdapter ------------------- #
# ------------------------------------------------------------------ #
def selectAdapter(hmcConn=None,
                  adapterName=None,
                  cpcID=None):
    log.debug("Entered")
    try:
        log.debug("Getting Adapters list..")
        # check input parameters
        if adapterName == None or cpcID == None:
            exc = HMCException("selectAdapter",
                               "You should specify both adapterName and cpcName!")
            raise exc
        # get adapters list on the cpc
        adapRet = getCPCAdaptersList(hmcConn, cpcID)
        # check adapters list
        if len(adapRet) == 0:
            msg = "No such adapter %s. Exiting..." % (adapterName)
            log.warning(msg)
        # prepare Adapters list..
        adapterURIs = []
        adapterNames = []
        adapterTypes = []
        adapterStatuses = []

        for adapterInfo in adapRet:
            _adapterName = assertValue(pyObj=adapterInfo, key='name')
            _adapterURI = assertValue(pyObj=adapterInfo, key='object-uri')
            _adapterStatus = assertValue(pyObj=adapterInfo, key='status')
            _adapterType = assertValue(pyObj=adapterInfo, key='type')

        # append adapter name, URI, status and type into array
            adapterURIs.append(_adapterURI)
            adapterNames.append(_adapterName)
            adapterStatuses.append(_adapterStatus)
            adapterTypes.append(_adapterType)

        if adapterName != None:
            if adapterName in adapterNames:
                index = adapterNames.index(adapterName)
                adapterURI = adapterURIs[index]
                adapterStatus = adapterStatuses[index]
                adapterType = adapterTypes[index]
            else:
                exc = HMCException("selectAdapter",
                                   "Cannot find adapter '%s' in available adapters list %s!" % (adapterName, adapterNames))
                raise exc
    except HMCException as exc:   # raise HMCException
        exc.setMethod("selectAdapter")
        raise exc
    except Exception as exc:
        exc = HMCException("selectCPC",
                           "An exception caught while selecting Adapter",
                           origException=exc)
        raise exc
    finally:
        log.debug("Completed")
    return {KEY_ADAPTER_NAME: adapterName,
            KEY_ADAPTER_URI: adapterURI,
            KEY_ADAPTER_STATUS: adapterStatus,
            KEY_ADAPTER_TYPE: adapterType}
# ------------------------------------------------------------------ #
# ----------------------- End of selectAdapter --------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ------- Start of selectStorageGroup function --------------------- #
# ------------------------------------------------------------------ #
def selectStorageGroup(hmcConn=None,
                       storageGroupName=None
                       ):
    log.debug("Entered")
    sgUri = None
    try:
        if (hmcConn == None):
            exc = HMCException("selectStorageGroup",
                               "You should specify the hmc connection!")
            raise exc
        sgRet = getStorageGroupList(hmcConn)
        # check storage group list
        if len(sgRet) == 0:
            msg = "Couldn't find any storage group in the HMC connection. Exiting..."
            log.warning(msg)
        for sgInfo in sgRet:
            if sgInfo["name"] == storageGroupName:
                sgUri = sgInfo["object-uri"]
                break
    except HMCException as exc:   # raise HMCException
        exc.setMethod("selectStorageGroup")
        raise exc
    except Exception as exc:
        raise exc
    finally:
        log.debug("Completed")
        return sgUri

# ------------------------------------------------------------------ #
# ------- End of selectStorageGroup function ----------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ------- Start of selectVirtualSwitch function -------------------- #
# ------------------------------------------------------------------ #
def selectVirtualSwitch(hmcConn=None,
                        cpcID=None,
                        adapterUri=None,
                        adapterPort=None
                        ):
    log.debug("Entered")
    vsUri = None
    try:
        if (hmcConn == None or cpcID == None):
            exc = HMCException("selectVirtualSwitch",
                               "You should specify both hmc connection and cpcID!")
            raise exc
        vsRet = getCPCVirtualSwitchesList(hmcConn, cpcID)
        # check virtual switches list
        if len(vsRet) == 0:
            msg = "No such virtual switch, backing adapter url is %s. Exiting..." % (adapterUri)
            log.warning(msg)
        for vsInfo in vsRet:
            vsPropsTemp = getVirtualSwitchProperties(hmcConn, vsURI=vsInfo["object-uri"])
            if vsPropsTemp["backing-adapter-uri"] == adapterUri.decode("utf-8") and vsPropsTemp["port"] == int(adapterPort):
                vsUri = vsPropsTemp["object-uri"]
                break
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getCPCVirtualSwitchesList")
        raise exc
    except Exception as exc:
        raise exc
    finally:
        log.debug("Completed")
        return vsUri

# ------------------------------------------------------------------ #
# ------- End of selectVirtualSwitch function ---------------------- #
# ------------------------------------------------------------------ #


# ------------------------------------------------------------------ #
# ------- Start of getStorageGroupList function -------------------- #
# ------------------------------------------------------------------ #
def getStorageGroupList(hmcConn,
                        ):
    log.debug("Entered")
    try:
        # get storage group list
        return getHMCObjectList(hmcConn,
                                WSA_URI_LIST_STORAGE_GROUP,
                                "List Storage Groups",
                                "storage-groups",
                                httpBadStatuses=[400])
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getStorageGroupList")
        raise exc
    finally:
        log.debug("Completed")

# ------------------------------------------------------------------ #
# ------- End of getStorageGroupList function ---------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ------- Start of listVirtualStorageResourcesOfStorageGroup function#
# ------------------------------------------------------------------ #
def listVirtualStorageResourcesOfStorageGroup(hmcConn,
                                              sgID,
                                              ):
    log.debug("Entered")
    try:
        # get storage group list
        return getHMCObjectList(hmcConn,
                                WSA_URI_LIST_VIRTUAL_STORAGE_RESOURCES % sgID,
                                "List Virtual Storage Resources of a Storage Group",
                                "virtual-storage-resources",
                                httpBadStatuses=[400, 404])
    except HMCException as exc:   # raise HMCException
        exc.setMethod("listVirtualStorageResourcesOfStorageGroup")
        raise exc
    finally:
        log.debug("Completed")

# ------------------------------------------------------------------ #
# ------- End of listVirtualStorageResourcesOfStorageGroup function  #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of updateVirtualStorageResourceProperties function #
# ------------------------------------------------------------------ #
def updateVirtualStorageResourceProperties(hmcConn,
                                           elementUri=None,
                                           vsrProp=None,
                                           ):
    log.debug("Entered")
    updateSuccess = False
    try:
        # check input params
        if elementUri == None:
            exc = HMCException("updateVirtualStorageResourceProperties",
                               "you should specify the element uri parameter")
            raise exc
        if vsrProp != None:
            # update vsr properties
            newVsrProp = vsrProp
            # prepare HTTP body as JSON
            httpBody = json.dumps(newVsrProp)
            # update new properties
            getHMCObject(hmcConn,
                         httpPath=elementUri,
                         actionDesc='Update Virtual Storage Resource Properties',
                         httpMethod=WSA_COMMAND_POST,
                         httpBody=httpBody,
                         httpGoodStatus=204,
                         httpBadStatuses=[400, 403, 404, 409, 503])
            updateSuccess = True
        else:
            exc = HMCException("updateVirtualStorageResourceProperties",
                               "you should specify vsrProp for vsr update")
    except HMCException as exc:   # raise HMCException
        updateSuccess = False
        exc.setMethod("updateVirtualStorageResourceProperties")
        if exc != None:
            print "[EXCEPTION updateVirtualStorageResourceProperties] ", exc.httpResponse
        raise exc
    except Exception as exc:
        exc = HMCException("getHMCObject",
                           "Unknown failure happened",
                           httpResponse=exc.httpResponse,
                           origException=exc)
    finally:
        log.debug("Completed")
        return updateSuccess
# ------------------------------------------------------------------ #
# ----------- End of updateVirtualStorageResourceProperties function #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of getAdapterProperties function ----------------- #
# ------------------------------------------------------------------ #
def getAdapterProperties(hmcConn,
                         adaURI=None):
    log.debug("Entered")
    try:
        # check input params
        if adaURI != None:
            URI = adaURI
        else:
            exc = HMCException("getAdapterProperties",
                               "You should specify the adaURI parameters")
            raise exc
        # get Adpater properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get Adapter Properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getAdapterProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------- End of getAdapterProperties function ----------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of getVirtualSwitchProperties function ----------- #
# ------------------------------------------------------------------ #
def getVirtualSwitchProperties(hmcConn,
                               vsURI=None):
    log.debug("Entered")
    try:
        # check input params
        if vsURI != None:
            URI = vsURI
        else:
            exc = HMCException("getVirtualSwitchProperties",
                               "You should specify the vsURI parameters")
            raise exc
        # get Virtual Switch properties
        return getHMCObject(hmcConn, URI,
                            "Get Virtual Switch Properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getVirtualSwitchProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------- End of getVirtualSwitchProperties function ----------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of createStorageGroup function ----------------------- #
# ------------------------------------------------------------------ #
def createStorageGroup(hmc, sgTempl):
    try:
        # prepare HTTP body as JSON
        httpBody = json.dumps(sgTempl)
        # create workload
        resp = getHMCObject(hmc,
                            WSA_URI_LIST_STORAGE_GROUP,
                            "Create Storage Group",
                            httpMethod = WSA_COMMAND_POST,
                            httpBody = httpBody,
                            httpGoodStatus = 201,           # HTTP created
                            httpBadStatuses = [400, 403, 404, 409, 503])
        return assertValue(pyObj=resp, key='object-uri')
    except HMCException as exc:   # raise HMCException
        print "[HMCEXCEPTION createStorageGroup]", exc.message
        if exc.httpResponse != None:
            print "[HMCEXCEPTION createStorageGroup]", eval(exc.httpResponse)['message']
        raise exc
    except Exception as exc:
        print "[EXCEPTION createStorageGroup]", exc
        raise exc

# ------------------------------------------------------------------ #
# ----- End of createStorageGroup function ------------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ----- Start of requestStorageGroupFulfillment function ----------- #
# ------------------------------------------------------------------ #
def requestStorageGroupFulfillment(hmc, sgID, sgReqTempl):
    try:
        # prepare HTTP body as JSON
        httpBody = json.dumps(sgReqTempl)
        # create workload
        resp = getHMCObject(hmc,
                            WSA_URI_REQUEST_STORAGE_GROUP_FULFILLMENT % sgID,
                            "Request Storage Group Fulfillment",
                            httpMethod = WSA_COMMAND_POST,
                            httpBody = httpBody,
                            httpGoodStatus = 204,           # HTTP created
                            httpBadStatuses = [400, 403, 404, 409, 503])
        return assertValue(pyObj=resp, key='object-uri')
    except HMCException as exc:   # raise HMCException
        print "[HMCEXCEPTION requestStorageGroupFulfillment]", exc.message
        if exc.httpResponse != None:
            print "[HMCEXCEPTION requestStorageGroupFulfillment]", eval(exc.httpResponse)['message']
        raise exc
    except Exception as exc:
        print "[EXCEPTION requestStorageGroupFulfillment]", exc
        raise exc

# ------------------------------------------------------------------ #
# ----- End of requestStorageGroupFulfillment function ------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of getStorVolListOfSG function ------------------- #
# ------------------------------------------------------------------ #
def getStorVolListOfSG(hmcConn=None,
                       sgURI=None):
    log.debug("Entered")
    try:
        if sgURI != None:
            URI = "%s/storage-volumes"%sgURI
        else:
            exc = HMCException("getStorVolListOfSG",
                               "You should specify sgURI param")
            raise Exception
        # Get storage volume list of a storage group
        return getHMCObject(hmcConn,
                            URI,
                            "Get storage volume list of one storage group")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getStorVolListOfSG")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ----------- End of getStorVolListOfSG function ------------------- #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# --------- Start of getStorVolProperties function ----------------- #
# ------------------------------------------------------------------ #
def getStorVolProperties(hmcConn=None,
                         storVolURI=None):
    log.debug("Entered")
    try:
        if storVolURI != None:
            URI = storVolURI
        else:
             exc = HMCException("getStorVolProperties",
                               "You should specify storVolURI parameter")
             raise exc
        # get storage volume properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get Storage-Volume Properties")
    except HMCException as exc:   # raise HMCException
        exc.setMethod("getStorVolProperties")
        raise exc
    finally:
        log.debug("Completed")
# ------------------------------------------------------------------ #
# ------------End of getStorVolProperties function ----------------- #
# ------------------------------------------------------------------ #

def getStorageControlUnitProperties(hmcConn=None,
                                    StorctrlUnitUri=None):
    log.debug("Entered")
    try:
        if StorctrlUnitUri != None:
            URI = StorctrlUnitUri
        else:
            exc = HMCException("getStorageControlUnitProperties",
                               "You should specify StorctrlUnitUri parameter")
            raise exc
        # Get Storage Control Unit Properties
        return getHMCObject(hmcConn,
                            URI,
                            "Get Storage Control Unit Properties")
    except HMCException as exc:
        exc.setMethod("getStorageControlUnitProperties")
        raise exc
    finally:
        log.debug("Completed")
