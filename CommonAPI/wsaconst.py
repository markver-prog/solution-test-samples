
WSA_CONST_VERSION = "1.1"  # Current version of the API contants

# logger name
HMC_API_LOGGER = "HMCLogger"
HMC_API_SHORT_LOGGER = "HMCLoggetShrt"

# check API Version during HMC logon or not to do it
CHECK_API_VERSION = False

# set current API version
API_VERSION = 1.1
API_VERSION = 1.2
import sys
WINDOWS_OS = sys.platform.startswith("win")

#############################################################################
# HMC Hosts
#############################################################################

# old
R93_HMC = "9.12.16.234"
R03_HMC = "9.12.16.242"
MR30_HMC = "9.12.16.253"
R90_HMC = "9.12.16.241"

# current
P93_HMC = "9.12.16.241"
P90_HMC = "9.12.16.253"
R01_HMC = "9.12.16.236"
HMCs = {'P93':P93_HMC,
        'R91':P93_HMC,
        'P91':P93_HMC,
        'P90':P90_HMC,
        'ZBX30':R01_HMC,
        'P95':R01_HMC}
HMC_API_SSL_port = 6794
HMC_API_port = 6167

#############################################################################
# User Authentication
#############################################################################
WSA_USERID            = ''
WSA_PASSWORD          = ''
WSA_DEFAULT_USERID    = ''
WSA_DEFAULT_PASSWORD  = ''

#############################################################################
# ActiveMQ
#############################################################################

WSA_ACTIVEMQ_PORT_NON_SSL = 61616

WSA_ACTIVEMA_PORT_SSL     = 61617



#############################################################################
# Virtualization host types
#############################################################################
ZVM_TYPE = 'zvm'
if API_VERSION < 1.1:
  X86_TYPE = 'x86'
else:
  X86_TYPE = 'x-hyp'
POWER_TYPE = 'power-vm'
PRSM_TYPE = 'prsm'
PRSM2_TYPE = 'prsm2'

# virtual server types
VS_POWER_TYPE = 'power-vm'
VS_X86_TYPE   = 'x-hyp'
VS_ZVM_TYPE   = 'zvm'
VS_PRSM_TYPE  = 'prsm'
VS_TYPES = [VS_POWER_TYPE, VS_X86_TYPE, VS_ZVM_TYPE, VS_PRSM_TYPE]

#############################################################################
# Blades' types
#############################################################################
POWER_BLADE_TYPE = 'power'
X86_BLADE_TYPE = 'system-x'

#############################################################################
# Virtual switches' types
#############################################################################
IEDN_SWITCH_TYPE = "virtual-iedn"
QDIO_SWITCH_TYPE = "virtual-qdio"


#############################################################################
# CPC constants
#############################################################################
CPC_NODE_TYPE = 'cpc'
CPC_STATUS_OPERATING = 'operating'
CPC_STATUS_SERVICE_REQUIRED = 'service-required'
CPC_STATUS_EXCEPTIONS = 'exceptions'
CPC_OPERATING_STATUSES = [CPC_STATUS_OPERATING]
# comment next line after R93 come back
CPC_OPERATING_STATUSES = [CPC_STATUS_OPERATING, CPC_STATUS_SERVICE_REQUIRED]
# comment next line after P93 will come back (Alexander Chepkasov: VSLifeCycle testing - 22/05/2012)
CPC_OPERATING_STATUSES = [CPC_STATUS_OPERATING, CPC_STATUS_EXCEPTIONS, CPC_STATUS_SERVICE_REQUIRED]

#############################################################################
# VS statuses
#############################################################################
VS_STATUS_OPERATING = 'operating'
VS_STATUS_NOT_OPERATING = 'not-operating'
VS_STATUS_NOT_ACTIVATED = 'not-activated'
VS_CAN_BE_DELETED_STATUSES = [VS_STATUS_NOT_OPERATING,VS_STATUS_NOT_ACTIVATED]

#############################################################################
# Job statuses
#############################################################################
JOB_STATUS_COMPLETE = 'complete'
JOB_STATUS_STOPPED = 'stopped'
JOB_STATUS_ACTIVE = 'active'

#############################################################################
# Storage resource statuses
#############################################################################
SR_ALLOCATION_STATUS_FREE = 'free'

