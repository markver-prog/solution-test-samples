#!/bin/bash
#
# Notes:
# - this script expects "ibmcloud login ..." has already been performed
# - it also expects a resource group has been defined (ie. 'ibmcloud target -g YOUR_RESOURCE_GROUP').
#   Try executing "ibmcloud resource groups" for details.
#

# verify number of arguments passed in
if [ $# -lt 4 ]; then
   echo "usage: $(basename $0) <region,ex:us-south,eu-de,au-syd> <cluster-name> <dbadmin> <dbpass> [service-plan]"
   echo "ex:    $(basename $0) us-south cluster01 misterAdmin testing123AbcXyz postgresql-free"
   exit 1 
fi

### get args (set the region to lower case to simplify later checks)
target="$(echo $1 | tr '[:upper:]' '[:lower:]')"
clname=$2
cluser=$3
clpass=$4
if [ -n "$5" ]; then 
   # If needed run "ibmcloud catalog service $catalogname | grep plan" to see available plans.
   # ex:
   #  $ ibmcloud catalog service hyperp-dbaas-mongodb | grep plan | cut -c 1-100 | sed 's/^.*mongodb/mongodb/'
   #   mongodb-free                   plan         ecf07f9f-3d75-4fd8-8074-876ee07b07cf 
   #   mongodb-large                  plan         b58c564f-7bec-4e6e-85ee-ec9206f6c9c5 
   #   mongodb-medium                 plan         98e2ea9f-1668-4e67-a931-4ddfbbdea50c 
   #   mongodb-small                  plan         25a5357c-4c91-4afc-a112-2f23e2141f78 
   #  $ ibmcloud catalog service hyperp-dbaas-postgresql | grep plan | cut -c 1-100 | sed 's/^.*postgresql/postgresql/'
   #   postgresql-free                  plan         ab547763-605f-4d83-a52e-f646249c8f8
   #   postgresql-large                 plan         15f5d677-e423-459d-9128-53a9b4146b2
   #   postgresql-medium                plan         c979c2c2-1d67-4ea5-8a23-a42db1ba93b
   #   postgresql-small                 plan         9d357858-7210-48fc-9e6b-f45909ac382
   #
   srvplan="$5"
else
   # set this plan by default
   if [ -z "$srvplan" ]; then
      srvplan="mongodb-free"
   fi
fi

### select a catalog entry based on the requested plan name
if [ "${srvplan:0:10}" = "postgresql" ]; then
   # set catalog target to the postgresql type service
   catalogname="hyperp-dbaas-postgresql"
elif [ "${srvplan:0:7}" = "mongodb" ]; then
   # set to mongodb type 
   catalogname="hyperp-dbaas-mongodb"
else
   echo "error: unsupported service plan \"${srvplan}\""
   echo "Please search for hyperp-dbaas-postgresql or hyperp-dbaas-mongodb "
   echo " in the ibmcloud catalog and display entry to list available plans."
   exit 1
fi

### sanitize the region passed in (only allow use in the listed regions)
case $target in
us-south|eu-de|au-syd)
   region="$target"
   ;;
*)
   echo "error: unknown region \"${target}\"." 
   exit 1
   ;;
esac

### check if we have everything we need: user should source config file if needed
test -z "$clname" &&  echo "error: clname not set." && exit 1
test -z "$cluser" &&  echo "error: cluser not set." && exit 1
test -z "$clpass" &&  echo "error: clpass not set." && exit 1
test -z "$catalogname" &&  echo "error: catalogname not set." && exit 1
test -z "$region"      &&  echo "error: region not set." && exit 1
test -z "$srvplan"     &&  echo "error: srvplan not set." && exit 1

### create DBaaS service-instance based on the provided paramaters
echo ibmcloud resource service-instance-create $clname "$catalogname" "$srvplan" "$region" -p '{ blah blah blah json }'
ibmcloud resource service-instance-create $clname "$catalogname" "$srvplan" "$region" -p '{ "name":"'$clname'", "admin_name":"'$cluser'", "password":"'$clpass'", "confirm_password":"'$clpass'", "license_agree":["agreed"]}'
