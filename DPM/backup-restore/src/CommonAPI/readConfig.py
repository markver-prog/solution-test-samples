#! /usr/bin/env python

# ------------------------------------------------------------------ #
# - This script loads data from configuration file
# - (.cfg - the same as ini file)
# - and statuses of its VSs (for x86 and POWER blades)
# - If there exist configuration (.cfg) file, the script loads
# - configuration data from this file
# ------------------------------------------------------------------ #
# @author: Alexander P. Chepkasov, RSTL, Jan 2012
# ------------------------------------------------------------------ #


# imports
import ConfigParser


#############################################################################
# Sections/options names for configuration files
#############################################################################
VS_TYPE_OPTION = 'vs-type'
VS_NAME_OPTION = 'vs-name'
COMMON_SECTION = 'common'
LOGGING_SECTION = 'logging'


# ------------------------------------------------------------------ #
# --------- Start of readConfig function --------------------------- #
# ------------------------------------------------------------------ #
# - Loads configuration data from .cfg file
# ------------------------------------------------------------------ #
def readConfig(
    fileName   # .cfg file name (full path or short name)
):
    '''
      Loads configuration data from .cfg file

      - @param fileName: file name (full or short path to .cfg file)
      - @return: dictionary of sections data. It has following structure:
                 {<section name> : <section data>,
                  <section name> : <section data>, ...}, where
                         <section data> = {<option name>: <option value>,
                                           <option name>: <option value>, ...}
    '''
    optDict = dict()
# check None file name => generate IOError exception
    if fileName == None:
        exc = IOError("Empty file or directory name")
        exc.errno = 2
        raise exc
    config = ConfigParser.ConfigParser()
    config.readfp(open(fileName))
    sections = config.sections()
# walk through sections
    for section in sections:
        sectDict = dict()
        items = config.items(section)
        for option, values in items:
            values = (config.get(section, option)).split(',')
        # remove white spaces
            i = 0
            while i < len(values):
                values[i] = values[i].strip()
                if values[i] == '':
                    del values[i]
                else:
                    i += 1
            sectDict[option] = values
        optDict[section] = sectDict
    return optDict
# ------------------------------------------------------------------ #
# --------- End of readConfig function ----------------------------- #
# ------------------------------------------------------------------ #