#############################################################################
# Blade constants
#############################################################################
BLADE_STATUS_OPERATING    = 'operating'
BLADE_STATUS_NO_POWER     = 'no-power'
BLADE_STATUS_STATUS_CHECK = 'status-check'
BLADE_STATUS_STOPPED      = 'stopped'
BLADE_STATUS_DEF_ERROR    = 'definition-error'
BLADE_OPERATING_STATUSES  = [BLADE_STATUS_OPERATING,BLADE_STATUS_NO_POWER]
#BLADE_OPERATING_STATUSES  = [BLADE_STATUS_OPERATING,BLADE_STATUS_STATUS_CHECK]

#############################################################################
# Activate/deactivate constants
#############################################################################
JOB_OPERATION_TIMEOUT = 'job-operation-timeout'
FAILED_BLADES_DICT    = 'failed-blades-dict'
FAILED_VS_DICT        = 'failed-virtual-servers-dict'


#############################################################################
# Basic constants
#############################################################################
PROPERTY_DESCRIPTION_LENGTH = 1024


#############################################################################
# API URIs
#############################################################################

# Log onto an HMC
WSA_URI_LOGON   = '/api/session'

# Log off of an HMC
WSA_URI_LOGOFF  = '/api/session/this-session'

# Retrieve the API version
WSA_URI_VERSION = '/api/version'

# List all ensembles
WSA_URI_ENSEMBLES      = '/api/ensembles'

# Retrieve properties of a specific ensemble
WSA_URI_ENSEMBLE       = '/api/ensembles/{0}'

# Retrieve all CPCs
WSA_URI_CPCS           = '/api/cpcs'

# Job URI
WSA_URI_JOBS           = '/api/jobs/%s'

# Retrieve all virtualization hosts of a specific ensemble
WSA_URI_VIRT_HOSTS_ENS = '/api/ensembles/%s/virtualization-hosts'

# Retrieve all virtualization hosts of a specific cpc
WSA_URI_VIRT_HOSTS_CPC = '/api/cpcs/%s/virtualization-hosts'

# Retrieve all partitions of a specific cpc
WSA_URI_PARTITIONS_CPC = '/api/cpcs/%s/partitions'

# Retrieve all adapters of a specific cpc
WSA_URI_ADAPTERS_CPC = '/api/cpcs/%s/adapters'

# Retrieve all virtual switches of a specific cpc
WSA_URI_VIRTUAL_SWITCHES_CPC = '/api/cpcs/%s/virtual-switches'

# Retrieve all properties of a specific partition
WSA_URI_PARTITION   =     '/api/partitions/%s'

# Retrieve all NICs of a specific partition
WSA_URI_NICS_PARTITION = '/api/partitions/%s/nics'

# Retrieve all properties of a specific NIC
WSA_URI_NIC = '/api/partitions/%s/nics/%s'

# Retrieve all HBAs of a specific partition
WSA_URI_HBAS_PARTITION = '/api/partitions/%s/hbas'

# Retrieve properties of a specific HBA
WSA_URI_HBA = '/api/partitions/%s/hbas/%s'

# Retrieve properties of a specific storage port
WSA_URI_STORAGE_PORT = '/api/adapters/%s/storage-ports/%s'

# Retrieve all properties of a specific virtualization host
WSA_URI_VIRT_HOST      = '/api/virtualization-hosts/%s'

# Retrieve all virtual servers of a specific virtualization host
WSA_URI_VIRT_SERVERS_OF_VIRT_HOST = '/api/virtualization-hosts/%s/virtual-servers'

# Retrieve all virtual switches of a specific z/VM virtualization host
WSA_URI_VIRTUAL_SWITCHES = '/api/virtualization-hosts/%s/virtual-switches'

# Retrieve properties of a specific zBX
WSA_URI_ZBX            = '/api/zbxs/%s'

# Retrieve properties of a specific blade
WSA_URI_BLADE          = '/api/blades/%s'

# Retrieve properties of a specific blade center
WSA_URI_BLADECNTR='/api/bladecenters/%s'

# Retrieve properties of a specific virtual server
WSA_URI_VIRT_SERVER    = '/api/virtual-servers/%s'

# Virtual disk of a specific virtual server
WSA_URI_VIRT_DISK      = '/api/virtual-servers/%s/virtual-disks'

