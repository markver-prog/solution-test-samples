#! /usr/bin/env python
""" This python script exercises various aspects of the IBM Cloud 
Hyper Protect Crypto Services (HPCS) Key Protect service through its REST API.

Here is the format of the input file (-f option), with example input shown. 
This example passes in a null service_host, which tells the script 
to dynamically retrieve the connection info (this does not work for
standard Key Protect, it is a unique function for HPCS Key Protect):
{
    "service_host": "",
    "service_instance_id": "fb5af3ea-e10b-42e9-a1e5-c97404e96feb",
    "root_key_name":"SolutionTestRootKey"
}

This example passes in a specific service_host for HPCS Key Protect
(this is normally not needed, the null string example above is
all that is needed for HPCS Key Protect instances):
{
    "service_host": "us-south.hpcs.cloud.ibm.com:11399",
    "service_instance_id": "fb5af3ea-e10b-42e9-a1e5-b97404e96feb",
    "root_key_name":"SolutionTestRootKey"
}

This example passes in a service_host for standard Key Protect:
{
    "service_host": "keyprotect.us-south.bluemix.net",
    "service_instance_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "root_key_name":"SampleRootKey"
}

Here is the format of the input Key Protect API key file (-a option), which
is the same format as provided by the Key Protect service:
{
        "name": "SampleAPIKey",
        "description": "A sample for test purposes",
        "createdAt": "2018-03-21T17:15+0000",
        "apikey": "xxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}


Developed and tested on Linux on System z using python 2.7.12.
"""
from __future__ import print_function
import sys, optparse, time, httplib, urllib, json, socket
import os, string, time, base64, copy
import uuid
from Crypto.Cipher import AES

# ##########################################################################
# get_access_token function
# ##########################################################################
def get_access_token(api_key):
    '''Contact Cloud Identity and Access Management to get an access token.

       Input is an api key for the user's Key Protect service.
    '''

    headers = {"Content-type":"application/x-www-form-urlencoded",
               "Accept":"application/json"}
    params = "grant_type=urn%3Aibm%3Aparams%3Aoauth%3Agrant-type%3Aapikey&apikey=" + api_key

    conn = httplib.HTTPSConnection('iam.bluemix.net')
    try:
        conn.request("POST", "/oidc/token", params, headers)
        response = conn.getresponse()
    except socket.error as errno:
        print("Error attempting to connect to Cloud Identity and Access Management to get access token")
        print(errno)
        sys.exit()

    if response.status == 200:
        if not quiet:
            print(">>> Acquired access token at", time.strftime("%m/%d/%Y %H:%M:%S"))
    else:
        print("Failed to aquire access token. Ensure API key passed in via input file is correct")
        print("status", response.status, "reason", response.reason)
        sys.exit()

    #get the json object and convert to a python object
    objs = json.loads(response.read())
    access_token = objs['access_token']
    expiration   = objs['expiration']

    if extraverbose:
       print("Access token:", access_token)
    if verbose:
       print("Token expires:", time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(expiration)))

    conn.close()

    return access_token

# ##########################################################################
# get_api_endpoint_url function
# ##########################################################################
def get_api_endpoint_uri(instance_id, access_token):
    '''Contact zcryptobroker to get the Key Protect API endpoint URI (url:port).

       Input is an instance ID for our crypto instance,
       an access token for the user's Key Protect service, and
       the uri of the zcryptobroker to connect to.
    '''
    broker   = 'zcryptobroker.mybluemix.net'

    headers = {
              "authorization":"Bearer " + access_token,
    }

    need_new_token = False
    conn = httplib.HTTPSConnection(broker)
    try:
        conn.request("GET", "/crypto_v1/instances/" + instance_id, "", headers)
        response = conn.getresponse()
    except socket.error as errno:
        print ("Socket error attempting to connect to zcryptobroker service to get API endpoint URI")
        print (errno)
        sys.exit()
    except:
        print ("Unexpected error attempting to connect to zcryptobroker service to get API endpoint URI")
        raise

    if response.status == 200:
        if not quiet:
            print ("Retrieved API endpoint URI", time.strftime("%m/%d/%Y %H:%M:%S"))
        # get the json object and convert to a python object
        objs = json.loads(response.read())
        # now get the connection info...
        if 'apiConnectionInfo' in objs:
            api_endpoint_uri  = objs['apiConnectionInfo'] # get the uri
    else:
        try:
           objs = json.loads(response.read())
           error_msg = objs['resources']
        except ValueError, e:
           error_msg = {}
           error_msg[0] = {}
           error_msg[0]['errorMsg'] = 'No error message text returned'

        if ((response.status == 401) and
            (error_msg[0]['errorMsg'] == 'Unauthorized: Token is expired')):
            need_new_token = True
            key_id = ""
            if not quiet:
                print ("get_api_endpoint_uri: Redrive loop, must get a new access token, the old one is expired...")
        else:
            print ("Failed to get API endpoint URI")
            print ("Status:", response.status, "reason:", response.reason)
            print ("Key Protect instance ID:", instance_id)
            print ("Error Message:", error_msg[0]['errorMsg'])
            sys.exit()

    conn.close()
    return api_endpoint_uri, need_new_token


