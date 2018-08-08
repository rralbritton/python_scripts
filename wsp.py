import arcpy
mxd = arcpy.mapping.MapDocument("CURRENT")
mxd.replaceWorkspaces("", "", r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@FM-GISSQLHA_DEFAULT_VERSION.sde", "SDE_WORKSPACE", True)
arcpy.RefreshTOC()
#mxd.save()
