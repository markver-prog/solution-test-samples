This python script exercises various aspects of the IBM Cloud 
Hyper Protect Crypto Services (HPCS) Key Protect service through its REST API.
This script works equally well with HPCS Key Protect and standard Key Protect, since
the REST APIs are the same. The only difference is that since each HPCS instance 
has a unique API endpoint URI, HPCS provides the ability to dynamically
determine what that endpoint is. So, if this script finds that a null string 
was passed in for the service host, it will attempt to retrieve it dynamically. 

The high level flow is:
1.  Contact the Cloud Identity and Access Management service to get an access token, 
    passing as input an API key for the user's Key Protect service.
2.  Have Key Protect search for a requested Customer Root Key (CRK) and return
    its ID, if found.
3.  If the CRK is not found, then either:
       * a. Ask Key Protect to generate a CRK, OR
       * b. Import the user's own CRK into Key Protect
4.  Have Key Protect generate and return a Data Encryption Key (DEK) wrapped 
    (encrypted) using the CRK
5.  Have Key Protect unwrap the DEK
6.  AES encrypt a message using the unwrapped DEK
7.  Have Key Protect wrap and unwrap the DEK again, then ensure it can still
    be used to decrypt the previously encrypted message
8.  Repeat steps 2-7 as often as requested
9.  An access token is only valid for 60 minutes. Normally this is sufficient,
    but if the above loop runs long enough the token can expire. In that case,
    it reacts to the expired token by requesting a new one. 
10. Finally, delete the CRK if so requested.

Input:
1. The IBM Cloud Key Protect service information is provided via a file 
(by default called `KPinfo.json`).
2. A file containing the api key for the Key Protect service

The user can also specify options when invoking the script.
The available options (in no particular order) are:

    --version               Print the version of this script and exit
    --help, -h              Prints help info and exits
    --quiet, -q             Show progress count instead of repetitive messages
    --verbose, -v           Show more details in stdout
    --extraverbose, -x      In addition to verbose output, also show 
                            tokens and keys
    --repeat, -r loopcount  Number of times to loop through execution. 
                            Default: 1
    --delay, -d seconds     Number of seconds to delay between passes. 
                            Default: no delay
    --deleteAll -D          Delete ALL root keys associated with this 
                            Key Protect instance upon completion of the
                            program. Default: Do not delete keys.
    --file, -f filename     Path to input file. Default: KPinfo.json
    --apifile, -a filename  Path to input apiKey file. Default: apiKeyKP.json
    --createkey, -c         Create root key if inputted root key not found
                            in Key Protect. Incompatible with --importkey option.
    --importkey, -i         Import a (predefined) root key if inputted root key
                            not found in Key Protect. Incompatible with
                            --createkey option.

Here is the format of the input file (`-f` option), with example input shown. 
You can retrieve the "service_instance_id" using the ibmcloud CLI:
```
ibmcloud resource service-instance "Key Protect-rc" -id 
```
(where "Key Protect-rc" is the name of the KP instance you created).
This will output something called a `.crn.`, which has the service ID at the end of it. 

This example passes in a null service_host, which tells the script
to dynamically retrieve the connection info (this does not work for
standard Key Protect, it is a unique function for HPCS Key Protect):

    {
    "service_host": "",
    "service_instance_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "root_key_name":"SampleRootKey"
    }

This example passes in a specific service_host for HPCS Key Protect
(this is normally not needed, the null string example above is
all that is needed for HPCS Key Protect instances):

    {
    "service_host": "us-south.hpcs.cloud.ibm.com:11399",
    "service_instance_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "root_key_name":"SampleRootKey"
    }

This example passes in a service_host for standard Key Protect:

    {
    "service_host": "keyprotect.us-south.bluemix.net",
    "service_instance_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "root_key_name":"SampleRootKey"
    }

Here is the format of the input Key Protect API key file (`-a` option), which
is the same format as provided by the Key Protect service. You do not need
to create this file yourself, you can simply download it through the UI at the 
time you create the API key for the service.

    {
    "name": "SampleAPIKey",
    "description": "A sample for test purposes",
    "createdAt": "2018-03-21T17:15+0000",
    "apikey": "xxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }    

This script was developed and tested on Linux on System z using python 2.7.12.
