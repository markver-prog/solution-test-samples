#! /usr/bin/env python

# ------------------------------------------------------------------ #
# - This file contains HMC classes to be used by another HMC API scripts
# - Classes:
#        HMCConnection - object to invoke HMC API web services
#        HMCException  - special exception object
#        CompareResult - result of Python objects comparing
# ------------------------------------------------------------------ #
# @author: Alexander P. Chepkasov, RSTL, Jan 2012,
# Changed by Daniel.Wu to apply prsm2 change.
# ------------------------------------------------------------------ #


# imports
from wsaconst import *
import prsm2api
import logging
import httplib
import os
import time
import ssl
import socket
import traceback


# ------------------------------------------------------------------ #
# --------------- HMCConnection object ----------------------------- #
# ------------------------------------------------------------------ #
# - Encaplsulates connection to HMC API web services
# - performs logon/logoff/make request/etc operations with HMC API
# ------------------------------------------------------------------ #
class HMCConnection:
    '''
      - This class encaplsulates HTTP connection to HMC API web services
      - performs logon/logoff/make request/etc operations with HMC API
    '''

    hmcAPIHost = None   # host name/IP address of HMC
#  hmcAPIPort = 6794   # HMC API web services TCP port to connect
    httpTimeout = 60    # HTTP timeout
    maxAttempts = 5     # default max attempts number to perform HTTP request
    logonAttempts = 1   # number of attempts to do HMC logon
    useHttps = True     # use HTTPS to connect to HMC
    hmcConn = None      # httplib.HTTPConnection (or HTTPSConnection) object
    hmcprops = None     # python object, which contain authenticate data

# API session ID and jms notification topic
    sessionID = None
    notificationTopic = None
# API minor and major versions
    apiMinorVer = None
    apiMajorVer = None

# user ID/password (None by default)
    userID = None
    userPassword = None

    configFile = 'hmcapi.properties'

# logger object
    log = logging.getLogger(HMC_API_LOGGER)

    # -------------------------------------------- #
    # - Constructor
    # -------------------------------------------- #
    def __init__(self,
                 hmcHost,               # host name/IP address of HMC
                 hmcPort=WSA_PORT_SSL,  # HMC API web services TCP port to connect
                 timeout=httpTimeout,   # HTTP timeout
                 useSSL=useHttps        # use HTTPS to connect to HMC
                 ):
        '''
          - Constructor

          - @param hmcHost:   # host name/IP address of HMC
          - @param hmcPort:   # HMC API web services TCP port to connect
          - @param timeout:   # HTTP timeout
          - @param useSSL:    # use HTTPS to connect to HMC
        '''
        self.log.debug("Entered")
        self.hmcAPIHost = hmcHost
        self.hmcAPIPort = hmcPort
        self.httpTimeout = timeout
        self.useHttps = useSSL
    # try to load configuration data from .properties file..
        try:
            self.hmcprops = self.loadProperties(configFile=self.configFile)
        except IOError as exc:
            pass
            # will use default userid/password
            # (look at WSA_DEFAULT_USERID/WSA_DEFAULT_PASSWORD in wsaconst.py)
            #self.log.warning("Cannot load configuration file [%s]: %s. Will use default userid/password.",
            #                 self.configFile, exc)
