#LightConcernsReport.py

import sys, os, arcpy, datetime, traceback, smtplib
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.mime.application import MIMEApplication

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName

arcpy.env.overwrite = "True"

try:

    #Query out any new lighting concerns reported in the past 24 hours
    lightingConcerns = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\UUSD.DBO.lighting_concerns"
    lightingConcernsView = outName(lightingConcerns,"_view")
    arcpy.MakeFeatureLayer_management(lightingConcerns,lightingConcernsView)

    #Get all points created in the last 24 hours
    # ArcGIS UTC Time reads 7 hours later than the actual time.
    # The following script adds 7 hours to the current time so that
    # the 'current time' would match the current time in the ArcGIS DB
    UTCNowTime = datetime.datetime.now()+ datetime.timedelta(hours = 7)
    UTCPriorTime = UTCNowTime - datetime.timedelta (hours = 24)
    SQL = "created_date >="+ "'"+UTCPriorTime.strftime('%Y-%m-%d')+"'"
    arcpy.SelectLayerByAttribute_management(lightingConcernsView,"NEW_SELECTION", SQL)

    #Count number of records selected
    count = arcpy.GetCount_management(lightingConcernsView)
    results = int(count.getOutput(0))
    emailFile = r"\\ad.utah.edu\sys\FM\gis\ags_directories\Lighting_Concerns\email.txt"
    infile = open(emailFile,'w')

    if results > 0:
        
        #Open file for email
        print str(results) +" new concern(s) have been reported in the past 24 hours.\n" 
        infile.write(str(results)+" new concern(s) have been reported in the past 24 hours.\nPlease see attached map for approximate location(s).\n")
        infile.close()
        print "Please see attached map for approximate location(s).\n"

        #Add temp layer to MXD
        mxd = arcpy.mapping.MapDocument(r"\\ad.utah.edu\sys\FM\gis\ags_directories\Lighting_Concerns\Report_Template.mxd")
        df = arcpy.mapping.ListDataFrames(mxd)[0]

        #Select all visible points and zoom to their extent
        lyr = arcpy.mapping.ListLayers(mxd,"Lighting Concerns", df)[0]
        arcpy.SelectLayerByAttribute_management(lyr,"SWITCH_SELECTION")
        df.zoomToSelectedFeatures() 
        arcpy.SelectLayerByAttribute_management(lyr,"CLEAR_SELECTION")    

        #Save output
        mxdOutput = r"\\ad.utah.edu\sys\FM\gis\ags_directories\Lighting_Concerns\Lighting_Report_"+str(UTCNowTime.strftime('%m%d%y'))+".pdf"
        arcpy.mapping.ExportToPDF (mxd, mxdOutput)
        del mxd

        #Send Email with results

        #Recipient's Email
        Recp = ['Rachel.Albritton@fm.utah.edu','russ.courville@fm.utah.edu']

        msg = MIMEMultipart()
        msg['Subject'] = "FM Lighting Concerns Report"
        msg['From'] = "FM_Lighting_Report@fm.utah.edu"
        msg['To'] = ",".join(Recp)
        
        #Write Email Body (Status Report)
        report = open(errorFile,'rb')
        body = MIMEText(report.read())
        msg.attach(body)

        # Send the message via the SMTP server
        Host = "smtp.utah.edu"
        s = smtplib.SMTP(Host)
        s.sendmail(Sender, Recp, msg.as_string())
        s.quit()

        #Cleanup
        os.remove(mxdOutput)
                                                                                          
    else:

        print "There are no new lighting concerns to report."  

except: 
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    #Email that an error occured
    errorFile = r"\\ad.utah.edu\sys\FM\gis\ags_directories\Lighting_Concerns\errors.txt"
    erfile = open(errorFile,'w')
    erfile.write("An error occured while analyzing the lighting data")
    erfile.write(pymsg)
    erfile.write(msgs)
    erfile.close()
    
    #Recipient's Email
    Recp = ['Rachel.Albritton@fm.utah.edu']
    msg = MIMEMultipart()
    msg['Subject'] = "ERROR - FM Lighting Concerns Report - ERROR"  
    msg['From'] = "FM_Lighting_Report@fm.utah.edu"
    msg['To'] = ",".join(Recp)
    
    #Write Email Body (Status Report)
    report = open(emailFile,'rb')
    body = MIMEText(report.read())
    msg.attach(body)

print "done"
