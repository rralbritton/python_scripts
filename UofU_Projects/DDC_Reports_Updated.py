#Title:         DDC_Reports_Updated.py
#Purpose:       Send security walk-through summary to DDC management.

#Assumptions:   Assumes a walkthrough is being done once every eight hours.
#               After a walkthrough is completed and a report is requested,
#               the script pulls only those records created in the reports table 
#               within the last 8 hours.

#Notes:         It is possible that a user can log an issue in the Reports Table &
#               forget to change the status of a stop from "OK" to "Report to Manager".
#               The reverse is also true. Overtime the script will work to build in logic
#               to notify a user of discrepancies between a stop status in the report table
#               and the number of issue records recorded in the Reports Table.

#Author:        Rachel Albritton
#Date:          Febuary 12, 2016



import arcpy, os, datetime, smtplib
from arcpy import da
from datetime import timedelta
from email.MIMEText import MIMEText

# Workspace should be the a server registered folder
arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_directories\DDC_Web"
arcpy.env.overwriteOutput = True

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName 
    
# Variables
StopsTable = r"\\ad.utah.edu\sys\FM\GIS\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@fm-sqlsrvrtest.fm.utah.edu.sde\UUSD.DBO.DDC\UUSD.DBO.DDC_Stops"
StopsView = outName(StopsTable,"_View")
ReportsTable = r"\\ad.utah.edu\sys\FM\GIS\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@fm-sqlsrvrtest.fm.utah.edu.sde\UUSD.DBO.DDC_Reports_Table"
ViewTable = outName(ReportsTable,"_Lyr")
PicTable = r"\\ad.utah.edu\sys\FM\GIS\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@fm-sqlsrvrtest.fm.utah.edu.sde\UUSD.DBO.DDC_Reports_Table__ATTACH"
PicTableView = outName(PicTable,"_View")
fileLocation = r"\\ad.utah.edu\sys\FM\gis\ags_directories\DDC_Web\Photos"
inputfile =  r"\\ad.utah.edu\sys\FM\gis\ags_directories\DDC_Web\DDC_ReportSummary.txt"

#Open Report
infile = open(inputfile,'w')
infile.write("REPORT SUMMARY: "+str(datetime.datetime.now())+"\n\n")

# Select all records from the ReportsTable, that have been created over the past 8 hours. 

#Make layer and table views
arcpy.MakeTableView_management(ReportsTable, ViewTable)
arcpy.MakeFeatureLayer_management(StopsTable,StopsView)
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

# Anything created after the UTCPriorTime should be included in the mgmt report
# Find all records that are later than or = UTCPriorTime

SQL = "created_date >="+ "'"+UTCPriorTime.strftime('%Y-%m-%d %H:%M:%S')+"'"
arcpy.SelectLayerByAttribute_management(ViewTable,"NEW_SELECTION", SQL)

#Count number of records selected
result1 = arcpy.GetCount_management(ViewTable)
count = int(result1.getOutput(0))
print str(count) +" issues were logged\n"
 
if count == 0:
    infile.write("No Issues were logged during this walk through.\n\n")
    print "No Issues were logged during this walk through."

    #Print a summary report
    
    #Select and count the # of stops set to "OK"
    #Total should = the # of stops if no reports are found in the count reports analysis
    #If total # is less than the total # of stops then a tech either didn't change the stop status
    #or the tech didn't log a record for an issue
    
    arcpy.SelectLayerByAttribute_management(StopsView,"NEW_SELECTION", "Stop_Status = 'OK'")
    result2 = arcpy.GetCount_management(StopsView)
    StopCount = int(result2.getOutput(0))
    
    if StopCount < 9: #9 is the total # of stop in test file
        sc2 = arcpy.SearchCursor(StopsView)
        for line in sc2:
            if line.Stop_Status == "OK":
                infile.write("Stop "+str(line.Stop_Number)+": "+line.Stop_Status+"\tTech: "+line.last_edited_user+"\tDate: "+str(line.last_edited_date)+"\n")

    sc3 = arcpy.SearchCursor(StopsView)
    infile.write("\n")
    infile.write("The following stops are set to 'Report to Manager' but have no additional information logged about them.\n\n")

    for lines in sc3:
        if lines.Stop_Status == "Report to Manager":
            infile.write ("Stop "+str(lines.Stop_Number)+": "+lines.Stop_Status+"\tTech: "+lines.last_edited_user+"\tDate: "+str(lines.last_edited_date)+"\n") 
                          
else:
    
    infile.write("Issues Recorded: \n\n")
    sc1 = arcpy.SearchCursor(ViewTable)
    for row in sc1:
        infile.write("Stop "+str(row.Stop_Num)+": "+row.Issue+"\tTech: "+row.created_user+"\tDate: "+str(row.created_date)+"\n")
        del row
    del sc1

    #Check recorded status of the rest of the stops
    arcpy.SelectLayerByAttribute_management(StopsView,"NEW_SELECTION", "Stop_Status = 'OK'")

    sc4 = SearchCursor(StopsView)
    
    for rows in sc4:
        if rows.Stop_Status == "OK":
            infile.write("Stop "+str(rows.Stop_Number)+": "+rows.Stop_Status+"\tTech: "+rows.last_edited_user+"\tDate: "+str(rows.last_edited_date)+"\n")
    
##    result4 = arcpy.GetCount_management(StopsView)
##    StopCount2 = int(result4.getOutput(0))
##    print StopCount2
        
    # Downloaded related photo attachements if they exist

    #Select all attachment records created within the past 8 hours
    arcpy.SelectLayerByAttribute_management(PicTableView,"NEW_SELECTION", SQL)

    # Count number of records selected
    result5 = arcpy.GetCount_management(PicTableView)
    PicCount = int(result5.getOutput(0))
    print str(PicCount) + "  attachment records selected\n\n"

    if PicCount == 0:
        infile.write("No Attachements Found for this report period.\n\n")
        print "No Attachments Found."
    
    else: # download relevant attachments to registered server folder
        infile.write("\n"+str(PicCount) + "  photos are attached to this email for this report period.\n\n")
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

infile.close()

#Email Report

#Sender Email
Sender = "Rachel.Albritton@fm.utah.edu"

#Recipient's Email
Recp = "Rachel.Albritton@fm.utah.edu"

SUBJECT = "Security Walk Through Report Summary"

msg = MIMEMultipart()
msg['Subject'] = SUBJECT 
msg['From'] = Sender
msg['To'] = Recp

#Write Email Body (Status Report)
report = open(inputfile,'rb')
body = MIMEText(report.read())
msg.attach(body)

#Attach Photo(s)
PhotoFiles = os.listdir(r"\\ad.utah.edu\sys\FM\gis\ags_directories\DDC_Web\Photos")
PhotoFolder = r"\\ad.utah.edu/sys/fm/gis/ags_directories/DDC_Web/Photos/"

for file in PhotoFiles:
    FullPath = PhotoFolder+file
    if file.endswith(".jpg"):
        fp = open(FullPath,'rb')
        img = MIMEImage(fp.read())
        fp.close()
        msg.attach(img)

# Send the message via the SMTP server
Host = "smtp.utah.edu"
s = smtplib.SMTP(Host)
s.sendmail(Sender, [Recp], msg.as_string())
s.quit()

#Delete Photos from Server Folder (Pics will still remain in DB)

print "done"
