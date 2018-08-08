#Name:          update_Structures_Copy.py
#
#Purpose:       The stuctures_COPY_DO_NOT_DELETE feature class is used in projects          #
#               where clients need access to edit related data to the structures            #
#               feature class. Currently, the ability to edit related tables in AGOL        #
#               also requires that users have access to the geometry of the related         #
#               FC, and at minimum have the ability to create new features. For             # 
#               security purposes, FM GIS does not want to allow this access, and           #
#               created the structures_COPY_DO_NOT_DELETE feature class as an alternative   #
#               solution.                                                                   #
#               The purpose of this script is to update the the                             #
#               strucutres_COPY_DO_NOT_DELETE feature class every 24 hours                  #
#               in order to keep the copy current.                                          #
#                                                                                           #
#Assumptions:  This script assumes that building numbers are NOT IN (0,-1)                  #
#              AND lifecycle IN( 'Active' , 'Construction' )                                #
#                                                                                           #            
#Author:        Rachel Albritton     Facilities Management                                  #
#                                                                                           #
#Last Update:   March 22, 2017                                                              #
#############################################################################################

import sys, os, arcpy, datetime, traceback, smtplib
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.mime.application import MIMEApplication

#Set Workspace
arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest"
arcpy.env.overwriteOutput = True

#Set Varaiables
structures_COPY = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\UUSD.DBO.structures_COPY_DO_NOT_DELETE"
orginal_Structures = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\UUSD.DBO.structure"
buildings_eap_table = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\UUSD.DBO.Buildings_EAP"
buildings_eap_copy = r"\\ad.utah.edu\sys\FM\gis\ags_directories\Structures_Copy_Management\building_eap_copy.dbf"
buildings_eap_backup = r"\\ad.utah.edu\sys\FM\gis\ags_directories\Structures_Copy_Management\EAP_Buildings_Backup.gdb\Buildings_EAP"
structures_View = "structures_view"
structures_COPY_View = "structures_copy_view"
email = r"\\ad.utah.edu\sys\FM\gis\ags_directories\Structures_Copy_Management\email.txt"

