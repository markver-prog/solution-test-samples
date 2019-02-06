### Prerequisites
HMC version should be equal or above 2.14.1 with DPM-mode enabled, and DPM version should be equal or above R3.1.
Besides, the logon account to be used to logon HMC should have the API Access Control enabled (Customize API Setting task -> Web Services Tab -> check the checkbox in the Access Control table)
### Usage
This script tool includes 4 sections, backup/restore storage groups and backup/restore partitions. For the backup action, it's no matter we start with the partitions or the storage groups, which will generate one partition config file and one storage group config file containing the configure information, both are readable and editable.

The partition configures information include partition name, description, type, status, processor information (type, mode and number), initial memory, maximum memory, Network Interface Cards information (adapter name, port, description and device number), Storage Groups information (storage group name, type and device number), accelerator and crypto information.

The storage group configure information include storage group name, type (FCP or FICON), description, shareability, max number of partitions, path number, and volume information (volume type, size and description)

When in the restore stage, after the roll is complete and the CEC is powered back up and in DPM Mode, storage admin will configure the FICON and FCP environment (Storage Cards Tab and FICON Connections Tab), then, you could run the restore storage group script for the storage groups. After that, storage admin will configure the switches and storage controller with the new WWPN's and fulfill the storage groups to make them to Complete state. (At least, fulfill the storage groups which need to be attached to partitions, it is forbidden for the storage groups attachment action which are not in the Complete state).

Double check the partition config file, confirm the adapter IDs in the config file are existing in the new system, if not, replace the adapter IDs in config file with the new IDs in the system (it would be great if there has a new PCHID mapping table).

The last step would be run the script to restore the partitions. It would be shown in the trace if any operation failed, like attach storage group failed or set boot option failed. It might because the adapter ID couldn't be found, or the partition name already exist in the system, you could do it manually when the script finished.

Open the partition details page, confirm all parameters are set correct, especially the device numbers for each device and the boot option section. Now, I think it's the time to start the partition.
### Options
The user should specify the following input parameters for the scripts, use -h for details information for each script command
```
--hmcHost, -hmc: <IP address or hostname of the HMC>
--cpcName, -cpc: <CPC name>
--userId, -uid: <userid on that HMC>
--password, -psw: <password of that HMC userid>
--backupDir, -bakDir: [backup config file directory, the same directory with the script file if omit this parameter]
--configFile, -config: [specify the config file, use either the relative or absolute path]
--emailList, -email: [email list whom will receive the storage group request mail notification, split with comma, no quotation mark and blank]
```
### Quickstart
The following example command backs up the storage groups in M90 to M90-sgBackup directory:
```
$ python sgBackup.py -hmc 9.12.*.* -cpc M90 -uid *** -psw *** -bakDir M90-sgBackup
```
Possible output when running the command:
```
*****************************************************
Back up all Storage Groups on specified CPC
	Parameters were input:
	HMC system IP	9.12.*.*
	CPC name	M90
	Backup Directory --> M90-sgBackup
*****************************************************
[M90_FICON_Boot_SG] -> fc storage group backup is Done.
[M90_FCP_Dedicated_SG] -> fcp storage group backup is Done.
...
Above 35 Storage-Groups on M90 were saved into below file successfully.
M90-sgBackup/M90-StorGroups-20181212-102822.cfg
```
The following example command backs up the partition in M90 to M90-parsBackup directory:
```
$ python parsBackup.py -hmc 9.12.*.* -cpc M90 -uid *** -psw *** -bakDir M90-parsBackup
```
Possible output when running the command:
```
********************************************************
Back up basic configs for all partitions on specified CPC
	Parameters were input:
	HMC system IP	9.12.*.*
	CPC name	M90
	Backup Directory --> M90-parsBackup
********************************************************
M90-LNXT01 backup is Done.
M90-LNXT02 backup is Done.
...
M90 partitions' configuration were saved in below file successfully.
M90-parsBackup/M90-Partitions-20181212-104344.cfg
```
The following example command restores the storage groups in M90 from the config file M90-StorGroups-20181212-102822.cfg
```
$ python sgRestore.py -hmc 9.12.*.* -cpc M90 -uid *** -psw *** -config M90-sgBackup/M90-StorGroups-20181212-102822.cfg -email ***@ibm.com
```
Possible output when running the command:
```
>>> parsing the input parameters...
>>> loading the config file...
>>> Creating HMC connection...
>>> HMC connection created!
>>> Constructing Storage Group: M90_FICON_Dedicated_SG...
>>> Constructing Storage Group: M90_Shared_Testing_SG...
Here are the storage group(s) been created successfully: ['M90_FICON_Dedicated_SG', 'M90_Flash_Shared_Testing_SG']
Script run completed!!!
```
The following example command restores the partitions in M90 from the config file M90-Partitions-20181212-104344.cfg
```
$ python parsRestore.py -hmc 9.12.*.* -cpc M257 -uid *** -psw *** -config M90-parsBackup/M90-Partitions-20181212-104344.cfg
```
Possible output when running the command:
```
>>> parsing the input parameters...
>>> loading the config file...
>>> Creating HMC connection...
>>> HMC connection created!
>>> Creating partition: M90-Test-Part-I...
>>> Creating partition: M90-Test-Part-II...
>>> Create vNIC for M90-Test-Part-I successfully: M90-Test-Part-I-10dot-mgmt
>>> Construct storage group for M90-Test-Part-I successfully: M90_B020_FICON_Boot_SG
>>> Set boot option for M90-Test-Part-I successfully!!!
>>> Create vNIC for M90-Test-Part-II successfully: M90-Test-Part-II-vlan1292
>>> Construct storage group for M90-Test-Part-II successfully: M90_B021_FICON_Data_SG
>>> Set boot option for M90-Test-Part-II successfully!!!
Here are the partition(s) been created successfully: ['M90-Test-Part-I', 'M90-Test-Part-II']
Script run completed!!!
```