# Create network adapter for a specific virtual server
WSA_URI_VS_NETWORK_ADAPTER = '/api/virtual-servers/%s/network-adapters'

# Network adapter URI for a specific virtual server
WSA_URI_VS_NA_PROPERTIES = '/api/virtual-servers/%s/network-adapters/%s'

# Retrieve properties of a specific virtual network
WSA_URI_VIRT_NETWORK   = '/api/virtual-networks/%s'

# Retrieve nodes of a specific ensemble
WSA_URI_ENSEMBLE_NODES = '/api/ensembles/%s/nodes'

# Retrieve properties of a specific ensemble
WSA_URI_ENSEMBLE_PROPERTIES = '/api/ensembles/%s'

# Retrieve properties of a specific node and ensemble
WSA_URI_NODE_PROPERTIES = '/api/ensembles/%s/nodes/%s'

# Retrieve properties of a specific workload
if API_VERSION < 1.2:
  WSA_URI_WKLD_PROPERTIES = '/api/workloads/%s'
else:
  WSA_URI_WKLD_PROPERTIES = '/api/workload-resource-groups/%s'

# workloads URI
if API_VERSION < 1.2:
  WSA_URI_WORKLOADS = '/api/workloads/'
else:
  WSA_URI_WORKLOADS = '/api/workload-resource-groups/'

# Retrieve properties of a specific storage resource
WSA_URI_SR_PROPERTIES = '/api/storage-resources/%s'

# Retrieve list of ZBXs for a specific CPC
WSA_URI_LIST_ZBXS_OF_CPC = '/api/cpcs/%s/zbxs'

# Retrieve list of ZBXs for a specific ensemble
WSA_URI_LIST_ZBXS_OF_ENSEMBLE = '/api/ensembles/%s/zbxs'

# Retrieve list of blade centers for a specific ZBX
WSA_URI_LIST_BLADECENTERS = '/api/zbxs/%s/bladecenters'

# Retrieve list of blades for a specific ZBX
WSA_URI_LIST_BLADES = '/api/zbxs/%s/blades'

# Retrieve list of blades for a specific BladeCenter
WSA_URI_LIST_BC_BLADES = '/api/bladecenters/%s/blades'

# Retrieve list of workloads for a specific ensemble
if API_VERSION < 1.2:
  WSA_URI_LIST_WORKLOADS = '/api/ensembles/%s/workloads'
else:
  WSA_URI_LIST_WORKLOADS = '/api/ensembles/%s/workload-resource-groups'

# Retrieve list of workload element groups for a specific ensemble
WSA_URI_WKLD_ELEMENT_GROUPS_OF_ENSEMBLE = '/api/ensembles/%s/workload-element-groups'

# Retrieve properties of a specific workload element group
WSA_URI_WKLD_ELEMENT_GROUP_PROPERTIES = '/api/workload-element-groups/%s'

# Get Element Group Properties
WSA_URI_ELEMENT_GROUP_PROPERTIES = '/api/element-groups/%s'

# Get Workload Element Group Properties
WSA_URI_WORKLOAD_ELEMENT_GROUP_PROPERTIES = '/api/workload-element-groups/%s'
# Retrieve list of virtual networks for a specific ensemble
WSA_URI_LIST_VIRT_NETWORKS = '/api/ensembles/%s/virtual-networks'

# Retrieve list of storage resources for a specific virtualization host
WSA_URI_LIST_VHSR = '/api/virtualization-hosts/%s/virtualization-host-storage-resources'

# Retrieve properties of a specific virtualization host storage resource
WSA_URI_VHSR_PROPERTIES = '/api/virtualization-hosts/%s/virtualization-host-storage-resources/%s'

# Retrieve list of storage groups for a specific virtualization host
WSA_URI_LIST_VHSG = '/api/virtualization-hosts/%s/virtualization-host-storage-groups'

# Retrieve properties of a specific virtualization host storage group
WSA_URI_VHSG_PROPERTIES = '/api/virtualization-hosts/%s/virtualization-host-storage-groups/%s'

# Retrieve list of storage resources for a specific ensemble
WSA_URI_LIST_SR = '/api/ensembles/%s/storage-resources'

# Retrieve all virtual servers of a specific ensemble
WSA_URI_VIRT_SERVERS_OF_ENSEMBLE = '/api/ensembles/%s/virtual-servers'

