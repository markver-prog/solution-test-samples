#!/bin/bash
#
# Script to provision an instance of standard Key Protect, 
# or HPCS enabled for use with Key Protect. 
#
script_version="1.0"
hostname=$(hostname)

#login uri for the ibmcloud cli. 
login_host="api.ng.bluemix.net"         

resource_group="default"

crypto_endpoint="https://zcryptobroker.mybluemix.net/crypto_v1/instances"

# info about the new service to pass to KeyProtectSample.py
crypto_service_host=""                                 # Null string, telling KeyProtectSample.py to dynamically
                                                       # retrieve the uri from HPCS
KP_service_host_prod="keyprotect.us-south.bluemix.net" # The API endpoint for standard Key Protect 
service_host=$crypto_service_host                      # The default

crypto_apikey_file="apiKeyHpcsKP.json" # Name of output file containing HPCS Key Protect API key
KP_apikey_file="apiKeyStandardKP.json" # Name of output file containing standard Key Protect API key
apikey_file=$crypto_apikey_file        # The default

crypto_outfilename="authHpcsKP.json"   # Name of output file when using HPCS Key Protect
KP_outfilename="authStandardKP.json"   # Name of output file when using standard Key Protect
outfilename=$crypto_outfilename        # The default

current_dir=$(pwd) # where this script is located

sleep_time=10          # Seconds to pause between actions 
standard_KeyProtect=0  # Default: create an HPCS Key Protect instance, 
                       # rather than a standard Key Protect instance. This can be changed
                       # with the "-K" option on script invocation.
override_apikey_file=0 # Default: user did not override default apikey_file name
override_outfilename=0 # Default: user did not override default outfilename
    

usage(){
        echo "Usage: $0 [-h] [-K] [-o filename] [-a filename] [-r res-group ] apikey_file"
        echo "   -h          : Display this help text and exit"
        echo "   -K          : Create a standard Key Protect instance, rather than "
        echo "                 an HPCS Key Protect instance."
        echo "                 Default: Create an HPCS Key Protect instance."
        echo "   -o filename : Path to json output file that lists the host url,"
        echo "                 the Key Protect instance ID, and the root key name to create."
        echo "                 Default for HPCS Key Protect: authHpcsKP.json"
        echo "                 Default for standard Key Protect: authStandardKP.json"
        echo "   -a filename : Path to json Key Protect API key output file." 
        echo "                 Default for HPCS Key Protect: apiKeyHpcsKP.json"
        echo "                 Default for standard Key Protect: apiKeyStandardKP.json"
        echo "   -r res-group: Name of IBM Cloud resource group to target."
        echo "                 Use 'ibmcloud resource groups' to see what"
        echo "                 resource groups are defined for this"
        echo "                 IBM Cloud userid."
        echo "                 Default: 'default'"
        echo "   apikey_file : Path to file containing Platform API key"
        echo "                 associated with your userid"
        echo "                 for authenticating to IBM Cloud."

}

# Quick function to check if a command is installed
command_installed() {
   command -v "$1" > /dev/null 2>&1 ;
}

#
# catch signals to terminate and exit cleanly
#
trap "echo; echo '$0 terminated by signal request'; exit" SIGINT SIGTERM

#
# parse options 
#
while getopts ":hpKDo:a:r:" opt; do
   case $opt in
     h) # display help
        echo ""
        echo "Script version $script_version"
        echo ""
        echo "Script creates one standard Key Protect instance,"
        echo "or one HPCS instance that is setup for"
        echo "access via the Key Protect REST APIs."
        echo "Outputs two files:"
        echo "  1. File containing API key for the new service"
        echo "  2. File with additional data to be consumed as input by "
        echo "     KeyProtectSample.py"
        echo ""
        usage
        echo ""
        exit 1
        ;;
     K) # Create standard Key Protect instance, rather than HPCS Key Protect
        standard_KeyProtect=1
        ;;

     o) # output file name
        outfilename=${OPTARG}
        override_outfilename=1
        ;;
     a) # output api key file name
        apikey_file=${OPTARG}
        override_apikey_file=1
        ;;
     r) # specify resource group
        resource_group=${OPTARG}
        ;;
    \?) # invalid option
        echo "Invalid option"
        usage
        exit 1
        ;;
     :)  # no value specified for a valid option
        echo "Option requires a value"
        usage
        exit 1
        ;;
   esac