# ##########################################################################
# get_key_list function
# ##########################################################################
def get_key_list(correlation_id, host, instance_id, access_token):
    '''Contact Key Protect to get a list of the root keys it owns.

       Input is the target Key Protect host, an instance ID for the
       Key Protect service, an access token, and a correlation ID.

       Outputs a list of root keys owned by this KP instance, or
       a boolean indicating a new access token is needed. 
    '''
    headers = {
              "accept":"application/vnd.ibm.collection+json",
              "authorization":"Bearer " + access_token,
              "bluemix-instance":instance_id,
              "correlation-id":correlation_id # used for debug
    }

    need_new_token = False
    key_list = {}

    conn = httplib.HTTPSConnection(host)
    try:
        conn.request("GET", "/api/v2/keys", "", headers)
        response = conn.getresponse()
    except socket.error as errno:
        print("Socket error attempting to connect to Key Protect service to get list of keys")
        print(errno)
        sys.exit()
    except:
        print("Unexpected error attempting to connect to Key Protect service to get list of keys")
        raise

    if response.status == 200:
        if not quiet:
            print("Retrieved list of stored keys", time.strftime("%m/%d/%Y %H:%M:%S"))
        #get the json object and convert to a python object
        objs = json.loads(response.read())
        if 'resources' in objs:
            key_list = objs['resources']
    else:
        try:
           objs = json.loads(response.read())
           error_msg = objs['resources']
        except ValueError, e:
           error_msg = {}
           error_msg[0] = {}
           error_msg[0]['errorMsg'] = 'No error message text returned'

        if ((response.status == 400) and
            (error_msg[0]['errorMsg'] == 'Bad Request: Token is expired')):
            need_new_token = True
            key_id = ""
            if not quiet:
                print("get_key_list: Redrive loop, must get a new access token, the old one is expired...")
        else:
            print("Failed to get list of root keys")
            print("Status:", response.status, "reason:", response.reason)
            print("Correlation id=", headers['correlation-id'])
            print("Key Protect instance ID:", instance_id)
            print("Error Message:", error_msg[0]['errorMsg'])
            sys.exit()

    conn.close()
    return key_list, need_new_token


# ##########################################################################
# get_key_id function
# ##########################################################################
def get_key_id(correlation_id, host, instance_id, access_token, key_name):
    '''Get the id corresponding to a key name.

       Input is the target Key Protect host, an instance ID for the
       Key Protect service, an access token, and the name of the key 
       for which we want to retrieve an ID. Also a correlation ID.

       Output is the ID associated with the requested key.
    '''
    headers = {
              "accept":"application/vnd.ibm.collection+json", 
              "authorization":"Bearer " + access_token, 
              "bluemix-instance":instance_id,
              "correlation-id":correlation_id # used for debug
    }

    need_new_token = False
    key_id = "NOT FOUND"

    # get list of root keys owned by this KP instance...
    key_list, need_new_token = get_key_list(correlation_id, 
                                            host, 
                                            instance_id, 
                                            access_token)

    # search for the desired root key from the returned list of keys
    # and save it's ID
    if not need_new_token:
       for k in key_list:
          if k['name'] == key_name:
             key_id = k['id']
             if not quiet:
                print("Found desired key in list of stored keys")

                if verbose:
                   print("List of stored keys found:")
                   for k in key_list:
                      print("   Key name:", k['name'], "with ID:", k['id'])

       if key_id == "NOT FOUND" and not quiet:
          print("Desired key", key_name, "not found in list of stored keys")
            
    return key_id, need_new_token

