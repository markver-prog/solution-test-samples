#!/bin/bash
#
# This is useful if you have a lot of service-instances and want to 
# filter out hyperp-dbaas related service-instances for both DB types
#
# Notes:
# - this script expects "ibmcloud login ..." has already been performed
# - requires jq filter or equivalent json parser
# 

# The jq parser outputs each value on its own line.
# Using the following function we can cycle through the jq output to
# 1. parse out the cluster ID, location, and service type from the crn value.
# 2. convert service-instance names that contain white space to ones with
#    underscore to allow for easier column formatting.
# 3. concatenate the results to one line per service-instance for display.
#
function serviceLine {
   while read line; do
      # Use the first 4 characters of the jq output to determine handling
      case ${line:0:4} in
      "crn:")
        # The crn is a list of values separated by ":" pull out 8th, 5th, and 6th
        # value which are the cluster-id, service type, and location, respectively.
        value="$(echo $line | sed 's/:/ /g' | awk '{print  $8,$5,$6}')"
        echo -n "$value "
        ;;
      "acti"|"inac")
        # The state is either "active" or "deactive"
        if [ "$line" == "active" -o "$line" == "inactive" ]; then
           value="$line"
           echo -n "$value "
        else
           # This handles the special case where a service-instance name
           #   starts with either "acti" or "inac"; unlikely but possible.
           # As the final value of the jq output for a service-instance,
           #   display the value without any additional white space after.
           value="$(echo "$line" | sed 's/ /_/g')"
           echo $value
        fi
        ;;
      *)
        # Value did not start with "crn:" or "acti" or "inac" so value is not
        # a crn string nor a state status.  Value must be a service-instance name.
        value="$(echo "$line" | sed 's/ /_/g')"
        echo $value
        ;;
      esac
   done
}
      
# Filter out both DB types and re-display in columns according to 
# cluster-id, DB type, location, state, and name.
# Pass to the column command for pretty formatting.
{ echo "ID DBtype Location State Name";
  ibmcloud resource service-instances --service-name hyperp-dbaas-mongodb    --output json | jq -r '.[] | .crn, .state, .name' | serviceLine; 
  ibmcloud resource service-instances --service-name hyperp-dbaas-postgresql --output json | jq -r '.[] | .crn, .state, .name' | serviceLine; 
} | column -t