# ?    self.credentials = base64.encodestring("%s:%s"%(self.hmcprops["userid"], self.hmcprops["password"]))
        self.log.debug("Completed")

    # -------------------------------------------- #
    # - Loads authenticate data from .properties file
    # -------------------------------------------- #
    def loadProperties(self,
                       configFile   # .properties file name
                       ):
        '''
          - Loads authenticate data from .properties file

          - @param configFile: .properties file name
        '''
        self.log.debug("Entered")
        propFilePath = os.path.dirname(os.path.abspath(__file__)) + '/' + configFile
        propFile = open(propFilePath)
        propLines = propFile.readlines()
        hmcprops = {}
        for line in propLines:
            if not line.startswith("#") and not line.isspace() and line.count("=") == 1:
                name, value = line.split("=")
                hmcprops[name.strip()] = value.strip()
        self.log.debug("Completed")
        return hmcprops

    # -------------------------------------------- #
    # - Prints class' members
    # -------------------------------------------- #
    def printInfo(self):
        '''
          -  Prints class' members
        '''
        self.log.debug("Entered")
        self.log.info("Connection settings:")
        self.log.info("\tAPI Host: %s", self.hmcAPIHost)
        self.log.info("\tAPI Port: %s", self.hmcAPIPort)
        self.log.info("\tHTTP timeout: %s", self.httpTimeout)
        self.log.debug("Completed")

    # -------------------------------------------- #
    # - Queries HMC API version
    # -------------------------------------------- #
    def getAPIVersion(self,
                      headers={"Content-type": "application/json", "Accept": "*/*"}
                      ):
        '''
          - Queries HMC API version
          - @param headers: default headers for JSON
        '''
        self.log.debug("Entered")
        response = None
        try:
            response = self.makeRequest(path=WSA_URI_VERSION, headers=headers, authenticateRequired=False)
        # check HTTP response
            prsm2api.assertHttpResponse(response, "HMCConnection.getAPIVersion",
                                        "Query API Version",
                                        badStatuses=[500])
        # extract version number
            respBody = response.read()
            self.apiMajorVer = prsm2api.assertValue(jsonObj=respBody, key='api-major-version')
            self.apiMinorVer = prsm2api.assertValue(jsonObj=respBody, key='api-minor-version')
            self.log.info("Query API Version response: version=%s.%s",
                          self.apiMajorVer, self.apiMinorVer)
        except HMCException as exc:   # raise HMCException
            exc.setMethod("HMCConnection.getAPIVersion")
            if response != None:
                exc.setHTTPResponse(response)
            raise exc
        except Exception as exc:
            exc = HMCException("HMCConnection.getAPIVersion",
                               "Got an exception while doing Query API Version",
                               origException=exc)
            if response != None:
                exc.setHTTPResponse(response)
            raise exc
        finally:
            self.log.debug("Completed")

    # -------------------------------------------- #
    # - Sets user authentication data
    # -------------------------------------------- #
    def setUserCredential(self,
                          userid,
                          password
                          ):
        '''
          - Sets user authentication data
          @param userid: user ID to be used for HMC APIs authentication
          @param password: user password to be used for HMC APIs authentication
        '''
        self.userID = userid
        self.userPassword = password

    # -------------------------------------------- #
    # - Perform HMC API authentication
    # -------------------------------------------- #
    def authenticateHMC(self,
                        headers={"Content-type": "application/json", "Accept": "*/*"}
                        ):
        '''
          - Performs HMC API authentication
          - @param headers: default headers for JSON
        '''
        self.log.debug("Entered")
        response = None
        try:
            # ensure user id and password have been defined
            if self.userID == None:
                userid = prsm2api.assertValue(pyObj=self.hmcprops,
                                              key=WSA_USERID,
                                              listIndex=0,
                                              optionalKey=True)
                userid = prsm2api.checkValue(WSA_USERID, userid,
                                             WSA_DEFAULT_USERID)
            else:
                userid = self.userID
            if self.userPassword == None:
                password = prsm2api.assertValue(pyObj=self.hmcprops,
                                                key=WSA_PASSWORD,
                                                listIndex=0,
                                                optionalKey=True)
                password = prsm2api.checkValue(WSA_PASSWORD, password,
                                               WSA_DEFAULT_PASSWORD)
            else:
                password = self.userPassword
        # prepare HTTP body - the JSON object with authentication data
            body = '{"userid":"%s", "password":"%s"}' % (userid, password)
            response = self.makeRequest(method=WSA_COMMAND_POST,
                                        path=WSA_URI_LOGON,
                                        body=body, headers=headers,
                                        logonRequired=False,
                                        attempts=self.logonAttempts)
        # check HTTP response
            prsm2api.assertHttpResponse(response, "HMCConnection.authenticateHMC",
                                        "HMC Logon",
                                        badStatuses=[400, 403])
            respBody = response.read()
            self.log.debug("response=%s", respBody)
            self.sessionID = prsm2api.assertValue(jsonObj=respBody, key='api-session')
            self.notificationTopic = prsm2api.assertValue(jsonObj=respBody, key='notification-topic')
            self.apiMajorVer = prsm2api.assertValue(jsonObj=respBody, key='api-major-version')
            self.apiMinorVer = prsm2api.assertValue(jsonObj=respBody, key='api-minor-version')
        # print HMC API session info
            self.log.debug("Logged to HMC with parameters:")
            self.log.debug("\tapi-session=%s", self.sessionID)
            self.log.debug("\tnotification-topic=%s", self.notificationTopic)
            self.log.debug("\tapi-major-version=%s", self.apiMajorVer)
            self.log.debug("\tapi-minor-version=%s", self.apiMinorVer)
        except HMCException as exc:   # raise HMCException
            exc.setMethod("HMCConnection.authenticateHMC")