# ##########################################################################
# Function to create a standard or root key 
# ##########################################################################
def create_key(correlation_id, host, instance_id, access_token, key_alias, extractable=False):
    '''Contact Key Protect to create a standard or root key.

       Input is the target Key Protect host, an instance ID for the 
       Key Protect service, an access token, a unique, human-readable 
       key name (alias), and a boolean variable indicating whether the key
       to be created is extractable or not. Extractable=True means 
       we are creating a standard key that can be retrieved and used to 
       encrypt/decrypt data; extractable=False, the default,  means we 
       are creating a root key that will never leave the HSM, and can only 
       be used to encrypt/decrypt other keys.

       Output is the ID of the newly-created key, or a boolean indicating
       that a new access token is needed.
    '''
    if extractable:
       description = 'KeyProtectSample.py standard key'
    else:
       description = 'KeyProtectSample.py root key -- generated'

    headers = {
              "content_type":"application/vnd.ibm.kms.key+json",
              "authorization":"Bearer " + access_token,
              "bluemix-instance":instance_id,
              "prefer":"return=representation",
              "correlation-id":correlation_id  # used for debug
    }
    body_template = {
           'metadata':{
              'collectionType':'application/vnd.ibm.kms.key+json',
              'collectionTotal':1
           },
           'resources':[]
    }


    body = {
           'type':'application/vnd.ibm.kms.key+json',
           'name':key_alias,
           'description': description,
           'extractable': extractable
    }

    request_body = copy.deepcopy(body_template)
    request_body['resources'].append(body)
    request_string_body = json.dumps(request_body)

    need_new_token = False
    key_list = {}
    key_id = ""

    conn = httplib.HTTPSConnection(host)
    try:
        conn.request("POST", "/api/v2/keys", request_string_body,  headers)
        response = conn.getresponse()
    except socket.error as errno:
        print("Socket error attempting to connect to Key Protect service to create a key")
        print(errno)
        sys.exit()
    except:
        print("Unexpected error attempting to connect to Key Protect service to create a key")
        raise

    if response.status == 201:
        if extractable and not quiet:
            print("Created standard key", time.strftime("%m/%d/%Y %H:%M:%S"))
        elif not quiet:
            print("Created root key", time.strftime("%m/%d/%Y %H:%M:%S"))

        #get the json object and convert to a python object
        objs = json.loads(response.read())
        if 'resources' in objs:
            key_list = objs['resources']
            for k in key_list:
                if k['name'] == key_alias:
                    key_id = k['id']
                if verbose:
                    print("   Key name:", k['name'])
                    print("   Key id:", k['id'])
                    print("   Key algorithm type:", k['algorithmType'])

        else:
            print("Error generating key. 'Resources' not in the returned json object")
            sys.exit() 

        if key_id == "":
            print("Error: key created with incorrect name")
            sys.exit()            

    else:
        try:
           objs = json.loads(response.read())
           error_msg = objs['resources']
        except ValueError, e:
           error_msg = {}
           error_msg[0] = {}
           error_msg[0]['errorMsg'] = 'No error message text returned'

        if (response.status == 400 and 
            error_msg[0] == "Bad Request: Token is expired"):
            need_new_token = True
            if not quiet:
                print("create_key: Redrive loop, must get a new access token, the old one is expired...")
        else:
            if extractable:
                print("Failed to create a standard key")
            else:
                print("Failed to create a root key")
            print("Status", response.status, "reason", response.reason)
            print("Correlation id=", headers['correlation-id'])
            print("Key Protect instance ID:", instance_id)
            print("Error Message:", error_msg[0]['errorMsg'])
            sys.exit()

    conn.close()
    return key_id, need_new_token


