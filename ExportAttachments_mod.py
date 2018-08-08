#ExportAttachments.py

import arcpy
from arcpy import da
import os
import traceback

inTable = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\UUSD.DBO.restrooms__ATTACH"

#Folder where attachments will be saved
fileLocation = r"S:\Chris\Projects\Gender Free Restrooms\Photos"    

try:
    with da.SearchCursor(inTable, ['DATA','REL_OBJECTID','ATT_NAME']) as cursor:
        for item in cursor:
            attachment = item[0]
            filename = str(item[2])    
            open(fileLocation + os.sep + filename, 'wb').write(attachment.tobytes())
            del item
            del filename
            del attachment
    print 'done'

except:
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    # Return python error messages for use in script tool or Python Window
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)

    # Print Python error messages for use in Python / Python Window
    print(pymsg)
    print(msgs) 