# Retrieve properties of a specific zBX and TORs
WSA_URI_TORS_PROPERTIES = '/api/zbxs/%s/top-of-rack-switches/%s'
WSA_URI_ZBX_TORS_PROPERTIES = '/api/zbxs/%s/top-of-rack-switches/%s'

# Workload Resource Groups Report
WSA_URI_WORKLOADS_REPORT = '/api/ensembles/%s/performance-management/operations/generate-workload-resource-groups-report'

# Service Classes Report
WSA_URI_SERVICE_CLASSES_REPORT = '/api/ensembles/%s/performance-management/operations/generate-service-classes-report'

# Service Class Hops Report
WSA_URI_SERVICE_CLASS_HOPS_REPORT = '/api/ensembles/%s/performance-management/operations/generate-service-class-hops-report'

# Load Balancing Report
WSA_URI_LOAD_BALANCING_REPORT = '/api/ensembles/%s/performance-management/operations/generate-load-balancing-report'

# Mount Virtual Media Image
WSA_URI_MOUNT_VIRTUAL_MEDIA_IMAGE = '%s/operations/mount-virtual-media-image'
# Mount Virtual Media
WSA_URI_MOUNT_VIRTUAL_MEDIA = '%s/operations/mount-virtual-media'
# Unmount Virtual Media Image
WSA_URI_UNMOUNT_VIRTUAL_MEDIA = '%s/operations/unmount-virtual-media'

# Retrieve all virtual functions upon a partition
WSA_URI_VIRT_FUNCS_PARTITION = '/api/partitions/%s/virtual-functions'

# Add more elements to an existing (empty or non-empty) crypto configuration
WSA_URI_INCREASE_CRYPTO_CONFIGURATION = '/api/partitions/%s/operations/increase-crypto-configuration'

# For storage group
WSA_URI_LIST_STORAGE_GROUP = '/api/storage-groups'

WSA_URI_STORAGE_GROUP_PROPERTIES = '/api/storage-groups/%s'

WSA_URI_LIST_STORAGE_VOLUME = '/api/storage-groups/%s/storage-volumes'

WSA_URI_ATTACH_STORAGE_GROUP = '/api/partitions/%s/operations/attach-storage-group'

WSA_URI_LIST_VIRTUAL_STORAGE_RESOURCES = '/api/storage-groups/%s/virtual-storage-resources'

WSA_URI_REQUEST_STORAGE_GROUP_FULFILLMENT = '/api/storage-groups/%s/operations/request-fulfillment'
#############################################################################
# Testcase exit return codes
#############################################################################

# Exit return code for successful testcase execution
WSA_EXIT_SUCCESS = 0

# Exit return code for an API error
WSA_EXIT_ERROR_API = 1

# Exit return code for an unexpected error such as a communication failure
WSA_EXIT_ERROR_UNCAUGHT = 2


#############################################################################
# zExtension-related API URIs
#############################################################################

# Retrieve list of zExtensions for a specific ensemble
WSA_URI_LIST_ZEXT_OF_ENSEMBLE = '/api/ensembles/%s/z-extensions'

# Retrieve all virtualization hosts of a zExtensions
WSA_URI_VIRT_HOSTS_ZEXT = '/api/z-extensions/%s/virtualization-hosts'

# Retrieve Compute Elements of zExtensions list
WSA_URI_LIST_CE_OF_ZEXT = '/api/z-extensions/%s/compute-elements'

# Retrieve properties of a specific CE
WSA_URI_CE          = '/api/compute-elements/%s'


#############################################################################
# CEs' types
#############################################################################
POWER_CE_TYPE = 'power'
X86_CE_TYPE   = 'system-x'
DP_XI50_TYPE  = 'dpxi50z'



#############################################################################
# Compute element statuses
#############################################################################
CE_STATUS_OPERATING    = 'operating'
CE_STATUS_NO_POWER     = 'no-power'
CE_STATUS_STATUS_CHECK = 'status-check'
CE_STATUS_STOPPED      = 'stopped'
CE_STATUS_DEF_ERROR    = 'definition-error'
CE_STATUS_SERVICE      = 'service'
CE_OPERATING_STATUSES  = [CE_STATUS_OPERATING,CE_STATUS_NO_POWER]

