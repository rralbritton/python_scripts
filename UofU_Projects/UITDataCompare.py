#UITDataCompare.py

import arcpy, os, datetime, smtplib, traceback
from email.MIMEText import MIMEText

def sendEmail():
    
    Sender = "Fiber.Updates@fm.utah.edu"
    Recp = "Rachel.Albritton@fm.utah.edu"
    SUBJECT = "Fiber Updates"
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

#Setup workspace
arcpy.env.overwriteOutput = True 
workspace = arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb"

#Variables
gisFiberLines = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\UUSD.DBO.Fiber\UUSD.DBO.Fiber_Lines"
gisEnclosures = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\UUSD.DBO.Fiber\UUSD.DBO.Fiber_Enclosures"
uitFiberLines = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\readonly_CAMPDB.sde\INFRASTRUCTURE.CONDUIT_BANK_V"
uitEnclosures = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\readonly_CAMPDB.sde\INFRASTRUCTURE.ENCLOSURE_V"

gisFiberLinesCopy = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\fiber_lines_copy"
tempMissingLines = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\temp_missing_lines"
knownMissingLines = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\Fiber_Missing_Lines"
newGISLines = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\new_Lines"
knownMissingEnclosures = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\Fiber_Missing_Enclosures"
tempMissingEnclosures = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\temp_missing_enclosures"
gisEnclosuresCopy = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\gis_enclosures_copy"

inputFile = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\fiberUpdate.txt"