#      if response != None:
#        exc.setHTTPResponse(response)
            raise exc
        except Exception as exc:
            exc = HMCException("HMCConnection.authenticateHMC",
                               "Got an exception while doing HMC logon",
                               origException=exc)
            if response != None:
                exc.setHTTPResponse(response)
            raise exc
        finally:
            self.log.debug("Completed")

    # -------------------------------------------- #
    # - Performs HMC logon
    # -------------------------------------------- #
    def logon(self,
              authenticateRequired=True
              ):
        '''
          - Performs HMC logon
        '''
        self.log.debug("Entered")
        try:
            # create HTTP connection object
            if self.useHttps == True:
                self.log.debug("Establishing HTTPS connection to HMC %s...", self.hmcAPIHost)
                self.hmcConn = httplib.HTTPSConnection(self.hmcAPIHost,
                                                       self.hmcAPIPort,
                                                       context=ssl._create_unverified_context())  # , timeout=self.httpTimeout)
            else:
                self.log.debug("Establishing HTTP connection to HMC...")
                self.hmcConn = httplib.HTTPConnection(self.hmcAPIHost,
                                                      self.hmcAPIPort)  # , timeout=self.httpTimeout)

        # check HMC API version
            try:
                checkApiVer = (CHECK_API_VERSION == True)
            except NameError as exc:
                checkApiVer = False
            if checkApiVer:
                self.getAPIVersion()
        # do HMC logon
            if authenticateRequired:
                self.authenticateHMC()
        except HMCException as exc:
            exc.setMethod("HMCConnection.logon")
            raise exc
        finally:
            self.log.debug("Completed")

    # -------------------------------------------- #
    # - Returns True of False if connection established or not
    # -------------------------------------------- #
    def isLoggedOn(self):
        '''
          - Checks if connection established (session-id != None)
          - @return: True of False if connection established or not
        '''
        return (self.sessionID != None)

    # -------------------------------------------- #
    # - Closes HMC API connection
    # -------------------------------------------- #
    def logoff(self,
               headers={"Content-type": "application/json", "Accept": "*/*"}
               ):
        '''
          - Closes HMC API connection
          - @param headers: default headers for JSON
        '''
        self.log.debug("Entered")
        try:
            if self.hmcConn != None:
                # do logoff
                if self.sessionID != None:
                    headers["X-API-Session"] = self.sessionID
                    response = self.makeRequest(method=WSA_COMMAND_DELETE,
                                                path=WSA_URI_LOGOFF,
                                                headers=headers,
                                                logonRequired=False,
                                                attempts=1)
                # check HTTP response
                    prsm2api.assertHttpResponse(response, "HMCConnection.logoff",
                                                "HMC Logoff",
                                                goodHttpStatus=204,
                                                badStatuses=[400])
                self.hmcConn.close()
        except HMCException as exc:
            origExc = exc.origException
        # do nothing in the case of HTTP exception
            if not issubclass(type(origExc), httplib.HTTPException):
                exc.printError()
                raise exc
        finally:
            # clear session data
            self.sessionID = None
            self.notificationTopic = None
            self.log.debug("Completed")

    # -------------------------------------------- #
    # - Performs HTTP request to HMC
    # -------------------------------------------- #
    def makeRequest(self,
                    path=None,
                    method=WSA_COMMAND_GET,
                    body=None,
                    headers={"Content-type": "application/json", "Accept": "*/*"},
                    logonRequired=True,       # HMC API request requires HTTP session to be established
                    attempts=maxAttempts,
                    authenticateRequired=True
                    ):
        '''
          - Performs HTTP request to HMC

          - @param path:           HTTP request URL
          - @param method:         HTTP method
          - @param body:           HTTP request body
          - @param headers:        HTTP request headers
          - @param logonRequired:  HMC API request requires HTTP session to be established?
          - @param attempts:       number of attempts to retry HTTP request
        '''
        self.log.debug("Entered")
        try:
            if logonRequired:
                # establish HMC connection
                if not self.isLoggedOn():
                    self.logon(authenticateRequired)
            # setup session ID into HTTP header
                if self.isLoggedOn():
                    headers["X-API-Session"] = self.sessionID
            reqbody = None
            if body != None:
                reqbody = body + "  "

            self.log.debug("REST call being made:")
            self.log.debug("\tHost: %s", self.hmcAPIHost)
            self.log.debug("\tPort: %s", self.hmcAPIPort)
            self.log.debug("\tTimeout: %s", self.httpTimeout)
            self.log.debug("\tMethod: %s", method)
            self.log.debug("\tURI: %s", path)
            self.log.debug("\tHeaders: %s", headers)
            if reqbody != None:
                self.log.debug("\tBody: %s", reqbody)

        # do several attempts to send a request
            while True:
                try:
                    response = None
                    self.hmcConn.request(method, path, reqbody, headers)
                    response = self.hmcConn.getresponse()
                    break
            # do re-login in the case of any HTTP or SSLError Exception
                except (httplib.HTTPException, ssl.SSLError) as exc:
                    attempts -= 1
                    if attempts > 0:
                        self.log.debug("%s %s (attempts left: %d); %s",
                                       "%s occurred." % (type(exc)),
                                       "Trying to establish new HMC session",
                                       attempts, exc)
                    # try to re-login
                        self.logoff()
                        self.logon()
                        headers["X-API-Session"] = self.sessionID
                        continue
                    exc = HMCException("HMCConnection.makeRequest",
                                       "Got %s exception while doing makeRequest" % (type(exc)),
                                       origException=exc)
                    request = HTTPRequest(hmcHost=self.hmcAPIHost,
                                          hmcPort=self.hmcAPIPort,
                                          httpMethod=method, httpPath=path,
                                          httpBody=reqbody)
                    exc.setHTTPRequest(request)
                    if response != None:
                        exc.setHTTPResponse(response)
                    raise exc
            # catch socket-related errors
                except Exception as exc:
                    if issubclass(type(exc), socket.error):
                        msg = "Got %s exception while doing makeRequest. Please, check host name/ip address[%s] and TCP port[%s]." % (type(exc),
                                                                                                                                      self.hmcAPIHost,
                                                                                                                                      self.hmcAPIPort)
                    else:
                        msg = "Got an exception while doing makeRequest"
                    exc = HMCException("HMCConnection.makeRequest",
                                       msg,
                                       origException=exc)
                    if response != None:
                        exc.setHTTPResponse(response)
                    request = HTTPRequest(hmcHost=self.hmcAPIHost,
                                          hmcPort=self.hmcAPIPort,
                                          httpMethod=method, httpPath=path,
                                          httpBody=reqbody)
                    exc.setHTTPRequest(request)
                    raise exc
        finally:
            self.log.debug("Completed")
        return response


