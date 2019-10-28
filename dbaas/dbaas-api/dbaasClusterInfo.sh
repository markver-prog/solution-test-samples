#!/bin/bash
#
# run some DBaaS API
# Notes:
# - Requires: jq (json parser)
#    if needed replace jq with suitable json formatting tool, ex:
#       python -m json.tool
#       json_pp             #(i.e. perl JSON::PP module)
#       json_reformat       #(i.e. yajl tools)
#       jsonlint
#    etc...
# - The json output that comes out of the command is often passed 
#    directly to further filters for pulling out specific values.
#   For that reason error messages and other formatting displays 
#    are explicitly sent to file descriptor 2 using ">&2" syntax
#    to allow them to be shown despite the pipe.
#

if [ -z "$1" ]; then
   >&2 echo "usage: $(basename $0) <cluster-id> [cert-file]"
   >&2 echo "ex:    $(basename $0) 2e3b8dc8-72b1-4f64-8eb4-012345654321 /path/to/ca/cert.pem"
   exit 1 
fi

# Check for env variables needed. These can be placed and source from an openrc file for convenience.
test -z "$DBAAS_MANAGER_IP" && (>&2 echo "error: DBAAS_MANAGER_IP not set, please source openrc") && exit 1
test -z "$DBAAS_MANAGER_PORT" && (>&2 echo "error: DBAAS_MANAGER_PORT not set, please source openrc") && exit 1
test -z "$API_KEY" && (>&2 echo "error: API_KEY not set, please source openrc") && exit 1

# Set the target cluster-id
target="${1}"

# An IBM provided CA certificate is required to talk to the dbaas-manager.
# These can be obtained from your DBaaS service-instance's dashboard overview tab.
# By default look for the CA file in the current directory.
# If needed, user should pass in the full path to the correct CA cert file.
sslCA="~/cert.pem"
if [ -n "$2" ]; then
   sslCA="$2"
fi
SSLPARMS="--cacert $sslCA"

# concatenate the host:ip for use in the curl calls
DBAASHOST="${DBAAS_MANAGER_IP}:${DBAAS_MANAGER_PORT}"

# Use your ibmcloud API_KEY and obtain a request token from the dbaas-manager
creds=$(curl -f -s $SSLPARMS -H "accept: application/json" -H "api_key: $API_KEY" -XGET https://${DBAASHOST}/api/v1/auth/token)
test $? -ne 0 && (>&2 echo -e "error: Problem getting token:\n ${creds}") && exit 1

# parse out the token and account ID from the results of previous operation using jq 
token=$(echo ${creds} | jq -r '.access_token')
accountid=$(echo ${creds} | jq -r '.user_id')

# Use the obtained token to issue further requests to dbaas-manager
RC=0
tmpout=$(mktemp)
case $target in
????????-????-????-????-????????????)
    # target string satisfies UUID format;  attempt the API call to gather data on the specific cluster ID
    ### use curl "-s -S" to run in silent mode (skip the progress meter) but still return message when an error is encountered
    ### use curl "-f" to exit with RC 22 on failure rather than an html output with the error details
    curl -f -s -S $SSLPARMS -H "accept: application/json" -H "x-auth-token: ${token}" -o $tmpout -XGET https://${DBAASHOST}/api/v1/$accountid/clusters/${target}
    if [ $? -ne 0 ]; then
       >&2 echo -e "error: Problem getting cluster info"
       RC=1
    else
       # pass the output to jq for pretty json formatting
       cat $tmpout | jq -r .
    fi
    ;;
*)
    >&2 echo "error: '$target' does not match expected cluster-id format"
    RC=1
    ;;
esac
rm $tmpout

# pretty print
>&2 echo

exit $RC