# ##########################################################################
# Function to import a root key
# ##########################################################################
def import_key(correlation_id, host, instance_id, access_token, key_alias, key_material):
    '''Contact Key Protect to import a customer root key.

       Input is the target Key Protect host, an instance ID for the
       Key Protect service, an access token, a unique, human-readable
       key name (alias), and the base64 encoded key material
       to import. The key must be 256, 384 or 512 bits

       Output is the ID of the newly-created key, or a boolean indicating
       that a new access token is needed.
    '''
    headers = {
              "content_type":"application/vnd.ibm.kms.key+json",
              "authorization":"Bearer " + access_token,
              "bluemix-instance":instance_id,
              "prefer":"return=representation",
              "correlation-id":correlation_id  # used for debug
    }
    body_template = {
           'metadata':{
              'collectionType':'application/vnd.ibm.kms.key+json',
              'collectionTotal':1
           },
           'resources':[]
    }


    body = {
           'type':'application/vnd.ibm.kms.key+json',
           'name':key_alias,
           'payload':key_material,
           'description': 'KeyProtectSample.py root key -- imported',
           'extractable': False
    }

    request_body = copy.deepcopy(body_template)
    request_body['resources'].append(body)
    request_string_body = json.dumps(request_body)

    need_new_token = False
    key_list = {}
    key_id = ""

    conn = httplib.HTTPSConnection(host)
    try:
        conn.request("POST", "/api/v2/keys", request_string_body,  headers)
        response = conn.getresponse()
    except socket.error as errno:
        print("Socket error attempting to connect to Key Protect service to import a key")
        print(errno)
        sys.exit()
    except:
        print("Unexpected error attempting to connect to Key Protect service to import a key")
        raise

    if response.status == 201:
        print("Imported root key", time.strftime("%m/%d/%Y %H:%M:%S"))

        #get the json object and convert to a python objecto
        objs = json.loads(response.read())
        if 'resources' in objs:
            key_list = objs['resources']
            for k in key_list:
                if k['name'] == key_alias:
                    key_id = k['id']
                if verbose:
                    print("   Key name:", k['name'])
                    print("   Key id:", k['id'])
                    print("   Key algorithm type:", k['algorithmType'])

        else:
            print("Error importing key. 'Resources' not in the returned json object")
            sys.exit()

        if key_id == "":
            print("Error: key imported with incorrect name")
            sys.exit()
    else:
        try:
           objs = json.loads(response.read())
           error_msg = objs['resources']
        except ValueError, e:
           error_msg = {}
           error_msg[0] = {}
           error_msg[0]['errorMsg'] = 'No error message text returned'

        if (response.status == 400 and
            error_msg[0] == "Bad Request: Token is expired"):
            need_new_token = True
            if not quiet:
                print("import_key: Redrive loop, must get a new access token, the old one is expired...")
        else:
            print("Failed to import a root key")
            print("Status", response.status, "reason", response.reason)
            print("Correlation id=", headers['correlation-id'])
            print("Key Protect instance ID:", instance_id)
            print("Error Message:", error_msg[0]['errorMsg'])
            sys.exit()

    conn.close()
    return key_id, need_new_token