try:
    #Open textfile
    infile = open(inputFile,'w')
    today = (datetime.date.today()).strftime('%m_%d_%y')
    infile.write("FIBER DATA CHECK SUMMARY: "+ str(today)+"\n\n")
    
    #Export UIT table(s) to a FGDB
    uitFiberLinesIntExport = arcpy.TableToTable_conversion(uitFiberLines, r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb","uitFiberLinesIntExport")
    uitEnclosuresExport = arcpy.TableToTable_conversion(uitEnclosures, r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb","uitEnclosuresExport")
    
    #Create table/fc views
    gisFiberLinesView = arcpy.MakeFeatureLayer_management(gisFiberLines,"gisFiberLinesView")
    uitFiberLinesIntView = arcpy.MakeTableView_management(uitFiberLinesIntExport, "uitFiberLinesIntView")
    knownMissingLinesView = arcpy.MakeTableView_management(knownMissingLines,"knownMissingLinesView")
    uitEnclosuresView = arcpy.MakeTableView_management(uitEnclosuresExport,"uitEnclosuresView")
    gisEnclosuresView = arcpy.MakeFeatureLayer_management(gisEnclosures,"gisEnclosuresView")
    knownMissingEnclosuresView = arcpy.MakeTableView_management(knownMissingEnclosures,"knownMissingEnclosuresView")

    #Select out conduit duck banks, tube routes, tube banks, and interduct banks
    arcpy.SelectLayerByAttribute_management(uitFiberLinesIntView,"NEW_SELECTION","CONDUIT_ROUTE_TYPE IN('ConduitBank','InterductBank','TubeBank','TubeRoute')")
    uitFiberLinesExport = arcpy.TableToTable_conversion(uitFiberLinesIntView,r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb","uitFiberLinesExport")
    uitFiberLinesView = arcpy.MakeTableView_management(uitFiberLinesExport,"uitFiberLinesView")            

    #Check Temp Missing Lines Table    
    if arcpy.Exists(tempMissingLines):
        gisMissingLinesView = arcpy.MakeTableView_management(tempMissingLines,"gisMissingLinesView")
        rowCount = int(arcpy.GetCount_management(gisMissingLinesView).getOutput(0))
        if rowCount != 0:
            tempMissingLinesBackup = workspace+"//temp_missing_lines_"+str(today)
            arcpy.CopyRows_management(gisMissingLinesView,tempMissingLinesBackup)
            arcpy.DeleteRows_management(gisMissingLinesView)
            infile.write("temp_missing_lines feature class contained old data.\nThis data was backed up at " + tempMissingLinesBackup + ".\n\n")
            
    else:
        print "FC does not exist. Creating it now.\n"
        arcpy.CreateTable_management(workspace,"temp_missing_lines")
        gisMissingLinesView = arcpy.MakeTableView_management(tempMissingLines,"gisMissingLinesView")
        
        arcpy.AddField_management(gisMissingLinesView,"cb_id","LONG")
        arcpy.AddField_management(gisMissingLinesView,"type","TEXT",25)
        arcpy.AddField_management(gisMissingLinesView,"from_enc","TEXT",25)
        arcpy.AddField_management(gisMissingLinesView,"to_enc","TEXT",25)
        arcpy.AddField_management(gisMissingLinesView,"from_utm_x","DOUBLE")
        arcpy.AddField_management(gisMissingLinesView,"from_utm_y","DOUBLE")
        arcpy.AddField_management(gisMissingLinesView,"to_utm_x","DOUBLE")
        arcpy.AddField_management(gisMissingLinesView,"to_utm_y","DOUBLE")
                
    #Find all fiber lines that are in UIT DB that are not in GIS DB
    #Write them into a temp table in FGDB
    infile.write("CONDUIT DUCT BANKS IN UIT BUT NOT IN GIS:\n")
    
    arcpy.AddJoin_management(uitFiberLinesView,"ID",gisFiberLinesView,"conduit_bank","KEEP_ALL")

    sc1 = arcpy.SearchCursor(uitFiberLinesView)
    print "Missing conduit duct banks:\n"
    for row1 in sc1:
        if row1.getValue("UUSD.DBO.Fiber_Lines.conduit_bank") == None:
            print row1.getValue("uitFiberLinesExport.ID")
            
            #Use insert cursor to write values in to temp table
            intcur1 = arcpy.InsertCursor(tempMissingLines)
            icur1 = intcur1.newRow()
            icur1.setValue("cb_id",row1.getValue("uitFiberLinesExport.ID"))
            icur1.setValue("type",row1.getValue("uitFiberLinesExport.CONDUIT_ROUTE_TYPE"))
            intcur1.insertRow(icur1)
            del intcur1
        del row1
    del sc1

    count1 = arcpy.GetCount_management(gisMissingLinesView).getOutput(0)

    #Compare this list with known missing conduit duct banks
    #And determine if there are missing CB that we aren't aware of
    print "\nThere are " + str(count1) + " conduit duct banks that are in the UIT DB that are not in the GIS DB."
    print "Checking to see if these CBs match known missing CBs"

    arcpy.AddJoin_management(gisMissingLinesView,"cb_id",knownMissingLinesView,"ID","KEEP_ALL")
            
    knownMissing = []

    sc2 = arcpy.SearchCursor(gisMissingLinesView)
    for row2 in sc2:
        if row2.getValue("Fiber_Missing_Lines.ID") != None:
            knownMissing.append(row2.getValue("Fiber_Missing_Lines.ID"))
        del row2
    del sc2

    arcpy.RemoveJoin_management(gisMissingLinesView)

    if len(knownMissing) > 0:
        #Delete known info and keep new
        where = "cb_id IN("+",".join([str(i) for i in knownMissing])+")"
        arcpy.SelectLayerByAttribute_management(gisMissingLinesView,"NEW_SELECTION",where)
        arcpy.DeleteRows_management(gisMissingLinesView)

    results = int(arcpy.GetCount_management(gisMissingLinesView).getOutput(0))
    
    #If there are new records to be added
    #Get data need to map line locations

    if results > 0:

        print "There are " + str(results) + " new records that need to be added to the GIS DB"
        infile.write("There are " + str(results) + " new records that need to be added to the GIS DB.\n")

        #Add From/To enclosure names to gisMissingLinesView
        arcpy.AddJoin_management(gisMissingLinesView,"cb_id",uitFiberLinesView,"ID","KEEP_COMMON")
        arcpy.CalculateField_management(gisMissingLinesView,'temp_missing_lines.from_enc','!uitFiberLinesExport.FROM_ENCLOSURE_ID!','PYTHON_9.3')
        arcpy.CalculateField_management(gisMissingLinesView,'temp_missing_lines.to_enc','!uitFiberLinesExport.TO_ENCLOSURE_ID!','PYTHON_9.3')
        
        #Get From/To enclosure coordinates
        arcpy.RemoveJoin_management(gisMissingLinesView)
        arcpy.AddJoin_management(gisMissingLinesView,"from_enc",gisEnclosuresView,"ID","KEEP_COMMON")
        arcpy.CalculateField_management(gisMissingLinesView,'temp_missing_lines.from_utm_x','!UUSD.DBO.Fiber_Enclosures.POINT_X!','PYTHON_9.3')
        arcpy.CalculateField_management(gisMissingLinesView,'temp_missing_lines.from_utm_y','!UUSD.DBO.Fiber_Enclosures.POINT_Y!','PYTHON_9.3')
        arcpy.RemoveJoin_management(gisMissingLinesView)

        arcpy.AddJoin_management(gisMissingLinesView,"to_enc",gisEnclosuresView,"ID","KEEP_COMMON")
        arcpy.CalculateField_management(gisMissingLinesView,'temp_missing_lines.to_utm_x','!UUSD.DBO.Fiber_Enclosures.POINT_X!','PYTHON_9.3')
        arcpy.CalculateField_management(gisMissingLinesView,'temp_missing_lines.to_utm_y','!UUSD.DBO.Fiber_Enclosures.POINT_Y!','PYTHON_9.3')
        arcpy.RemoveJoin_management(gisMissingLinesView)

        #Find all records that have all the from/to coordinates and map them
        arcpy.SelectLayerByAttribute_management(gisMissingLinesView,"NEW_SELECTION", "from_utm_x IS NOT NULL AND to_utm_x IS NOT NULL")
        arcpy.XYToLine_management(gisMissingLinesView,newGISLines,"from_utm_x","from_utm_y","to_utm_x","to_utm_y","GEODESIC","cb_id",gisEnclosures)
        arcpy.DeleteRows_management(gisMissingLinesView)

        #New lines should NOT be appended to the existing dataset.
        #New Lines need to be manually reviewd and edited to provide spatial accuracy where possible.

        #Update email report
        newLinesCount = int(arcpy.GetCount_management(newGISLines).getOutput(0))
        gisMissingCount = int(arcpy.GetCount_management(gisMissingLinesView).getOutput(0))
        infile.write("There are "+ str(newLinesCount) + " to be added to the Fiber Lines feature class.\nThe temporary new lines feature class is located at \n\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\new_Lines.\n\n")
        infile.write("There are " + str(gisMissingCount) + " conduit duct banks that could not be matched to existing enclosure(s).\n")
        infile.write("Review this table, add notes where necessary, and append to existing  ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\Fiber_DataCompare.gdb\Telecom_Missing_Lines table.\n\n")

    else:
        infile.write("There are NO new fiber lines that need to be added to the GIS DB.\n\n")
        
    #Find any Lines that are in the GIS DB but not in UIT DB
    infile.write("CONDUIT BANKS IN GIS BUT NOT IN UIT\n")
    arcpy.SelectLayerByAttribute_management(gisFiberLinesView,"NEW_SELECTION","conduit_bank <> 0")
    arcpy.CopyFeatures_management(gisFiberLinesView,gisFiberLinesCopy)
    gisFiberLinesCopyView = arcpy.MakeFeatureLayer_management(gisFiberLinesCopy,"gisFiberLinesCopyView")
    
    arcpy.AddJoin_management(gisFiberLinesCopyView,"conduit_bank",uitFiberLinesView,"ID","KEEP_ALL")
    arcpy.SelectLayerByAttribute_management(gisFiberLinesCopyView,"NEW_SELECTION","uitFiberLinesExport.ID IS NULL")
    nullCount = int(arcpy.GetCount_management(gisFiberLinesCopyView).getOutput(0))
    
    if nullCount == 0:
        infile.write("All GIS conduit duct banks are in the UIT database\n\n")
        arcpy.SelectLayerByAttribute_management(gisFiberLinesCopyView,"CLEAR_SELECTION")
    else:
        #Do Not Delete CB - need to verify with survey that this CB has been removed.
        #Instead create list to review
        #This process may change once utility data is being transfered into GIS.
            
        sc3 = arcpy.SearchCursor(gisFiberLinesCopyView)
        infile.write("The following CB location should be verified for removal: \n\n")

        for row3 in sc3:
            if row3.getValue("uitFiberLinesExport.ID") == None:
                infile.write(str(row3.getValue("fiber_lines_copy.conduit_bank"))+"\n")                    
            del row3
        del sc3

    #Find enclosures that are in the UIT DB but not in the GIS DB
    infile.write("ENCLOSURES IN UIT THAT ARE NOT IN GIS\n")

    #Check for Temporary Missing Enclosures Table
    if arcpy.Exists(tempMissingEnclosures):
        tempMissingEnclosuresView = arcpy.MakeTableView_management(tempMissingEnclosures,'tempMissingEnclosuresView')
        rowCount = int(arcpy.GetCount_management(tempMissingEnclosuresView).getOutput(0))
        if rowCount != 0:
            tempMissingEnclosuresBackup = workspace+"//temp_missing_enclosures_"+str(today)
            arcpy.CopyRows_management(tempMissingEnclosuresView,tempMissingEnclosuresBackup)
            arcpy.DeleteRows_management(tempMissingEnclosuresView)
            infile.write("temp_missing_enclosures feature table contained old data.\nThis data was backed up at " + tempMissingEnclosuresBackup + ".\n\n")

    else:
        print "Temp missing enclosures table does not exist. Creating it now.\n"
        arcpy.CreateTable_management(workspace, "temp_missing_enclosures")
        tempMissingEnclosuresView = arcpy.MakeTableView_management(tempMissingEnclosures,"tempMissingEnclosuresView")

        arcpy.AddField_management(tempMissingEnclosuresView,"ID","LONG")
        arcpy.AddField_management(tempMissingEnclosuresView,"name","Text",25)
        arcpy.AddField_management(tempMissingEnclosuresView,"bldg","Text",10)
        arcpy.AddField_management(tempMissingEnclosuresView,"room","Text",10)
        arcpy.AddField_management(tempMissingEnclosuresView,"type","Text",25)
        
    arcpy.AddJoin_management(uitEnclosuresView,"ID",gisEnclosuresView,"ID","KEEP_ALL")
    sc4 = arcpy.SearchCursor(uitEnclosuresView)

    print "Missing Enclosures: \n"     
    for row4 in sc4:
        if row4.getValue("UUSD.DBO.Fiber_Enclosures.ID") == None:
            print row4.getValue("uitEnclosuresExport.ID")

            #Use insert cursor to write values in to temp table
            intcur2 = arcpy.InsertCursor(tempMissingEnclosures)
            icur2 = intcur2.newRow()
            icur2.setValue("ID", row4.getValue("uitEnclosuresExport.ID"))
            icur2.setValue("name", row4.getValue("uitEnclosuresExport.ENCLOSURE"))
            intcur2.insertRow(icur2)
            del intcur2
        del row4
    del sc4

    missingEnclosuresCount = arcpy.GetCount_management(tempMissingEnclosures).getOutput(0)

    print "There are "+str(missingEnclosuresCount)+" enclosures that are in the UIT DB that are not in the GIS DB."
    print "\nChecking to see of these enclosures match known missing enclosures"

    arcpy.RemoveJoin_management(uitEnclosuresView)
    arcpy.AddJoin_management(tempMissingEnclosuresView,"ID", knownMissingEnclosuresView,"UIT_Enclos","KEEP_ALL")

    knownMissingEnclosuresList = []

    sc5 = arcpy.SearchCursor(tempMissingEnclosuresView)
    for row5 in sc5:
        if row5.getValue("Fiber_Missing_Enclosures.UIT_Enclos") != None:
            knownMissingEnclosuresList.append(row5.getValue("Fiber_Missing_Enclosures.UIT_Enclos"))
        del row5
    del sc5

    arcpy.RemoveJoin_management(tempMissingEnclosuresView)

    if len(knownMissingEnclosuresList) > 0:
        #Delete known info and keep new
        where = "ID IN("+",".join([str(i) for i in knownMissingEnclosuresList])+")"
        arcpy.SelectLayerByAttribute_management(tempMissingEnclosuresView,"NEW_SELECTION",where)
        arcpy.DeleteRows_management(tempMissingEnclosuresView)

    missingEnclosuresResults = int(arcpy.GetCount_management(tempMissingEnclosuresView).getOutput(0))
    print "There are " + str(missingEnclosuresResults) + " new enclosures that need to be added to the GIS DB.\nCheck temp_missing_enclosures table for details.\n\n"
    infile.write("There are " + str(missingEnclosuresResults) + " new enclosures that need to be added to the GIS DB.\nCheck temp_missing_enclosures table for details.\n\n")

    if missingEnclosuresResults > 0:
    
        arcpy.AddJoin_management(tempMissingEnclosuresView,"ID",uitEnclosuresView,"ID","KEEP_COMMON")
        arcpy.CalculateField_management(tempMissingEnclosuresView,'temp_missing_enclosures.bldg','!uitEnclosuresExport.BN!','PYTHON_9.3')
        arcpy.CalculateField_management(tempMissingEnclosuresView,'temp_missing_enclosures.room','!uitEnclosuresExport.ROOM!','PYTHON_9.3')
        arcpy.CalculateField_management(tempMissingEnclosuresView,'temp_missing_enclosures.type','!uitEnclosuresExport.ENCLOSURE_CODE!','PYTHON_9.3')
        arcpy.RemoveJoin_management(tempMissingEnclosuresView)

    #Find Enclosures that are in GIS but not in UIT
    infile.write("ENCLOSURES IN GIS BUT NOT IN UIT DB\n")

    arcpy.SelectLayerByAttribute_management(gisEnclosuresView,"NEW_SELECTION","ID <> 0")
    arcpy.CopyFeatures_management(gisEnclosuresView,gisEnclosuresCopy)
    gisEnclosuresCopyView = arcpy.MakeFeatureLayer_management(gisEnclosuresCopy,"gisEnclosuresCopyView")

    arcpy.AddJoin_management(gisEnclosuresCopyView,"ID",uitEnclosuresView,"ID","KEEP_ALL")
    arcpy.SelectLayerByAttribute_management(gisEnclosuresCopyView,"NEW_SELECTION","uitEnclosuresExport.ID IS NULL")
    enclosureNullCount = int(arcpy.GetCount_management(gisEnclosuresCopyView).getOutput(0))

    if enclosureNullCount == 0:
        infile.write("All GIS Enclosures whose ID is NOT = 0 are also in the UIT database.\n\n")
        arcpy.SelectLayerByAttribute_management(gisEnclosuresCopyView,"CLEAR_SELECTION")
    else:
        arcpy.SelectLayerByAttribute_management(gisEnclosuresCopyView,"CLEAR_SELECTION")

        sc6 = arcpy.SearchCursor(gisEnclosuresCopyView)
        infile.write("The following Enclosures do not exist in the UIT DB and should be verified for removal:\n\n")
        for row6 in sc6:
            if row6.getValue("uitEnclosuresExport.ID") == None:
                infile.write(str(row6.getValue("gis_enclosures_copy.ID"))+"\n")
            del row6
        del sc6
        
    infile.close()
 
    #Delete Temp Data
    arcpy.Delete_management(uitFiberLinesIntExport)
    arcpy.Delete_management(uitFiberLinesExport)
    arcpy.Delete_management(gisFiberLinesCopy)
    arcpy.Delete_management(gisEnclosuresCopy)
    arcpy.Delete_management(uitEnclosuresExport)
    
    sendEmail()
    print "done"
    
except:
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])

    # Return python error messages for use in script tool or Python Window
    arcpy.AddError(pymsg)

    # Print Python error messages for use in Python / Python Window
    print(pymsg)
    infile.write("\nAn ERROR Occured:\n" + pymsg)
    infile.close()
    sendEmail()

    