# Retrieve properties of a specific TOR of zExtension
WSA_URI_Z_EXT_TORS_PROPERTIES = '/api/zbxs/%s/top-of-rack-switches/%s'

#############################################################################
# zExtension statuses
#############################################################################
Z_EXT_STATUS_OPERATING = 'operating'
Z_EXT_STATUS_NOT_COMMUNICATING = 'not-communicating'
Z_EXT_STATUS_EXCEPTIONS = 'exceptions'
Z_EXT_STATUS_STATUS_CHECK = 'status-check'
Z_EXT_STATUS_NO_POWER = 'no-power'
Z_EXT_STATUS_SERVICE = 'service'
Z_EXT_STATUS_SERVICE_REQUIRED = 'service-required'
Z_EXT_OPERATING_STATUSES = [Z_EXT_STATUS_OPERATING,Z_EXT_STATUS_EXCEPTIONS]


#############################################################################
# HTTP Request and Response
#############################################################################

# Non-SSL HTTP Port ... need HTTPConnection ...
WSA_PORT_NON_SSL = 6167

# SSL HTTP Port ... needs HTTPSConnection ...
WSA_PORT_SSL     = 6794

# HTTP GET command
WSA_COMMAND_GET    = 'GET'

# HTTP DELETE command
WSA_COMMAND_DELETE = 'DELETE'

# HTTP POST command
WSA_COMMAND_POST   = 'POST'

# HTTP PUT command
WSA_COMMAND_PUT    = 'PUT'

# Header for content type ... both request and response
WSA_HEADER_CONTENT    = 'content-type'

# Header for API session ... request header only
WSA_HEADER_RQ_SESSION = 'x-api-session'

# Header for API session ... response header only
WSA_HEADER_RS_SESSION = 'api-session'

WSA_CONTENT_JSON = 'application/json'
WSA_CONTENT_XML  = 'application/xml'
WSA_CONTENT_ZIP  = 'application/zip'

# Currently supported content types
WSA_SUPPORTED_CONTENT = [ WSA_CONTENT_JSON, WSA_CONTENT_XML, WSA_CONTENT_ZIP ]


#############################################################################
# Response Validation
#############################################################################

STATUS       = 'status'
CONTENT_TYPE = 'content-type'
REQUIRED     = 'required'
OPTIONAL     = 'optional'

STATUS_200     = ( STATUS, 200 )
STATUS_201     = ( STATUS, 201 )
STATUS_202     = ( STATUS, 202 )
STATUS_204     = ( STATUS, 204 )
CONTENT_JSON   = ( CONTENT_TYPE, WSA_CONTENT_JSON )
REQUIRED_EMPTY = ( REQUIRED, [] )
OPTIONAL_EMPTY = ( OPTIONAL, [] )


# Logon and Version #########################################################

__ver_required       = ( REQUIRED, [ 'api-major-version', 'api-minor-version', 'hmc-name', 'hmc-version' ] )
__logon_required     = ( REQUIRED, [ 'api-major-version', 'api-minor-version', 'api-session', 'notification-topic' ] )

# Validate response from 'Get Version' operation
WSA_VERSION_VALIDATE   = dict( [ STATUS_200, CONTENT_JSON, __ver_required,   OPTIONAL_EMPTY ] )

# Validate response from 'Logon' operation
WSA_LOGON_VALIDATE     = dict( [ STATUS_200, CONTENT_JSON, __logon_required, OPTIONAL_EMPTY ] )


# Ensembles #################################################################

__list_ensembles_required = ( REQUIRED, [ 'ensembles' ] )

__get_ensemble_required   = ( REQUIRED, [ 'acceptable-status',
                                            'class',
                                            'cpu-perf-mgmt-enabled-power-vm',
                                            'cpu-perf-mgmt-enabled-zvm',
                                            'description',
                                            'has-unacceptable-status',
                                            'is-locked',
                                            'mac-prefix',
                                            'management-enablement-level',
                                            'name',
                                            'object-id',
                                            'object-uri',
                                            'parent',
                                            'power-consumption',
                                            'power-rating',
                                            'reserved-mac-address-prefixes',
                                            'status',
                                            'unique-local-unified-prefix' ] )