# ##########################################################################
# Wrap, wrap and generate, or unwrap a data encryption key (i.e., a DEK)
# ##########################################################################
def wrap_unwrap_key(correlation_id, host, instance_id, access_token, wrap_key_id, wrap, keytext=""):
    '''Contact Key Protectt to wrap, generate and wrap, or unwrap a data enryption key (DEK).

       Input is the target Key Protect host, an instance ID for the 
       Key Protect service, an access token, the ID of a root key to use 
       as a wrapping/unwrapping key, a boolean ("wrap") that indicates if 
       we are to wrap or unwrap a key, and keytext. Here is the relationship 
       between the wrap and keytext arguments:
          wrap = True,  keytext="<plaintext key>" : wrap the plaintext key 
                                                    and return the wrapped 
                                                    (encrypted) version
          wrap = True,  keytext=""                : generate a wrapped DEK 
                                                    and return it
          wrap = False, keytext="<encrypted key>" " unwrap the encrypted key 
                                                    and return the plaintext 
                                                    version
      
       Note that keytext, if passed, should be base64 encoded. 

       Output is a wrapped or unwrapped key, base64 encoded, or a boolean
       indicating that a new access token is needed. 
    '''
    need_new_token = False  # assume the access token is valid to start

    headers = {
              "content_type":"application/vnd.ibm.kms.key_action+json",
              "authorization":"Bearer " + access_token,
              "bluemix-instance":instance_id,
              "prefer":"return=representation",
              "correlation-id":correlation_id  # used for debug
    }

    wrap_body = {
           'plaintext':keytext
    }
    gen_and_wrap_body = {
    }
    unwrap_body = {
           'ciphertext':keytext
    }

    if wrap:      # initialize body of request depending on what we're doing
       if keytext == "":
           request_string_body = json.dumps(gen_and_wrap_body)
       else:
           request_string_body = json.dumps(wrap_body)
       action = "?action=wrap"
    else:
       request_string_body = json.dumps(unwrap_body)
       action = "?action=unwrap"

    conn = httplib.HTTPSConnection(host)
    try:
        conn.request("POST", "/api/v2/keys/" + wrap_key_id + 
                     action, request_string_body,  headers)
        response = conn.getresponse()
    except socket.error as errno:
        print("Socket error attempting to connect to Key Protect service to wrap or unwrap a key")
        print(errno)
        sys.exit()
    except:
        print("Unexpected error attempting to connect to Key Protect service to wrap or unwrap a key")
        raise

    if response.status == 200:
        if wrap and keytext == "" and not quiet:
            print("Generated a wrapped data encrytion key", time.strftime("%m/%d/%Y %H:%M:%S"))
        elif wrap and not quiet:
            print("Wrapped a data encrytion key", time.strftime("%m/%d/%Y %H:%M:%S"))
        elif not quiet:
            print("Unwrapped a data encryption key", time.strftime("%m/%d/%Y %H:%M:%S"))

        #get the json object and convert to a python object
        objs = json.loads(response.read())
        
        if wrap:
            key_output_text = objs['ciphertext']
        else:
            key_output_text = objs['plaintext']

        if extraverbose:
            if wrap:
                print("Wrapped data encryption key, base64 encoded:", key_output_text)
            else:
                print("Unwrapped data encryption key, base64 encoded:", key_output_text)
 
    else:
        key_output_text = ""
        try:
           objs = json.loads(response.read())
           error_msg = objs['resources']
        except ValueError, e:
           error_msg = {}
           error_msg[0] = {}
           error_msg[0]['errorMsg'] = 'No error message text returned'

        if ((response.status == 400) and 
            (error_msg[0]['errorMsg'] == 'Bad Request: Token is expired')):
            need_new_token = True
            if not quiet:
                print("wrap_unwrap_key: Redrive loop, must get a new access token, the old one is expired...")
        else:
            if wrap and keytext == "":
                print("Failed to generate a wrapped data encryption key")
            elif wrap:
                print("Failed to wrap a data encryption key")
            else:
                print("Failed to unwrap a data encryption key")
            print("Status", response.status, "reason", response.reason)
            print("Correlation id=", headers['correlation-id'])
            print("Key Protect instance ID:", instance_id)
            print("Error Message:", error_msg[0]['errorMsg'])
            sys.exit()

    conn.close()

    return key_output_text, need_new_token