done
shift $(expr $OPTIND - 1 ) # shift positional parms away so now can parse required arguments

#
# validate arguments
#
if [ "$#" -ne 1 ]; then
   echo "Required argument is missing"
   usage
   exit 1
fi

#
# save arguments      
#
script_name=$0
platform_apikey_file=$1

# If we are setting up standard Key Protect rather than HPCS Key Protect...
if [ $standard_KeyProtect -eq 1 ]; then
   service_host=$KP_service_host_prod
   # If user requested a standard Key Protect instance and did not
   # override the default names of output files, then change
   # the default names to those for standard Key Protect output files
   if [ $override_apikey_file -eq 0 ]; then
      apikey_file=$KP_apikey_file
   fi
   if [ $override_outfilename -eq 0 ]; then
      outfilename=$KP_outfilename
   fi
fi

# 
# Check if the ibmcloud cli is installed. If not, abort
#
if ! command_installed ibmcloud; then 
   echo "Error: Need to install IBM Cloud CLI"
   exit 8
fi

# disable check for new version of ibmcloud cli
ibmcloud config --check-version=false

#
# Login to IBM Cloud, using the API key file that was passed in
#
echo ">>> Logging into IBM Cloud..."
ibmcloud login -a $login_host --apikey @$platform_apikey_file 
rc=$?
if [ $rc -ne 0 ]; then
	echo "Error attempting to login to IBM Cloud, rc=$rc"
        echo "Ensure API key file is correct."
        exit 8
fi
#
# Specify the resource group to target
#
if [ $resource_group != "default" ]; then
   echo ">>> Assigning target resource group..."
   ibmcloud target -g $resource_group
   rc=$?
   if [ $rc -ne 0 ]; then
           echo "Error attempting to set resource group in IBM Cloud, rc=$rc"
           exit 8
   fi
fi

#
# Define names for new service, 
# and for the Service ID and Key Protect API key.
#
crypto_name="hpcs-autogen-$hostname"    # Name of an HPCS Key Protect service instance
KP_name="KeyProtect-autogen-$hostname"  # Name of a standard Key Protect service instance
if [ $standard_KeyProtect -eq 0 ]; then  
   service_name=$crypto_name               # The default. 
else
   service_name=$KP_name
fi

service_ID_name="autogen-Service-ID-for-$service_name"
API_key_name="KP-api-key-for-$service_name"
auth_policy_ID="NONE"

#======================================================================
#  BEGIN MAIN PROCESSING
#======================================================================
existing_crypto_count=$(ibmcloud resource service-instance $service_name --id | grep crn | wc -l)

#
# Create a new instance, if needed
#
if [ $existing_crypto_count -eq 0 ]; then
   echo
   # create an instance of the service
   if [ $standard_KeyProtect -eq 1 ]; then
      echo ">>> Okay, now we'll create a standard Key Protect service instance..."
      ibmcloud resource service-instance-create $service_name kms tiered-pricing us-south
   else
      echo ">>> Okay, now we'll create an HPCS service instance..."
      ibmcloud resource service-instance-create $service_name hs-crypto beta-plan us-south
   fi
   rc=$?
   if [ $rc -ne 0 ]; then
      echo "Error attempting to create  service $service_name, rc=$rc"
      exit 8
   else
      echo ">>> Created new service instance $service_name "
      sleep $sleep_time
      echo
   fi