# ------------------------------------------------------------------ #
# --------------- HMCException object ------------------------------ #
# ------------------------------------------------------------------ #
# - Special Exception object for HMC API scripts
# ------------------------------------------------------------------ #
class HMCException(Exception):
    '''
      - Special Exception object for HMC API scripts
    '''
# logger object
    log = logging.getLogger(HMC_API_LOGGER)
# return code (if used in scripts)
    RC = 0

    # -------------------------------------------- #
    # - Constructor
    # -------------------------------------------- #
    def __init__(self,
                 script,              # script (method) name
                 errorMessage,        # error message
                 origException=None,  # original exception, which caused this HMCException
                 httpResponse=None,   # wrong HTTP response, which caused this HMCException
                 httpRequest=None,    # HTTP request, which caused this HMCException
                 methodName=None      # method name (methods path)
                 ):
        '''
          - Constructor

          - @param script:         script (method) name
          - @param errorMessage:   error message
          - @param origException:  original exception, which caused this HMCException
          - @param httpResponse:   wrong HTTP response, which caused this HMCException
          - @param httpRequest:    HTTP request, which caused this HMCException
          - @param methodName:     method name (methods path)
        '''
        self.log.debug("Entered")
        self.script = script
        self.method = methodName
        self.message = errorMessage
        self.origException = origException
        self.httpResponse = httpResponse
        self.httpRequest = httpRequest
        self.excTime = time.localtime()  # gmtime()#time()  # time of the exception
        self.stack = traceback.format_tb(sys.exc_info()[2])
        self.log.debug("Completed")

    # -------------------------------------------- #
    # - Prints HMCException details to logger
    # -------------------------------------------- #
    def printError(self):
        '''
          - Prints HMCException details to logger
        '''
        self.log.debug("Entered")
        self.log.error("HMCException happened at %s in %s module",
                       time.strftime("%H:%M:%S", self.excTime),
                       self.script)
        if self.method != None:
            self.log.error("\tMethod(s): %s", self.method)
        self.log.error("\tCause:     %s", self.message)
        if self.origException != None:
            self.log.error("\tOriginal Exception: %s", self.origException)
        if self.httpRequest != None:
            self.httpRequest.printHTTPRequest()
        if self.httpResponse != None:
            # parse JSON object received from HMC
            try:
                status = prsm2api.assertValue(jsonObj=self.httpResponse,
                                              key='http-status')
                reason = prsm2api.assertValue(jsonObj=self.httpResponse,
                                              key='reason')
                request = prsm2api.assertValue(jsonObj=self.httpResponse,
                                               key='request-uri')
                msg = prsm2api.assertValue(jsonObj=self.httpResponse, key='message')
                stack = prsm2api.assertValue(jsonObj=self.httpResponse,
                                             key='stack', optionalKey=True)
                errDetails = prsm2api.assertValue(jsonObj=self.httpResponse,
                                                  key='error-details', optionalKey=True)
                self.log.error("\tHTTP Response:")
                self.log.error("\t\tHTTP Status:   %s.%s", status, reason)
                self.log.error("\t\tRequest URI:   %s", request)
                self.log.error("\t\tMessage:       %s", msg)
                if stack != None:
                    self.log.error("\t\tStack Info:     %s", stack)
                if errDetails != None:
                    self.log.error("\t\tError Details: %s", errDetails)
            except HMCException:
                self.log.error("\tHTTP Response:")
                self.log.error("\t\tstatus=%s; reason=%s; %s",
                               self.httpResponse.status,
                               self.httpResponse.reason,
                               self.httpResponse.msg)
        if self.RC != None:
            self.log.error("\tRC: %s" % (self.RC))
        self.log.error("\tTraceback: %s", self.stack)
        self.log.debug("Completed")

    # -------------------------------------------- #
    # - Returns status.reason string
    # -------------------------------------------- #
    def getHTTPError(self):
        '''
          - Returns status.reason string
          - @return: status.reason string
        '''
        RC = ""
        if self.httpResponse != None:
            # parse JSON object received from HMC
            try:
                status = prsm2api.assertValue(jsonObj=self.httpResponse,
                                              key='http-status')
                reason = prsm2api.assertValue(jsonObj=self.httpResponse,
                                              key='reason')
                RC = "%s.%s" % (status, reason)
            except HMCException:
                self.log.error("\tHTTP Response:")
                self.log.error("\t\tstatus=%s; reason=%s; %s".
                               self.httpResponse.status,
                               self.httpResponse.reason,
                               self.httpResponse.msg)
                RC = "%s.%s" % (self.httpResponse.status, self.httpResponse.reason)
        return RC

    # -------------------------------------------- #
    # - Sets(appends) method to methods path
    # -------------------------------------------- #
    def setMethod(self,
                  methodName    # method name to be added to methods path
                  ):
        '''
          - Sets(appends) method to methods path
          - @param methodName: method name to be added to methods path
        '''
        if self.method != None:
            self.method = "%s -> %s" % (methodName, self.method)
        else:
            self.method = methodName

    # -------------------------------------------- #
    # - Sets return code (RC) for this exception
    # -------------------------------------------- #
    def setRC(self,
              RC      # return code; integer
              ):
        '''
          - Sets return code (RC) for this exception
          - @param RC: return code; integer
        '''
        self.RC = RC

    # -------------------------------------------- #
    # - Sets latest HTTP response of this exception
    # -------------------------------------------- #
    def setHTTPResponse(self,
                        httpResponse  # HTTPResponse object
                        ):
        '''
          - Sets latest HTTP response of this exception
          - @param httpResponse: HTTPResponse object
        '''
        self.httpResponse = httpResponse

    # -------------------------------------------- #
    # - Sets HTTP request, which caused this exception
    # -------------------------------------------- #
    def setHTTPRequest(self,
                       httpRequest
                       ):
        '''
          - Sets HTTP request, which caused this exception
          - @param httpRequest:  HTTPRequest object
        '''
        self.httpRequest = httpRequest

    # -------------------------------------------- #
    # - Returns HTTPResponse.status code of this exception
    # -------------------------------------------- #
    def getHTTPStatus(self):
        '''
          - Returns HTTPResponse.status code if httpResponse != None
          - and httplib.OK otherwise
        '''
        if self.httpResponse != None:
            return self.httpResponse.status
        return httplib.OK