# ##########################################################################
# Function to delete all root keys associated with this KP instance
# ##########################################################################
def delete_root_keys(correlation_id, host, instance_id, access_token):
    '''Delete all of the root keys this Key Protect instance owns.

       Input is the target Key Protect host, an instance ID for the
       Key Protect service, an access token, and a correlation ID.

       Only output is a boolean indicating if a new access token is needed.
    '''
    headers = {
              "authorization":"Bearer " + access_token,
              "bluemix-instance":instance_id,
              "prefer":"return=representation",
              "correlation-id":correlation_id # used for debug
    }

    need_new_token = False
    
    if not quiet:
       print("Attempting to delete all root keys owned by Key Protect instance", instance_id, "...")

    key_list, need_new_token = get_key_list(correlation_id, 
                                            host, 
                                            instance_id, 
                                            access_token)

    if not need_new_token:
       if not quiet:
          print("List of stored keys found:")
          for k in key_list:
             print("   Key name:", k['name'], "with ID:", k['id'])

       conn = httplib.HTTPSConnection(host)
       for k in key_list:    # Delete each key
          key_id = k['id']
          key_name = k['name'] 
          try:
              conn.request("DELETE", "/api/v2/keys/" + key_id, "", headers)
              response = conn.getresponse()
          except socket.error as errno:
              print("Socket error attempting to connect to Key Protect service to delete root keys")
              print(errno)
              sys.exit()
          except:
              print("Unexpected error attempting to connect to Key Protect service to deleter root keys")
              raise

          if response.status == 200:
             #get the json object and convert to a python object
             objs = json.loads(response.read())
             if 'resources' in objs:
                resource_dict = objs['resources']
                key_deleted = resource_dict[0]['deleted'] # 'key deleted successfully' flag
                if key_deleted:
                   if not quiet:
                      print("Deleted root key", key_name, "with ID", key_id, "at", time.strftime("%m/%d/%Y %H:%M:%S"))
                else:
                   print("Attempt to delete key", key_name, "with ID", key_id, "was unsuccessful")

          else:  # error cases
              objs = json.loads(response.read())
              try:
                 objs = json.loads(response.read())
                 error_msg = objs['resources']
              except ValueError, e:
                 error_msg = {}
                 error_msg[0] = {}
                 error_msg[0]['errorMsg'] = 'No error message text returned'

              if ((response.status == 400) and
                  (error_msg[0]['errorMsg'] == 'Bad Request: Token is expired')):
                  need_new_token = True
                  key_id = ""
                  if not quiet:
                      print("get_key_list: Redrive loop, must get a new access token, the old one is expired...")
                  break # exit the FOR loop
              else:
                  print("Failed to delete root key", key_name, "with ID", key_id)
                  print("Status:", response.status, "reason:", response.reason)
                  print("Correlation id=", headers['correlation-id'])
                  print("Key Protect instance ID:", instance_id)
                  print("Error Message:", error_msg[0]['errorMsg'])
                  sys.exit()

          conn.close()
    return need_new_token



############################################################################
# function to print progress as a percentage 
############################################################################
def print_progress(count, total):
    '''Print progress as a percentage of total items processed. 
    '''

    percent_complete = float(count) / total * 100
    if percent_complete > 10 and percent_complete < 100:  # a cheat for back spacing
        print(int(percent_complete), "percent complete", end=' ')
        print("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b", end=' ')   # back space
        sys.stdout.flush()
    return

############################################################################
# function to load info on the target service from the input file
############################################################################
def read_input_file(file):
    '''Load info on target service from the input file.

       Input is the name of the file.
    '''
    try:
        cred = json.load(open(file))
    except IOError as errno:
        print("Error attempting to open input file", file)
        print("Ensure file exists")
        sys.exit()
    except:
        print("Unexpected error trying to open input file", file, sys.exc_info()[0])
        raise

    service_host = cred['service_host'].strip() 
    service_instance_id = cred['service_instance_id'].strip()
    root_key_name = cred['root_key_name'].strip()

    print("\nRead the following from input file", file, ":")
    print("   Service host:", service_host)
    print("   Service instance ID:", service_instance_id)
    print("   Root key name:", root_key_name, "\n")
    
    return service_host, service_instance_id, root_key_name

############################################################################
# function to load Key Protect API key from apikey input file
############################################################################
def read_apikey_file(file):
    '''Load api key for target service from the api key file.

       Input is the name of the file.
    '''
    try:
        cred = json.load(open(file))
    except IOError as errno:
        print("Error attempting to open api key file", file)
        print("Ensure file exists")
        sys.exit()
    except:
        print("Unexpected error trying to open api key file", file, sys.exc_info()[0])
        raise

    # the UI generates an apikey file with "apiKey" as a key, 
    # but the bx CLI generates it with "apikey" as the key.
    # Try both.
    try:
       api_key = cred['apikey'].strip()
    except KeyError:
       api_key = cred['apiKey'].strip()

    return api_key


##########################################################################
##########################################################################
# Start of main program. 
##########################################################################
##########################################################################

