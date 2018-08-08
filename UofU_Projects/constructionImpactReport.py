#Name:          constructionImpactReport.py
#Purpose:       Generate a report at the first of the month that provides information
#               on all parking stalls that were impacted by construction over the
#               previous month. This report is used by Chris Strong (GIS Analyst)
#               and his client(s).
#Author:        Rachel Albritton
#Last Update:   12/7/2017

import arcpy, os, traceback
import csv
import smtplib, email
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.mime.application import MIMEApplication

def sendEmail(inputFile, attachment):
    
    Sender = "GISAutomation@fm.utah.edu"
    Recp = ['Rachel.Albritton@fm.utah.edu','chris.strong@fm.utah.edu','solomon.brumbaugh@utah.edu'] #
    SUBJECT = "Construction Impacts Report"
    msg = msg = MIMEMultipart()
    
    msg['Subject'] = SUBJECT 
    msg['From'] = Sender
    msg['To'] = ",".join(Recp)

    #Write Email Body (Status Report)
    text = open(inputFile,'rb')
    body = MIMEText(text.read())
    msg.attach(body)

    #Attach Report
    filename = attachment
    fp=open(filename,'rb')
    att = email.mime.application.MIMEApplication(fp.read(),_subtype="csv")
    fp.close()
    att.add_header('Content-Disposition','attachment',filename=os.path.basename(filename))
    msg.attach(att)
    
    # Send the message via the SMTP server
    Host = "smtp.utah.edu"
    s = smtplib.SMTP(Host)
    s.sendmail(Sender, Recp, msg.as_string())
    s.quit()
    os.remove(attachment)
    
workspace = arcpy.env.workspace = r'\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde'
arcpy.env.overwriteOutput = True

#Input Data
cit = '\uusd.DBO.umap\uusd.DBO.CIT_Areas'
stalls = '\uusd.DBO.cs_parking\uusd.DBO.stalls'
outfile = r'\\ad.utah.edu\sys\FM\gis\gis_scheduled_tasks\cit_reports.csv'
fields =['beginDate','endDate','PROJECT','unifier_project_num','project_manager','Join_Count']
email_body = r'\\sys-files2.sys.utah.edu\sys\FM\gis\gis_scheduled_tasks\cit_areas_message.txt'


try: 
    #Create Feature Layer
    cit_layer = arcpy.MakeFeatureLayer_management(cit, 'cit_layer')
    stalls_layer = arcpy.MakeFeatureLayer_management(stalls, 'stalls_layer')

    #Query Data
    SQL = '(beginDate < DATEADD(m,-1, GETDATE())AND endDate >= GETDATE()AND beginDate<=endDate)OR(beginDate < GETDATE() AND endDate >= DATEADD(m,-1,GETDATE())AND endDate < GETDATE()AND beginDate<=endDate)OR (beginDate >= DATEADD(m,-1,GETDATE())AND beginDate < = GETDATE()AND endDate > GETDATE() AND beginDate<=endDate)'
    arcpy.SelectLayerByAttribute_management(cit_layer,'NEW_SELECTION', SQL)
    #cit_count = arcpy.GetCount_management(cit_layer).getOutput(0)
    #print cit_count

    arcpy.SelectLayerByAttribute_management(stalls_layer,'NEW_SELECTION','stall_control <> 2')
    #stallsCount = arcpy.GetCount_management(stalls_layer).getOutput(0)
    #print stallsCount

    #Create Spatial Join
    spatialJoin = r'\\ad.utah.edu\sys\FM\gis\gis_scheduled_tasks\temp_task_data.gdb\cit_stalls_join'
    arcpy.SpatialJoin_analysis(cit_layer,stalls_layer,spatialJoin,'JOIN_ONE_TO_ONE','KEEP_COMMON')
    #joinCount = arcpy.GetCount_management(spatialJoin).getOutput(0)
    #print joinCount

    with open(outfile,'wb') as outputCSV:
        writer = csv.writer(outputCSV)
        writer.writerow(['Begin Date','End Date','Project','Unifier No','Project Manager','Stall Count'])
        rows = arcpy.da.SearchCursor(spatialJoin,fields)
        for row in rows:
            writer.writerow(row)
        del rows

    sendEmail(email_body, outfile)
    arcpy.Delete_management(spatialJoin)
        
    print 'done'
    
except:
    
    #Open Error email File
    error_email = r'\\sys-files2.sys.utah.edu\sys\FM\gis\gis_scheduled_tasks\cit_areas_ERROR.txt'
    errorFile = open(error_email,'w')

    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    # Print Python error messages for use in Python / Python Window
    errorFile.write('The CIT/Stalls Impact Report Failed. Please review errors below.\n\n')
    errorFile.write(pymsg+'\n\n'+msgs)
    errorFile.close()
    print(pymsg)
    print(msgs)

    #Email Report
    Sender = "GISAutomationScript@fm.utah.edu"
    Recp = ['Rachel.Albritton@fm.utah.edu','chris.strong@fm.utah.edu']
    body = open(error_email, 'r')
    msg = MIMEText(body.read())
    body.close()

    msg['Subject'] = 'ERROR: CIT/Stalls Report Failed'
    msg['From'] = Sender
    msg['To'] = ",".join(Recp)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    Host = "smtp.utah.edu"
    s = smtplib.SMTP(Host)
    s.sendmail(Sender, Recp, msg.as_string())
    s.quit()
    os.remove(error_email)
    
