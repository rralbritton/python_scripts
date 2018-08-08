# Name:         ephone_data_management.py
# Purpose:      The purpose of this script to to provide QA/QC for ephone data
#               as well as to keep ephone phone_status current.
#               The ephone overall phone status is determined by a combination
#               of factors, and this status changes monthly after inspections
#               are complete, and may change throughout the month as ephone work
#               orders are completed. The purpose of this script is to calculate 
#               the overall phone status based on predetermined criteria.
#               Emergency phones that appear on the campus map are also
#               based on this overall phone status. So updated phone status
#               values must also be transfered over from the latest inventory
#               table to the parent feature class.
#
# Criteria:     PHONE_STATUS
#               If ANY of the following  = True, then ephone 'phone status' = Not functional
#               Device Button = NEVER calls ||
#               Dropped Call = Call was dropped ||
#               Outbound Audibility = Dispatch CAN NOT hear you ||
#               Inbound Audibility = You CAN NOT hear Dispatch
#
#               If ANY of the following are true and none of the above apply then
#               ephone 'phone status' = Partially functional
#               Device Button = SOMETIME calls ||
#               Phone Static = Has static
#
#               INSEPCTED
#
#Last Updated:  5/172018
#Author:        Rachel Albritton, Facilities Management
###################################################################################################

import arcpy, datetime

arcpy.env.workspace = r"C:\Users\u6003632\Google Drive\Work\Projects\Emergency_Phones\ephones.gdb"
arcpy.env.overwriteOutput = True
ephones = r"C:\Users\u6003632\Google Drive\Work\Projects\Emergency_Phones\ephones.gdb\Emergency_Phones"
ephone_newest_inspections = r"C:\Users\u6003632\Google Drive\Work\Projects\Emergency_Phones\ephones.gdb\ephone_newest_inspections"

##Create table and FC views 
newestInspectionLayer = arcpy.MakeTableView_management(ephone_newest_inspections,'newestInspectionLayer')
ephoneLayer = arcpy.MakeFeatureLayer_management(ephones, 'ephonesLayer')

##################
## PHONE STATUS ##
##################

join newInspectionsLayer records to ephones
arcpy.AddJoin_management(ephoneLayer,'aim_asset_id', newestInspectionLayer,'aim_asset_id','KEEP_COMMON')
fieldList = arcpy.ListFields(ephoneLayer)
for field in fieldList:
    print field.name

## NOT FUNCTIONAL ##   
notFunctionalSQL = "ephone_newest_inspections.device_button = 'NEVER calls' OR ephone_newest_inspections.dropped_call = 'Call was dropped' OR ephone_newest_inspections.out_audio = 'Dispatch CANNOT hear you'  OR ephone_newest_inspections.in_audio = 'You CAN NOT hear Dispatch'"
arcpy.SelectLayerByAttribute_management(ephoneLayer, 'NEW_SELECTION', notFunctionalSQL)
arcpy.CalculateField_management(ephoneLayer,'Emergency_Phones.phone_status',"\'Not Functional\'",'PYTHON_9.3')
count1 = arcpy.GetCount_management(ephoneLayer).getOutput(0)
print count1

#### PARTIALLY FUNCTIONAL ##
partFunctionalSQL = "(ephone_newest_inspections.device_button = 'SOMETIMES calls' OR ephone_newest_inspections.phone_static = 'Has static') AND ephone_newest_inspections.dropped_call = 'Call was NOT dropped' AND ephone_newest_inspections.out_audio = 'Dispatch CAN hear you' AND ephone_newest_inspections.in_audio = 'You CAN hear dispatch'"
arcpy.SelectLayerByAttribute_management(ephoneLayer, 'NEW_SELECTION', partFunctionalSQL)
arcpy.CalculateField_management(ephoneLayer,'Emergency_Phones.phone_status',"\'Partially Functional\'",'PYTHON_9.3')
count2 = arcpy.GetCount_management(ephoneLayer).getOutput(0)
print count2

#### FUNCTIONAL ##
functionalSQL = "ephone_newest_inspections.device_button = 'ALWAYS calls' AND ephone_newest_inspections.dropped_call = 'Call was NOT dropped' AND ephone_newest_inspections.out_audio = 'Dispatch CAN hear you' AND ephone_newest_inspections.in_audio = 'You CAN hear dispatch' AND ephone_newest_inspections.phone_static = 'Does NOT have static'"
arcpy.SelectLayerByAttribute_management(ephoneLayer, 'NEW_SELECTION', functionalSQL)
arcpy.CalculateField_management(ephoneLayer,'Emergency_Phones.phone_status',"\'Functional\'",'PYTHON_9.3')
count3 = arcpy.GetCount_management(ephoneLayer).getOutput(0)
print count3

print 'Phone Status done'

###############
## Inspected ##
###############

yesterday = datetime.datetime.now() - datetime.timedelta(hours = 24)
#inspectedSQL = 'ephone_newest_inspections.test_date < date \'' + (yesterday).strftime('%Y-%m-%d %H:%M') + '\''
inspectedSQL = '(Emergency_Phones.inspected IS NULL OR Emergency_Phones.inspected =  \'False\' ) AND ephone_newest_inspections.last_edited_date < date \'' + (yesterday).strftime('%Y-%m-%d %H:%M') + '\''

##ephones should still be joined to newest inspections
arcpy.SelectLayerByAttribute_management(ephoneLayer, 'NEW_SELECTION', inspectedSQL)
arcpy.CalculateField_management(ephoneLayer,'Emergency_Phones.inspected','\'True\'', 'PYTHON_9.3')

print 'Phone Inspection fields updated'

## KEEP FOR NOW IN CASE SQL VIEW DOES NOT WORK ##

##fieldList = arcpy.ListFields(ephoneLayer)
##for field in fieldList:
##    print field.name
##    
###get newest inspections reports
##
##cursor = arcpy.da.SearchCursor(inspections,'test_date')
##for row in cursor:
##    inspectionDates.append(row)
##
##maxDate = [max(inspectionDates)][0][0].strftime('%m/%d/%Y')
##print maxDate
##
###use max date to select all records in inspection table with that date
##inspectionLayer = arcpy.MakeTableView_management(inspections,'inspectionLayer',"test_date = '"+maxDate +"'")
