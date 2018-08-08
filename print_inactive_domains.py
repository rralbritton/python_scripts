#list_active_domains.py
import arcpy, sys, traceback, smtplib, os
from email.MIMEText import MIMEText

def sendEmail():
    
    Sender = "GIS_Automation@fm.utah.edu"
    Recp = "Rachel.Albritton@fm.utah.edu"
    SUBJECT = "Domain Clean Up"
    body = open(inputFile, 'r')
    msg = MIMEText(body.read())
    body.close()
    
    msg['Subject'] = SUBJECT 
    msg['From'] = Sender
    msg['To'] = Recp

    
    # Send the message via the SMTP server
    Host = "smtp.utah.edu"
    s = smtplib.SMTP(Host)
    s.sendmail(Sender, Recp, msg.as_string())
    s.quit()
    os.remove(inputFile)
    
#Set workspace environment to geodatabase
workspace = arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde"

#Variables
activeDomainTable = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\UUSD.DBO.domain_active"
allDomainsTable = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\UUSD.DBO.domain_all"
inputFile = "C:/Temp/domain_errors.txt"
inactiveDomains = []


try:

    #Start Edit Session
    edit = arcpy.da.Editor(workspace)
    edit.startEditing(False,True)

    #create views
    activeDomainsView = arcpy.MakeTableView_management(activeDomainTable,'activeDomainsView')
    allDomainsView = arcpy.MakeTableView_management(allDomainsTable, 'allDomainsView')
        
    #Text file to email errors
    infile = open(inputFile,'w')
    infile.write("FEATURE CLASSES & TABLES SKIPPED:\n")
    
    #Loop through feature datasets and list all feature classes and there Active Domains #subtypes
    print "FEATURE DATASETS\n"
    for fds in arcpy.ListDatasets():
        try: 
            for fc in arcpy.ListFeatureClasses('','',fds):
                for field in arcpy.ListFields(fc):
                    if field.domain !="":
                        print field.domain
                        intcur = arcpy.da.InsertCursor(activeDomainTable,("name"))
                        intcur.insertRow([field.domain])
                        del intcur
                subtypes = arcpy.da.ListSubtypes(fc)
                for stcode, stdict in list(subtypes.items()):
                    for stkey in list(stdict.keys()):
                        if stkey == 'FieldValues':
                            fields = stdict[stkey]
                            for field, fieldvals in list(fields.items()):
                                if not fieldvals[1] is None:
                                    intcur1 = arcpy.da.InsertCursor(activeDomainTable,("name"))
                                    intcur1.insertRow([fieldvals[1].name])
                                    del intcur1
                                    print fieldvals[1].name

        except:
            print "ERROR: " + fc
            infile.write(fc + "\n")
                        
    #Loop through all feature classes not in a feature dataset and list active domains & subtypes
    print "\nFEATURE CLASSES\n"
    try:
        for features in arcpy.ListFeatureClasses():
            #print "\n" + features
            for flds in arcpy.ListFields(features):
                if flds.domain !="":
                    print flds.domain
                    intcur = arcpy.da.InsertCursor(activeDomainTable,("name"))
                    intcur.insertRow([flds.domain])
                    del intcur
            subtypes = arcpy.da.ListSubtypes(features)
            for stcode, stdict in list(subtypes.items()):
                for stkey in list(stdict.keys()):
                    if stkey == 'FieldValues':
                        fields = stdict[stkey]
                        for field, fieldvals in list(fields.items()):
                            if not fieldvals[1] is None:
                                intcur1 = arcpy.da.InsertCursor(activeDomainTable,("name"))
                                intcur1.insertRow([fieldvals[1].name])
                                del intcur1
                                print fieldvals[1].name
    except:
        print "ERROR: " + features
        infile.write(features + "\n")
    
    ###Loop through all tables and list active domains & subtypes           
    print "\nTABLES\n"
    try:
        for table in arcpy.ListTables():
            #print "\n"+table
            for f in arcpy.ListFields(table):
                if f.domain !="":
                    print f.domain
                    intcur = arcpy.da.InsertCursor(activeDomainTable,("name"))
                    intcur.insertRow([f.domain])
                    del intcur
            subtypes = arcpy.da.ListSubtypes(table)
            for stcode, stdict in list(subtypes.items()):
                for stkey in list(stdict.keys()):
                    if stkey == 'FieldValues':
                        fields = stdict[stkey]
                        for field, fieldvals in list(fields.items()):
                            if not fieldvals[1] is None:
                                intcur1 = arcpy.da.InsertCursor(activeDomainTable,("name"))
                                intcur1.insertRow([fieldvals[1].name])
                                del intcur1
                                print fieldvals[1].name
    except:
        print "ERROR: " + table
        infile.write(table + "\n")
    
    #Delete duplicate records
    arcpy.DeleteIdentical_management(activeDomainTable,"name")
    print "\n" + arcpy.GetMessages(0) + "\n"

    #Get list of all domains
    allDomains = arcpy.da.ListDomains(workspace)
    for domain in allDomains:
        intcur = arcpy.da.InsertCursor(allDomainsTable,("dom_name"))
        intcur.insertRow([domain.name])
        del intcur
        
    #Stop edit session
    edit.stopEditing(True)
    
    ###Join all active domains table to the all domains table
    ###Those domains in the all domains table that do not have a match are inactive
    
    arcpy.AddJoin_management(allDomainsView,"dom_name",activeDomainsView,"name","KEEP_ALL")
      
    with arcpy.da.SearchCursor(allDomainsView, ["UUSD.DBO.domain_active.name","UUSD.DBO.domain_all.dom_name"]) as sc:
        for row in sc:
            if row[0] == None:
                inactiveDomains.append(row[1])
                try:
                    arcpy.DeleteDomain_management(workspace,row[1])
                except:
                    infile.write("\nCould not delete " + row[1]+".\n"+arcpy.GetMessages(2)+"\n")
                    
    #print inactiveDomains
    inactiveDomains.sort()
    print "\nLENGTH: "+ str(len(inactiveDomains))+"\n"
    infile.write("INACTIVE DOMAINS\n")
    for dom in inactiveDomains:
        print dom      
        infile.write(dom+"\n")
   
    infile.close()
    sendEmail()
    
    print "\nDONE"  

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
    infile.write(pymsg)
    infile.write(msgs)
    infile.close()
    sendEmail()


    
    
