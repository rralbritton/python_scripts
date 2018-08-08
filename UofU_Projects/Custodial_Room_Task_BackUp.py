#Room_Task.py
#Populate Room_Task Linking Table

import arcpy, traceback, os, sys

arcpy.env.workspace = "S:\\Rachel\\Projects\\Custodial"
arcpy.env.overwrite = "True"

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName

Room_Table = "Database Connections\\ FM-GISDBTEST0.FM.UTAH.EDU.sde\\UUSD.DBO.custodial_m_m_prototype\\UUSD.DBO.Rooms_M2M"
O2MTask_Table = "S:\\Rachel\\Data\Custodial.gdb\\Cleaning"
Linking_Table = "S:\Rachel\Data\Custodial.gdb\Test_Linking_Table"
ClnSingleList = "S:\Rachel\Data\Custodial.gdb\Cleaning_SingleList"

#Create temporary layer files for further analysis
TableView = outName(O2MTask_Table,"_Lyr")
arcpy.MakeTableView_management(O2MTask_Table, TableView)

TableView2 = outName(Linking_Table,"_Lyr")
arcpy.MakeTableView_management(Linking_Table, TableView2)

#Go through rooms table line by line
#Use search cursor to read the selected feature class Area_ID

try:
    
    sc = arcpy.SearchCursor (Room_Table)

    for row in sc:
        
        #Get Area_ID
        RoomOID = row.OBJECTID
        RoomNum = row.Build_Rm
        AreaID = row.Area_ID
                                      
        #Open Cleaning table and do a select by attribute to find records that match Area_ID
        #that was found by the search cursor in the above operation
        
        SQL1 = "Area_ID =" + str(AreaID)
        arcpy.SelectLayerByAttribute_management(TableView,"NEW_SELECTION", SQL1)
        print arcpy.GetMessage(0)+"\n"

        #use another search cursor to read cleaning code values of selected records
        sc1 = arcpy.SearchCursor(TableView)
        for r in sc1:

            #Get Cleaning Codes
            ClnCode1 = r.Cleaning_C

            #Copy Room Object ID being read within the first search cursor
            #and associated cleaning codes into the clean_task table using an insert cursor
            intcur = arcpy.InsertCursor(Linking_Table)
            icur = intcur.newRow()
            icur.setValue("Cln_Code",ClnCode1)
            icur.setValue("RoomID",RoomOID)
            intcur.insertRow(icur)
            del intcur
        
        del r
        del sc1

        #Clear Selection and go to the next row item
        arcpy.SelectLayerByAttribute_management(TableView,"CLEAR_SELECTION")
            
    del row 
    del sc

    #Assign appropriate task ID's to tasks within the linking table
    #Task ID's are the the task object ID found in the Cleaning_SingleList table

    #Open a new search cursor

    sc3 = arcpy.SearchCursor(ClnSingleList)

    for rows in sc3:

        #Get Object ID and Cln. Code for selected task
        TaskOID = rows.OBJECTID
        ClnCode2 = rows.Cln_Code
        
        #Open Room_Task Linking Table and select all rows that contain the cleaning code being read by sc3
        SQL2 ="Cln_Code ="+"'"+ClnCode2+"'"
        arcpy.SelectLayerByAttribute_management(TableView2, "NEW_SELECTION", SQL2)
        print arcpy.GetMessage(0)+"\n"

        #Check to make sure records are being selected
        count = arcpy.GetCount_management(TableView2)
        print "There are "+str(count)+" records selected in "+TableView2+"\n"
        
        #For selected records, set the TaskID field = TaskOID within the Linking Table
        arcpy.CalculateField_management(TableView2,"TaskID", TaskOID, "VB")
        print arcpy.GetMessage(0)+"\n"

        #Clear selected features
        arcpy.SelectLayerByAttribute_management(TableView2, "CLEAR_SELECTION")

    del rows
    del sc3
        
    print "Done"

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
    