# ------------------------------------------------------------------ #
# --------------- HTTPRequest object ------------------------------- #
# ------------------------------------------------------------------ #
# - Object to encapsulate HTTP request
# ------------------------------------------------------------------ #
class HTTPRequest:
    '''
      - Object to encapsulate HTTP request
    '''
# logger object
    log = logging.getLogger(HMC_API_LOGGER)

    # -------------------------------------------- #
    # - Constructor
    # -------------------------------------------- #
    def __init__(self,
                 hmcHost,           # HMC host
                 hmcPort,           # HMC port
                 httpMethod,        # HTTP method(GET/POST/CREATE/DELETE)
                 httpPath,          # HTTP path
                 httpBody=None,     # HTTP request body
                 httpHeaders=None,  # HTTP request headers
                 ):
        '''
          - Constructor

          - @param httpMethod:  HTTP method(GET/POST/CREATE/DELETE)
          - @param httpPath:    HTTP path
          - @param httpBody:    HTTP request body
          - @param httpHeaders: HTTP request headers
        '''
        self.log.debug("Entered")
        self.hmcHost = hmcHost
        self.hmcPort = hmcPort
        self.httpMethod = httpMethod
        self.httpPath = httpPath
        self.httpBody = httpBody
        self.httpHeaders = httpHeaders
        self.log.debug("Completed")

    # -------------------------------------------- #
    # - Prints HTTPRequest details to logger
    # -------------------------------------------- #
    def printHTTPRequest(self):
        self.log.error("\tHTTP Request:")
        self.log.error("\t\tHMC Host:      %s", self.hmcHost)
        self.log.error("\t\tHMC Port:      %s", self.hmcPort)
        self.log.error("\t\tHTTP Method:   %s", self.httpMethod)
        self.log.error("\t\tRequest URI:   %s", self.httpPath)
        if self.httpBody != None:
            self.log.error("\t\tBody:        %s", self.httpBody)
        if self.httpHeaders != None:
            self.log.error("\t\tHeaders:     %s", self.httpHeaders)


