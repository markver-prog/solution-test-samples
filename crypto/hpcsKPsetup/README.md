Script to configure a system with an instance of 
standard Key Protect, or HPCS enabled for use with Key Protect.
It is intended for provisioning an instance to be consumed
by KeyProtectSample.py, which is also available in this repo.

The high level flow is:
  1. Logs onto IBM Cloud via the ibmcloud cli using the
     Platform API key passed in as input
  2. Tells IBM Cloud to target the resource group
     passed in as input, if any
  3. Creates a new service instance for use
     by this system.
  4. Creates a service policy to define access to
     the service.
  5. Creates an API key for accessing the service
  6. Writes the output json files for consumption by
     KeyProtectSample.py
  7. Logs out of IBM Cloud and exits.

Input:
Takes 1 required argument:
  apikey_file : Path to file containing Platform API key for
                authenticating to IBM Cloud.

The user can also specify options when invoking the script. 
The available options (in no particular order) are:

    -h          : Displays help text and exits
    -r          : Name of IBM Cloud resource group to target.
                  The "ibmcloud resource groups" command will show
                  resource groups defined for this IBM Cloud userid.
    -K          : Create a standard Key Protect instance, rather than
                  an HPCS Key Protect instance.
                  Default: Create an HPCS Key Protect instance.
    -o filename : Path to json output file.
                  Default for HPCS Key Protect: authHpcsKP.json
                  Default for standard Key Protect: authStandardKP.json
    -a filename : Path the Key Protect API key output file.
                  Default for HPCS Key Protect: apiKeyHpcsKP.json"
                  Default for standard Key Protect: apiKeyStandardKP.json"

Output: 
  1. A new service instance
  2. IAM service policy for authorizing access to the instance
  3. An API key for the instance for accessing Key Protect services
  4. A json file containing an API key for accessing
     the Key Protect services
  5. A json output file that provides other initializaton data
     for KeyProtectSample.py

Here is the format of the output Key Protect API key file (`-a` option), which
is the same format as provided by the IAM service:

   {
   "name": "SampleAPIKey",
   "description": "A sample for test purposes",
   "createdAt": "2018-03-21T17:15+0000",
   "apikey": "xxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   }

Here is the format of the output file for an HPCS instance (`-o` option):

   {
   "service_host": "",
   "service_instance_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
   "root_key_name":"SampleRootKey"
   }

Here is the format of an output file for a standard Key Protect instance (`-o` option):

   {
   "service_host": "keyprotect.us-south.bluemix.net",
   "service_instance_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
   "root_key_name":"SampleRootKey"
   }


