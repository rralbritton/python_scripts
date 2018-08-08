#ExportAttachments.py

import arcpy
from arcpy import da
import os

inTable = r"S:\Rachel\Data\Temp_Fiber_Manhole_Data\Manholes_to_Verify_Download\3247b01312a148c29276bb1bfea13c7f.gdb\Manholes_to_Verify__ATTACH"

#Folder where attachments will be saved
fileLocation = r"S:\Rachel\Data\Temp_Fiber_Manhole_Data\Manholes_to_Verify_Download"

try:
    with da.SearchCursor(inTable, ['DATA', 'ATT_NAME', 'ATTACHMENTID']) as cursor:
        for item in cursor:
            attachment = item[0]
            filenum = "ATT" + str(item[2]) + "_"
            filename = filenum + str(item[1])
            open(fileLocation + os.sep + filename, 'wb').write(attachment.tobytes())
            del item
            del filenum
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