__get_ensemble_optional   = ( OPTIONAL, [ 'alt-hmc-name',
                                            'alt-hmc-ipv4-address',
                                            'alt-hmc-ipv6-address',
                                            'load-balancing-enabled',
                                            'load-balancing-ip-addresses',
                                            'load-balancing-port' ] )

# Validate response from 'List Ensembles' operation
WSA_LIST_ENSEMBLES_VALIDATE = dict( [ STATUS_200, CONTENT_JSON, __list_ensembles_required, OPTIONAL_EMPTY ] )

# Required keys for each ensemble returned by 'List Ensembles' operation
WSA_LIST_ENSEMBLE_REQUIRED  = [ 'name', 'object-uri', 'status' ]

# Validate response from 'Get Ensemble Properties' operation
WSA_GET_ENSEMBLE_VALIDATE   = dict( [ STATUS_200, CONTENT_JSON, __get_ensemble_required,   __get_ensemble_optional ] )


# CPCs ######################################################################

__list_cpcs_required = ( REQUIRED, [ 'cpcs' ] )

# Validate response from 'List CPCs' operation
WSA_LIST_CPCS_VALIDATE = dict( [ STATUS_200, CONTENT_JSON, __list_cpcs_required, OPTIONAL_EMPTY ] )

# Required keys for each cpc returned by 'List CPCs' operation
WSA_LIST_CPC_REQUIRED  = [ 'name', 'object-uri', 'status' ]


# Virtualization Hosts ######################################################

__list_virt_hosts_required = ( REQUIRED, [ 'virtualization-hosts' ] )

# Validate response from 'List Virtualization Hosts' operation
WSA_LIST_VIRT_HOSTS_VALIDATE = dict( [ STATUS_200, CONTENT_JSON, __list_virt_hosts_required, OPTIONAL_EMPTY ] )

# Required keys for each virtualization host returned by 'List Virtualization Hosts' operation
WSA_LIST_VIRT_HOST_REQUIRED  = [ 'name', 'object-uri', 'status', 'type' ]

# Mitrics util
KEY_METRIX_CNTX_URI = 'Metrix-context'
KEY_METRIX_GROUP_INF = 'Metrix-Group-infs'

# Shell commands for Middleware

commandsIhs = ['/opt/IBM/HTTPServer/bin/apachectl stop',
                '/opt/IBM/IHS85/bin/apachectl stop',
                '/WAS85prod/IHS85/bin/apachectl stop',
                '/opt/IBM/HTTPServer/bin/apachectl start',
                '/opt/IBM/IHS85/bin/apachectl start',
                '/WAS85prod/IHS85/bin/apachectl start',
                'curl -I http://localhost']
commandsWasIsRun = ['/opt/IBM/WebSphere/AppServer/profiles/AppSrv01/bin/serverStatus.sh server1 -user wsadmin -password passw0rd',
                '/opt/wasprofile/AppSrv01/bin/serverStatus.sh server1 -user wsadmin -password passw0rd']
commandsWas = ['/opt/IBM/WebSphere/AppServer/profiles/AppSrv01/bin/stopServer.sh server1 -user wsadmin -password passw0rd',
               '/opt/wasprofile/AppSrv01/bin/stopServer.sh server1 -user wsadmin -password passw0rd',
               '/opt/IBM/WebSphere/AppServer/profiles/AppSrv01/bin/startServer.sh server1 -user wsadmin -password passw0rd',
               '/opt/wasprofile/AppSrv01/bin/startServer.sh server1 -user wsadmin -password passw0rd']
commandsDb2 = ['su - db2inst1 -c \\"db2pd -dbptnmem\\"',
               'su - db2inst1 \\"-c db2 force application all\\"',
               'su - db2inst1 \\"-c db2 terminate\\"',
               'su - db2inst1 \\"-c db2stop\\"',
               'su - db2inst1 \\"-c db2stop force\\"',
               'su - db2inst1 \\"-c db2start\\"']
commandsGrepJmeter = ['ps -ef | grep jmeter']
commandsStopJmeter = ['pkill -f jmeter', '/opt/IBM/Jmeter/jakarta-jmeter-2.3.4/bin/shutdown.sh']
commandsGpmp = ['su ibmgpmp -c \\"/opt/ibm/gpmp/gpmp\\"']
startGpmpCode1='FEW6040I'
startGpmpCode2='FEW6038I'
