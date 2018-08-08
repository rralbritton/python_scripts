#Name:      DDC_ExportAttachments.py
#Purpose:   Select and download attachments related to reported issues
#Author:    Rachel Albritton, Facilities Management

import arcpy, os, datetime
from arcpy import da
from datetime import timedelta

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName

# Inputs
PicTable = r"\\ad.utah.edu\sys\FM\GIS\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@fm-sqlsrvrtest.fm.utah.edu.sde\UUSD.DBO.DDC_Reports_Table__ATTACH"
PicTableView = outName(PicTable,"_View")

# Folder where selected attachments will be saved
fileLocation = r"\\ad.utah.edu\sys\FM\gis\ags_directories\DDC_Web\Photos"

# Table must be a view in order to select relevant records
arcpy.MakeTableView_management(PicTable,PicTableView)

# Get start and end times for report
# ArcGIS UTC Time reads 7 hours later than the actual time.
# The following script adds 7 hours to the current time so that
# the current time would match the current time in the ArcGIS DB

UTCNowTime = datetime.datetime.now()+ datetime.timedelta(hours = 7)

# Next we need all records that may have been recorded in the past 8 hours
# as seen within the ArcGIS DB.
# Subtract 8 hours from the UTCNowTime variable

UTCPriorTime = UTCNowTime - datetime.timedelta (hours = 8)
 
# Find all records that are later than or = UTCPriorTime

SQL = "created_date >="+ "'"+UTCPriorTime.strftime('%Y-%m-%d %H:%M:%S')+"'"
arcpy.SelectLayerByAttribute_management(PicTableView,"NEW_SELECTION", SQL)

# Count number of records selected
count = arcpy.GetCount_management(PicTableView)
print str(count) + "  attachment records selected\n\n"

try:
    if count == 0:
        infile.write("No Attachements Found.\n\n")
        print "No Attachments Found."

    else: # download relevant attachments to registered server folder

        with da.SearchCursor(PicTableView, ['DATA', 'ATT_NAME', 'ATTACHMENTID']) as cursor:
            for item in cursor:
                attachment = item[0]
                filenum = "ATT" + str(item[2]) + "_"
                filename = filenum + str(item[1])
                open(fileLocation + os.sep + filename, 'wb').write(attachment.tobytes())
                del item
                del filenum
                del filename
                del attachment
                
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

print "done"
