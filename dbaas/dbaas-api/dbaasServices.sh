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
   >&2 echo "usage: $(basename $0) <list|cluster-id> [cert-file]"
   >&2 echo "ex:    $(basename $0) list /path/to/ca/cert.pem"
   >&2 echo "ex:    $(basename $0) 2e3b8dc8-72b1-4f64-8eb4-123456543210 /path/to/ca/cert.pem"
   exit 1 
fi

# check for needed env parameters.  These may be placed and source from an openrc file for convenience.
test -z "$DBAAS_MANAGER_IP" && (>&2 echo "error: DBAAS_MANAGER_IP not set, please source openrc") && exit 1
test -z "$DBAAS_MANAGER_PORT" && (>&2 echo "error: DBAAS_MANAGER_PORT not set, please source openrc") && exit 1
test -z "$API_KEY" && (>&2 echo "error: API_KEY not set, please source openrc") && exit 1

# the target is either a cluster-id or a request for a list
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
list)
    # "list" was requested so return info about all clusters owned by accountid
    ### use curl "-s -S" to run in silent mode (skip the progress meter) but still return message when an error is encountered
    ### use curl "-f" to exit with RC 22 on failure rather than an html output with the error details
    curl -f -s -S $SSLPARMS -H "accept: application/json" -H "x-auth-token: ${token}" -o $tmpout -XGET https://${DBAASHOST}/api/v1/$accountid/services 
    if [ $? -ne 0 ]; then
       >&2 echo -e "error: Problem getting service-instance list"
       RC=1
    else
    else
       # instead of the full json, return a list (one cluster per line) with main details such as the cluster name and state
       cat $tmpout | jq -r '.services[] | [ .service.guid, .service.region_id, .service.account_id, .service.state, .service.name ] | join(" ")' 
    fi
    ;;
????????-????-????-????-????????????)
    # instead of "list", target string satisfies UUID format; treat as cluster-id and attempt API call to gather data for this specific cluster
    ### use curl "-s -S" to run in silent mode (skip the progress meter) but still return message when an error is encountered
    ### use curl "-f" to exit with RC 22 on failure rather than an html output with the error details
    curl -f -s -S $SSLPARMS -H "accept: application/json" -H "x-auth-token: ${token}" -o $tmpout -XGET https://${DBAASHOST}/api/v1/$accountid/services/${target}
    if [ $? -ne 0 ]; then
       >&2 echo -e "error: Problem getting service-instance info"
       RC=1
    else
       # the call worked so pass the output to jq for pretty json formatting
       cat $tmpout | jq -r .
    fi
    ;;
*)
    >&2 echo "error: unknown request '${target}'. Please specify 'list' or service-instance guid."
    RC=1
    ;;
esac
rm $tmpout

# pretty print
>&2 echo

exit $RC
