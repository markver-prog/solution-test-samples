#### Sample scripts for interfacing with dbaas-manager API:

1. dbaasServices.sh 
```
usage: dbaasServices.sh <list|cluster-id> [cert-file]
ex:    dbaasServices.sh list /path/to/ca/cert.pem
ex:    dbaasServices.sh 2e3b8dc8-72b1-4f64-8eb4-123456543210 /path/to/ca/cert.pem
```

2. dbaasClusterInfo.sh 
```
usage: dbaasClusterInfo.sh <cluster-id> [cert-file]
ex:    dbaasClusterInfo.sh 2e3b8dc8-72b1-4f64-8eb4-012345654321 /path/to/ca/cert.pem
```

#### Executing the scripts

Create and source an openrc file with the dbaas-manager connection info.

For details on the dbaas-manager connection, check the IBM Cloud documentation for the DB type, ex:
- [API docs for hyperp-dbaas-mongodb](https://cloud.ibm.com/docs/services/hyper-protect-dbaas-for-mongodb?topic=hyper-protect-dbaas-for-mongodb-gen_inst_mgr_apis)
- [API docs for hyperp-dbaas-postgresql](https://cloud.ibm.com/docs/services/hyper-protect-dbaas-for-postgresql?topic=hyper-protect-dbaas-for-postgresql-gen_inst_mgr_apis)

Example openrc:
```
# cat openrc
export DBAAS_MANAGER_IP=dbaas900.hyperp-dbaas.cloud.ibm.com
export DBAAS_MANAGER_PORT=20000
export API_KEY=01010101010101010101010101010101010101010101
#
# source openrc
```

Sourcing the file enables executing the commands within the current shell environment.
So variables remain defined within the shell instead of going away with the execution environment.

For example after doing the source, the exported variables should still be defined, ex:
```
# echo $DBAAS_MANAGER_IP
dbaas900.hyperp-dbaas.cloud.ibm.com
# echo $DBAAS_MANAGER_PORT
20000
# echo $API_KEY
01010101010101010101010101010101010101010101
```

Download the CA certificate from the UI of an existing hyperp-dbaas service instance.

Look on the right of the overview tab where it says:

> <b>Connect to Database</b> <br>
> <hr>
> To ensure secure data transfer, obtain a certificate authority (CA) file here.

And use the link to download the certificate.

Run the dbaasServices.sh "list" instruction to get a listing of service-instances, ex:
```
#./dbaasServices.sh list /path/to/cert.pem 
10000000-0000-0000-0000-000000000001 us-south 10000000000000000000000000000001 active mycluster01
20000000-0000-0000-0000-000000000002 us-south 10000000000000000000000000000001 active mycluster02
#
```

Run the dbaasClusterInfo.sh to get specific data about one cluster, ex:
```
# ./dbaasClusterInfo.sh 10000000-0000-0000-0000-000000000001 /path/to/cert.pem
{
  "region": "us-south",
  "user_id": "10000000000000000000000000000001",
  "name": "mycluster01",
...
```
