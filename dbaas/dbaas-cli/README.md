#### Sample scripts for working with DBaaS service instances via the ibmcloud CLI.

1. dbaascli_create_instance.sh <br>
<b>Description:</b> create a service-instance for hyperp-dbaas-mongodb or hyperp-dbaas-postgresql service
based on the provided service-plan.  
```
usage: dbaascli_create_instance.sh <region ex:us-south,eu-de,au-syd> <cluster-name> <dbadmin> <dbpass> [service-plan]
ex:    dbaascli_create_instance.sh us-south cluster01 misterAdmin testing123AbcXyz postgresql-free
```

2. dbaascli_filter_instances.sh <br>
<b>Description:</b> list service-instances for both hyperp-dbaas-mongodb or hyperp-dbaas-postgresql services
along with the associated cluster-id/guid for each instance.  No arguments needed.


#### Executing the scripts

To use the scripts first log in to ibm cloud, ex:
```
# ibmcloud login -a https://cloud.ibm.com --apikey 01010101010101010101010101010101010101010101
```

Make sure to also set your resource group, ex:
```
# ibmcloud target -g "Default"
```

Run the create script, ex:
```
# ./dbaascli_create_instance.sh us-south mycluster01 myDBadmin adminPass123ABC mongodb-small
# ./dbaascli_create_instance.sh us-south mycluster02 myDBadmin adminPass123ABC postgresql-small
```

Run the script to list instances, ex:
```
# ./dbaascli_filter_instances.sh
ID                                    DBtype                   Location  State   Name
10000000-0000-0000-0000-000000000001  hyperp-dbaas-mongodb     us-south  active  mycluster01
20000000-0000-0000-0000-000000000002  hyperp-dbaas-postgresql  us-south  active  mycluster02
```
