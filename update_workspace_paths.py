# Open MXD and open arcpy window
# Copy/paste code in python window
# Remember to refresh layer then save map

import arcpy
mxd = arcpy.mapping.MapDocument("CURRENT")
mxd.replaceWorkspaces("", "", r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataReader@FM-GISSQLHA_DEFAULT_VERSION.sde", "SDE_WORKSPACE")


import arcpy
mxd = arcpy.mapping.MapDocument("CURRENT")
mxd.replaceWorkspaces("", "", r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@FM-GISSQLHA_DEFAULT_VERSION.sde", "SDE_WORKSPACE")