##########################################################################
# Process and validate input arguments and options
##########################################################################
if __name__ == "__main__":
    usage = "usage: %prog [options]"
    version = "%prog 1.0"
    p = optparse.OptionParser(usage=usage, version=version)
    p.add_option('--quiet', '-q',
                 action='store_true',
                 help='suppress all repetitive messages (not error messages) and display just a progress counter instead')
    p.add_option('--verbose', '-v',
                 action='store_true',
                 help='show details in stdout')
    p.add_option('--extraverbose', '-x',
                 action='store_true',
                 help='show details including keys and tokens in stdout')
    p.add_option('--createkey', '-c',
                 action='store_true',
                 help='create root key if inputted root key is not found in Key Protect. Incompatible with --importkey option ')
    p.add_option('--importkey', '-i',
                 action='store_true',
                 help='import a predefined root key if inputted root key is not found in Key Protect. Incompatible with --createkey option ')
    p.add_option('--file', '-f',
                 action='store', type="string", default='KPinfo.json',
                 help='input json file that lists the Key Protect host url, Key Protect Instance ID, and root key name. Default: KPinfo.json')
    p.add_option('--apifile', '-a',
                 action='store', type="string", default='apiKeyKP.json',
                 help='API key file for Key Protect instance. Default: apiKeyKP.json')
    p.add_option('--repeat', '-r',
                 action='store', type="int", default=1,
                 help='how many times to loop through  execution. Default: 1')
    p.add_option('--delay', '-d',
                 action='store', type="int", default=1,
                 help='how many seconds to delay between passes. Default: no delay')
    p.add_option('--deleteAll', '-D',
                 action='store_true',
                 help='delete ALL root keys associated with this Key Protect instance upon completion of this program. Default: do not delete keys')
    options, args = p.parse_args()

    quiet                    = options.quiet
    verbose                  = options.verbose
    extraverbose             = options.extraverbose
    if extraverbose:
       verbose = True
    if quiet:                # can't be quiet and verbose...
       verbose =  False
       extraverbose = False  
    generate_key_if_required = options.createkey
    import_key_if_required   = options.importkey
    repeat                   = options.repeat
    input_filename           = options.file
    apikey_filename          = options.apifile
    delay                    = options.delay
    deleteAll                = options.deleteAll
    
    if len(args) > 0:
        p.error("Too many arguments")
    if generate_key_if_required and import_key_if_required:
        p.error("Cannot specify both createkey and importkey options")
    if repeat < 1:
         p.error("Value of --repeat must be greater than 0")