# ------------------------------------------------------------------ #
# --------------- CompareResult object ------------------------------ #
# ------------------------------------------------------------------ #
# - Object to encaplsulate the result of Python objects comparing
# ------------------------------------------------------------------ #
class CompareResult:
    '''
      - Object to encaplsulate the result of Python objects comparing
    '''
    # -------------------------------------------- #
    # - Constructor
    # -------------------------------------------- #

    def __init__(self,
                 status,            # status of last operation; boolean
                 message=None,      # error message if last operation failed
                 traceMessage=None,  # trace message to further debug
                 key=None           # dictionary key on which last operation failed
                 ):
        '''
          - Constructor

          - @param status:        status of last operation; boolean
          - @param message:       error message if last operation failed
          - @param traceMessage:  trace message to further debug
          - @param key:           dictionary key on which last operation failed
        '''
        self.status = status
        self.message = None
        self.failurePoint = None
        self.keyPath = []
        self.traceMessageList = []
        if message != None:
            self.message = message
        if traceMessage != None:
            self.traceMessageList.insert(0, traceMessage)
        if key != None:
            self.keyPath.insert(0, key)

    # -------------------------------------------- #
    # - Adds dictionary key to keyPath to determine
    # - failure point
    # -------------------------------------------- #
    def addKey(self,
               key=None   # key to be added to keyPath
               ):
        '''
          - Adds dictionary key to keyPath to determine failure point
          - @param key: key to be added to keyPath
        '''
        if key != None:
            self.keyPath.insert(0, key)

    # -------------------------------------------- #
    # - Adds trace message to traceMessageList
    # -------------------------------------------- #
    def addTrace(self,
                 traceMessage  # trace message to be added to traceMessageList
                 ):
        '''
          - Adds trace message to traceMessageList
          - @param traceMessage: trace message to be added to traceMessageList
        '''
        if traceMessage != None:
            self.traceMessageList.insert(0, traceMessage)

    # -------------------------------------------- #
    # - Returns status of comparing
    # -------------------------------------------- #
    def getStatus(self):
        '''
          - Returns status of comparing
          - @return: the status of comparing
        '''
        return self.status

    # -------------------------------------------- #
    # - Returns keyPath to determine failure point
    # -------------------------------------------- #
    def getKeyPath(self):
        '''
          - Returns keyPath to determine failure point
          - @return: keyPath as a string
        '''
        if len(self.keyPath) == 0:
            return None
        msg = None
        for key in self.keyPath:
            if msg != None:
                msg = "%s->%s" % (msg, key)
            else:
                msg = "[%s" % (key)
        return "%s]" % (msg)

    # -------------------------------------------- #
    # - Sets error message
    # -------------------------------------------- #
    def setMessage(self,
                   message  # error message
                   ):
        '''
          - Sets error message
          - @param message: error message
        '''
        if message != None:
            self.message = message

    # -------------------------------------------- #
    # - Returns error message
    # -------------------------------------------- #
    def getMessage(self):
        '''
          - Returns error message
          - @return: error message
        '''
        return self.message

    # -------------------------------------------- #
    # - Sets failure point
    # -------------------------------------------- #
    def setFailurePoint(self,
                        failurePoint=None  # failure point (as a string)
                        ):
        '''
          - Sets failure point
          - @param failurePoint: failure point (as a string)
        '''
        if failurePoint != None:
            self.failurePoint = failurePoint

    # -------------------------------------------- #
    # - Returns failure point
    # -------------------------------------------- #
    def getFailurePoint(self):
        '''
          - Returns failure point
          - @return: failure point (as a string)
        '''
        return self.failurePoint

    # -------------------------------------------- #
    # - Prints trace messages (in debug trace mode)
    # -------------------------------------------- #
    def printTrace(self,
                   log    # logger to print trace messages
                   ):
        '''
          - Prints trace messages (in debug trace mode)
          - @param log: logger to print trace messages
        '''
        if log != None:
            for traceMsg in self.traceMessageList:
                log.debug("\t%s", traceMsg)
