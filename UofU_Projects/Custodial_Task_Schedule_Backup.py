#Task_Schedule.py
#Populates the Task_Schedule linking table

import arcpy, traceback

arcpy.env.workspace = "S:\\Rachel\\Projects\\Custodial"
arcpy.env.overwrite = "True"

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName

#Variables
TaskTable = "Database Connections\ FM-GISDBTEST0.FM.UTAH.EDU.sde\UUSD.DBO.Cleaning"
ScheduleTable = "Database Connections\ FM-GISDBTEST0.FM.UTAH.EDU.sde\UUSD.DBO.Custodial_Schedule"
LinkingTable ="Database Connections\ FM-GISDBTEST0.FM.UTAH.EDU.sde\UUSD.DBO.Custodial_Clean_Schedule"

#populate linking table based on task frequency
#task frequiences are listed int the task table
#frequiences: 
#d = daily = Monday-Friday
#1 = Monday
#18 = Tuesday
#3 = Wednesday
#4 = Thursday
#5 = Friday

#integer values for weekdays are equaly to the days onject id in the schedule table

#w = weekly = Friday

#Use search cursor to read the frequency of a task

sc = arcpy.SearchCursor (TaskTable)

for row in sc:

    #Get values
    TaskOID = row.OBJECTID
    Freq = row.Freq

    print str(TaskOID)+" - "+Freq+"\n"
    
    #Start insert cursor to insert values into the lonking table
    
    ic = arcpy.InsertCursor(LinkingTable)
    i = ic.newRow()
    
    if row.freq == "d":
        i.setValue("Tasks",TaskOID)
        i.setValue("Schedule", 1)
        ic.insertRow(i)
        i.setValue("Tasks",TaskOID)
        i.setValue("Schedule", 18)
        ic.insertRow(i)
        i.setValue("Tasks",TaskOID)
        i.setValue("Schedule", 3)
        ic.insertRow(i)
        i.setValue("Tasks",TaskOID)
        i.setValue("Schedule", 4)
        ic.insertRow(i)
        i.setValue("Tasks",TaskOID)
        i.setValue("Schedule", 5)
        ic.insertRow(i)
        
    elif row.freq == "w":
        i.setValue("Tasks",TaskOID)
        i.setValue("Schedule", 5)
        ic.insertRow(i)
        
    else:
        i.setValue("Tasks",TaskOID)
        i.setValue("Schedule", 0)
        ic.insertRow(i)
    del ic

del row
del sc

print "Done"

        
        
    