##############################################################################
# Begin main processing
#############################################################################

    # read input file to get info on target service 
    service_host, service_instance_id, root_key_name = read_input_file(input_filename)
    # read input api key file to get the api key for the Key Protect service
    api_key = read_apikey_file(apikey_filename)

    # Get an access token we can use to retrieve the API endpoint URI
    access_token = get_access_token(api_key)
    token_expired = False

    # Now, if no service host was passed in the input file,
    # then retrieve the API endpoint URI for us to connect to
    if service_host == "":
       print ("No service host passed as input, acquiring connection info...")
       service_host, token_expired = get_api_endpoint_uri(service_instance_id, access_token)
       print ("Using service host", service_host)

    # if asked to import a customer root key, define base64-encoded key material to import
    if import_key_if_required:
       importable_customer_root_key_base64 = "NzcwQThBNjVEQTE1NkQyNEVFMkEwOTMyNzc1MzAxNDI=" # This is a 256 bit key

    r = 1                    # define loop counter
    while r <= repeat:
        # Print loop counter only if quiet mode not enabled by user.
        if not quiet:
            print("\n*** Pass", r, "***\n")

        if token_expired:
            # get access token needed for invoking Key Protect API
            # It will expire in 60 minutes
            access_token = get_access_token(api_key)
            token_expired = False

        # Generate a random v4 uuid, stringify it, and use it as 
        # a correlation ID. Create a new one each time thru loop. 
        # This will be added to the header of each KP API call
        # so it will show up in the KP logs if needed for debug.
        correlation_id=str(uuid.uuid4())

        #************************
        # get id for the root key
        #************************
        wrap_key_id, token_expired = get_key_id(correlation_id,
                                                service_host, 
                                                service_instance_id, 
                                                access_token, 
                                                root_key_name)     
        if token_expired:
            continue   # redrive loop to get a new access token

        #*******************************************
        # If root key not found in Key Protect then, 
        # if requested by user, create it or import it.
        #*******************************************
        if wrap_key_id == "NOT FOUND":
            if generate_key_if_required:
               non_root_key = False
               wrap_key_id, token_expired = create_key(correlation_id,
                                                       service_host, 
                                                       service_instance_id, 
                                                       access_token, 
                                                       root_key_name, 
                                                       non_root_key)
               if token_expired:
                   continue   # redrive loop to get a new access token
            elif import_key_if_required:
               wrap_key_id, token_expired = import_key(correlation_id,
                                                       service_host,
                                                       service_instance_id,
                                                       access_token,
                                                       root_key_name,
                                                       importable_customer_root_key_base64)
               if token_expired:
                   continue   # redrive loop to get a new access token

            else:
                print("Please confirm root key name in input file, or specify the -c option if you want me to create the root key, or -i option if you want me to import a root key")

                sys.exit()
        #*******************************************************
        # generate and work with a wrapped data encryption key
        #*******************************************************
       
        # generate a wrapped data encryption key (DEK). 
        # By omitting the "keytext" parm, we are telling wrap_unwrap_key 
        # to generate a DEK.
        wrapped_DEK, token_expired = wrap_unwrap_key(correlation_id,
                                                     service_host, 
                                                     service_instance_id, 
                                                     access_token, 
                                                     wrap_key_id, 
                                                     wrap=True)
        if token_expired:
            continue   # redrive loop to get a new access token

        # unwrap the generated data encryption key and encrypt a message with it
        unwrapped_base64_DEK, token_expired = wrap_unwrap_key(correlation_id,
                                                              service_host, 
                                                              service_instance_id, 
                                                              access_token, 
                                                              wrap_key_id, 
                                                              wrap=False, 
                                                              keytext=wrapped_DEK)
        if token_expired:
            continue   # redrive loop to get a new access token

        # decode from base64 so we can use it
        unwrapped_DEK = base64.b64decode(unwrapped_base64_DEK) 

        # encrypt a message with the unwrapped DEK
        cipher = AES.new(unwrapped_DEK, AES.MODE_ECB)
        encrypted_msg = cipher.encrypt(b'The quick brown fox  jumps  over  the  lazy  dog')

        # now wrap and unwrap the DEK again, 
        # and ensure it can be used to decrypt the message
        wrapped_DEK, token_expired = wrap_unwrap_key(correlation_id,
                                                     service_host, 
                                                     service_instance_id, 
                                                     access_token, 
                                                     wrap_key_id, 
                                                     wrap=True, 
                                                     keytext=unwrapped_base64_DEK)
        if token_expired:
            continue   # redrive loop to get a new access token

        unwrapped_base64_DEK, token_expired = wrap_unwrap_key(correlation_id,
                                                              service_host, 
                                                              service_instance_id,
                                                              access_token, 
                                                              wrap_key_id, 
                                                              wrap=False, 
                                                              keytext=wrapped_DEK)
        if token_expired:
            continue   # redrive loop to get a new access token

        # decode from base64 so we can use it
        unwrapped_DEK = base64.b64decode(unwrapped_base64_DEK) 

        # decrypt the previously encrypted  message with the unwrapped DEK
        cipher = AES.new(unwrapped_DEK, AES.MODE_ECB)
        decrypted_msg = cipher.decrypt(encrypted_msg)
        if not quiet:
            print("Message decrypted with unwrapped generated DEK:", decrypted_msg)

        #*************************************
        # finish up this pass through the loop
        #*************************************
        if quiet :
           print_progress(r, repeat)

        if (delay > 0) and (r < repeat) :  # pause between passes if so requested by user
            time.sleep(delay)

        r = r + 1     # increment the loop counter

r = r - 1    # adjust for output    
if r == 1:
    print()
    print("1 pass through script completed successfully.")
else:
    print()
    print(r, "passes through script completed successfully.")

# If user requsted all root keys to be deleted upon program completion,
# then delete them.
if deleteAll:
   print("Main program loop completed")
   print()
   delete_attempted = False
   while not delete_attempted:
      token_expired = delete_root_keys(correlation_id, # try to delete keys
                                       service_host,
                                       service_instance_id,
                                       access_token)
      if token_expired:
          # get access token needed for invoking Key Protect API
          # It will expire in 60 minutes
          access_token = get_access_token(api_key)
          token_expired = False
      else: 
          delete_attempted = True # exit loop
          print("All root keys have been successfully deleted for Key Protect instance", service_instance_id)

print()
print("Script completed at", time.strftime("%H:%M:%S"))