else
   echo ">>> Service instance $service_name already exists. Reusing it."
fi
# Save the instance ID for the new or existing service.
# Note that if there are multiple instances with the same name,
# only the first instance will be saved. 
crypto_instance_ID=$(ibmcloud resource service-instance $service_name --id  | awk -F ":" 'NR==2{ print $8}')
rc=$?
if [ $rc -ne 0 ]; then
  echo "Error attempting to retrieve service instance ID for $service_name, rc=$rc" 
  exit 8
fi
echo ">>> Service instance ID = $crypto_instance_ID"

#
# If a Service ID for this host already exists, reuse it. 
# Otherwise, create one. 
#
service_ID_found_state=$(ibmcloud iam service-id $service_ID_name | awk 'NR==2{ print $1 }')
if [[ $service_ID_found_state != "OK" ]]; then
   echo ">>> Creating Service ID..."
   ibmcloud iam service-id-create $service_ID_name -d "Used in generating Key Protect API key for $service_name"
   rc=$?
   if [ $rc -ne 0 ]; then
      echo "Error attempting to create Service ID $service_ID_name, rc=$rc"
      exit 8
   fi
   echo ">>> Service ID $service_ID_name created"
else
   echo ">>> Service ID $service_ID_name already exists, so will reuse it"
fi
#
# If a service policy to enable the API
# to read/write to it already exists, reuse it.
# Otherwise, create one.
#
service_policy_found_state=$(ibmcloud iam service-policies $service_ID_name | awk 'NR==3')
if [[ $service_policy_found_state == "No policy found" ]]; then

   if [ $standard_KeyProtect -eq 1 ]; then
      echo ">>> Creating service policy for access to Key Protect services..."
      ibmcloud iam service-policy-create $service_ID_name                 \
                                   --roles "Administrator,Manager"        \
                                   --service-name "kms"                   \
                                   --service-instance $crypto_instance_ID \
                                   --region "us-south"                    \
                                   --force
   else
      echo ">>> Creating service policy for access to HPCS services..."
      ibmcloud iam service-policy-create $service_ID_name                 \
                                   --roles "Administrator,Manager"        \
                                   --service-name "hs-crypto"             \
                                   --service-instance $crypto_instance_ID \
                                   --region "us-south"                    \
                                   --force
   fi

   rc=$?
   if [ $rc -ne 0 ]; then
      echo "Error attempting to create Service Policy, rc=$rc"
      exit 8
   fi
   echo ">>> Service policy created"
else
   echo ">>> Service policy already exists, so are reusing it."
fi

#
# Create the api key for the Key Protect service instance and save it 
# as a file.
#
echo ">>> Creating API key for service instance..."
ibmcloud iam service-api-key-create $API_key_name $service_ID_name --file $apikey_file
rc=$?
if [ $rc -ne 0 ]; then
   echo "Error attempting to get Key Protect API key for service instance $service_name, rc=$rc"
   exit 8
fi
echo ">>> Created Key Protect API key for $service_name"

#
# Write out the json file that will be used as input by 
# KeyProtectSample.py. If it already exists, overwrite it. 
#
cat <<EOF > $outfilename
{
  "service_host": "$service_host",
  "service_instance_id": "$crypto_instance_ID",
  "root_key_name": "SolutionTestRootKeyFor-$hostname"
}
EOF

echo
echo "*** Json output file written to $outfilename ***"
echo "*** Key Protect API key file written to $apikey_file ***"
echo
if [ $standard_KeyProtect -eq 0 ]; then
   echo ">>> NEXT, you MUST initialize a new HPCS instance with a master key. <<<"
   echo ">>> That is done via the ibmcloud tke CLI                            <<<"
   echo
else
   echo ">>> Your standard Key Protect instance is ready to use <<<"
   echo
fi

#
# logout of IBM Cloud
#
ibmcloud logout

echo ">>> Script $script_name completed successfully."

exit 0
