import arcpy, os, traceback

rootdir = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\mxd"
readonly = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataReader@FM-GISSQLHA_DEFAULT_VERSION.sde"
readwrite = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@FM-GISSQLHA_DEFAULT_VERSION.sde"

try:
    #print indir
    #for file in os.listdir(indir):
    for dirpath, dirnames, filenames in os.walk(rootdir, topdown=True):
        newconnectionfile = ""
        for file in filenames:
            if file.endswith('.mxd'):
                if os.path.basename(dirpath) == os.path.basename(rootdir) or os.path.basename(dirpath) == "telecom" or os.path.basename(dirpath) == "utilities":
                    #print os.path.basename(dirpath) + "\\" + file + " -- READONLY --"
                    newconnectionfile = readonly
                else:
                    #print os.path.basename(dirpath) + "\\" + file + " -- READWRITE --"
                    newconnectionfile = readwrite

                #print dirpath + "\\" + file
                mxd = arcpy.mapping.MapDocument(dirpath + "\\" + file)
                #print mxd
                #mxd.findAndReplaceWorkspacePaths("", newconnectionfile)
                mxd.replaceWorkspaces("", "", newconnectionfile, "SDE_WORKSPACE", True)
                mxd.save();
                del mxd
                print os.path.basename(dirpath) + "\\" + file + " Re-Sourced"

except arcpy.ExecuteError: 
    msgs = arcpy.GetMessages(2) 
    arcpy.AddError(msgs)
except:
    # Get the traceback object
     tb = sys.exc_info()[2]
     tbinfo = traceback.format_tb(tb)[0]

     # Concatenate information together concerning the error into a message string
     pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
     print pymsg