try:
    #Create layers
    arcpy.MakeFeatureLayer_management(orginal_Structures, structures_View, "building_number NOT IN(0,-1) AND lifecycle IN( 'Active' , 'Construction' )")
    arcpy.MakeFeatureLayer_management(structures_COPY, structures_COPY_View, "building_number NOT IN(0,-1) AND lifecycle IN( 'Active' , 'Construction' )")

    #Find out if any records have been created in the orginal strucutres FC in the past 24 hours
    UTCNowTime = datetime.date.today()
    UTCPriorTime = datetime.date.today() - datetime.timedelta(hours = 24)
    SQL = "created_date >="+ "'"+UTCPriorTime.strftime('%Y-%m-%d')+"'"
    arcpy.SelectLayerByAttribute_management(structures_View,"NEW_SELECTION", SQL)

    #Count number of records selected
    results = int(arcpy.GetCount_management(structures_View).getOutput(0))
    print "Number of new records created: "+str(results)

    if results > 0:
            
        #Append selected record to the structures_COPY FC
        arcpy.Append_management(structures_View, structures_COPY_View, "TEST")

    #Check to see if any structures have been modified
    arcpy.SelectLayerByAttribute_management(structures_View,"CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management(structures_View,"NEW_SELECTION","last_edited_date >="+"'"+UTCPriorTime.strftime('%Y-%m-%d')+"'")
                                                    
    #Count number of records selected
    count = int(arcpy.GetCount_management(structures_View).getOutput(0))
    print "Number of modified records: "+str(count)

    if count > 0:

        #Create a list of the building numbers that have been modified
        #Use this list to query the structures_copy_view and delete associate records
        #These records will be replaced with the most updated records from the orginal structures feature class
       
        sc = arcpy.SearchCursor(structures_View)
        list = []
        for line in sc:
            list.append(line.building_number)
            del line
        del sc
        
        SQL_Copy = "building_number IN ("+",".join([str(i) for i in list])+")"
        arcpy.SelectLayerByAttribute_management(structures_COPY_View,"NEW_SELECTION",SQL_Copy)

        #When the record in the structures copy table gets deleted the foreign key
        #in the related table will become Null. Before deleting these corresponding related records,
        #create a backup of the Buildings_EAP table in case something goes wrong in the process, and
        #use select by attribute (building number) to find realted records and copy to a temporary table.
        arcpy.MakeTableView_management(buildings_eap_table,"buildings_eap_view")
        arcpy.CopyRows_management("buildings_eap_view", buildings_eap_backup)
        pre_table_count = int(arcpy.GetCount_management(buildings_eap_table).getOutput(0))
        
        arcpy.SelectLayerByAttribute_management("buildings_eap_view", "NEW_SELECTION", SQL_Copy)
        arcpy.CopyRows_management("buildings_eap_view", buildings_eap_copy)
        
        #Delete rows in structures copy table & rows in related table that having a matching building number
        arcpy.DeleteRows_management(structures_COPY_View)
        arcpy.DeleteRows_management("buildings_eap_view")

        #Append updated rows from orginal structures into the the copy
        arcpy.Append_management(structures_View, structures_COPY_View, "TEST")

        #The copied table column names will not match the target table.
        #Create a field map
        eapID = arcpy.FieldMap()
        bn = arcpy.FieldMap()
        fms = arcpy.FieldMappings()

        ##Get field names of eap_id and building number for both orginal files
        orginalEAP = "eap_id"
        copiedEAP = "eap_id"
        
        orignalBN = "building_number"
        copiedBN = "building_n"

        ##Add fields to their corresponding field map objects
        eapID.addInputField("buildings_eap_view",orginalEAP)
        eapID.addInputField(buildings_eap_copy,copiedEAP)

        bn.addInputField("buildings_eap_view",orignalBN)
        bn.addInputField(buildings_eap_copy,copiedBN)
        
        ##Set the out field properties for both FieldMap objects
        eap_id = eapID.outputField
        eap_id.name = "eap_id"       
        eapID.outputFiled = eap_id
        
        bldgnum = bn.outputField
        bldgnum.name = "building_number"
        bn.outputField = bldgnum

        ##Add the FieldMap objects to the FieldMappings object
        fms.addFieldMap(eapID)
        fms.addFieldMap(bn)

        #Merge copied table features to the related table view
        arcpy.Append_management(buildings_eap_copy,"buildings_eap_view","NO_TEST",fms)

        #Check to make sure the merge was succesful
        #Get count
        post_count_table = int(arcpy.GetCount_management(buildings_eap_table).getOutput(0))
            
        #Delete table copy
        arcpy.Delete_management(buildings_eap_copy)

        #Send Email Report if any changes were made
        if results or count > 0:

            #Open email file
            infile = open(email,'w')
            infile.write("Number if new records: "+str(results)+"\n")
            infile.write("Number of new modified records: " + str(count)+"\n")
            
            if count > 0:
                infile.write("Modifications were made to the following building numbers: \n")
                for items in list:
                    infile.write("%s\n" % items)
                
                #Count should equal the table orginal count before merge
                if pre_table_count == post_count_table:
                    infile.write("Table append OK.")
                else:
                    infile.write("An error occured with the table Append.\n")
                    infile.write("Pre table count = "+ str(pre_table_count)+"\n")
                    infile.write("Post table count = " + str(post_table_count)+"\n")
            infile.close()

        #Recipient's Email
        Recp = ['Rachel.Albritton@fm.utah.edu']
        Sender = "GIS_Automation@fm.utah.edu"
        msg = MIMEMultipart()
        msg['Subject'] = "Structures Copy Update Report"
        msg['From'] = Sender
        msg['To'] = ",".join(Recp)
        
        #Write Email Body (Status Report)
        report = open(email,'rb')
        body = MIMEText(report.read())
        msg.attach(body)

        # Send the message via the SMTP server
        Host = "smtp.utah.edu"
        s = smtplib.SMTP(Host)
        s.sendmail(Sender, Recp, msg.as_string())
        s.quit()
except:
    
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    print pymsg

    #Email that an error occured
    errorFile = r"\\ad.utah.edu\sys\FM\gis\ags_directories\Structures_Copy_Management\errors.txt"
    erfile = open(errorFile,'w')
    erfile.write("An error occured while analyzing the strucutures COPY data\n\n")
    erfile.write(pymsg)
    erfile.close()
    
    #Recipient's Email
    Recp = ['Rachel.Albritton@fm.utah.edu']
    Sender = "GIS_Automation@fm.utah.edu"
    msg = MIMEMultipart()
    msg['Subject'] = "ERROR - Structures COPY Report - ERROR"  
    msg['From'] = Sender
    msg['To'] = ",".join(Recp)
    
    #Write Email Body (Status Report)
    report = open(errorFile,'rb')
    body = MIMEText(report.read())
    msg.attach(body)
    
print "done"
