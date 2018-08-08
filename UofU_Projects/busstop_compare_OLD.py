#Name:          busstop_compare.py
#Purpose:       Compares new UTA stops feature class to old UTA stops feature class.
#               Deletes old stops that no longers exists from stops feature class and
#               the routes related table. Adds new stops to the old stops feature class
#               and adds related records to the routes table for new stops.
            

import arcpy, os

#workspace & parameters
workspace = arcpy.env.workspace  = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde"
scratch = r"S:\Rachel\Data\UTA_Data.gdb"

#if not os.path.exists(workspace): os.makedirs(workspace)
arcpy.env.overwriteOutput = True

print "preparing data..."

#Input Data
newStops = r"S:\Rachel\Data\UtahTransitSystems_01172017\BusStops_UTA\BusStops_UTA.shp" #in FGDB
clipBoundary = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@FM-GISSQLHA_DEFAULT_VERSION.sde\uusd.DBO.cartographic_features\uusd.DBO.Carto_Bound" 
oldStops = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@FM-GISSQLHA_DEFAULT_VERSION.sde\uusd.DBO.Transportation\UUSD.DBO.uta_campus_bus_stops" 
routes = r"S:\Rachel\Data\UtahTransitSystems_01172017\BusRoutes_UTA\BusRoutes_UTA.shp" #the actual routes are not stored in the SDE because they're unneeded. This FC will be stored in a FGDB.
routesTable = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@FM-GISSQLHA_DEFAULT_VERSION.sde\UUSD.DBO.uta_campus_bus_routes" 

#Clip new stops dataset to campus boundary
clippedStops = scratch+"/clippedStops"
arcpy.Clip_analysis(newStops, clipBoundary, clippedStops)

#Counts record #'s in both new and old sets
oldStopsCount = arcpy.GetCount_management(oldStops)
print "There are "+str(int(oldStopsCount.getOutput(0)))+" old stops.\n"

newStopsCount = arcpy.GetCount_management(clippedStops)
print "There are "+str(int(newStopsCount.getOutput(0)))+" new stops.\n"

#Convert new & old stops to a feature layer
newStopsFL = "newStopsFL"
oldStopsFL = "oldStopsFL"
arcpy.MakeFeatureLayer_management(clippedStops, newStopsFL)
arcpy.MakeFeatureLayer_management(oldStops, oldStopsFL)

#Any old stop that does not intersect with a new stop should be deleted
#Select by Location
arcpy.SelectLayerByLocation_management(oldStopsFL,"INTERSECT",newStopsFL,"","NEW_SELECTION")
oldStopsCount2 = arcpy.GetCount_management(oldStopsFL)

if int(oldStopsCount.getOutput(0))> int(oldStopsCount2.getOutput(0)):  #if not all of the old stops are select, the non-slected ones no longer exist
    
    #Delete stops that don't intersect with new stops
    arcpy.SelectLayerByLocation_management(oldStopsFL,None, None,"","SWITCH_SELECTION")
    oldStopsCount3 = arcpy.GetCount_management(oldStopsFL)      

    print str(oldStopsCount3)+" stops no longer exist and will to be removed from the stops layer.\n"
    
    #Create a list of points that are to be deleted.
    #This is needed to select the related records out from the routes table.
    sc = arcpy.SearchCursor(oldStopsFL)
    list = []
    for line in sc:
        list.append(line.UTAStopID)
        del line
    del sc

    #Select these records from the existing routes table & delete
    arcpy.MakeTableView_management(routesTable,"routesTableView")

    #where = "UTAStopID IN ('" + '\',\''.join(list1)) + "')" #this works for string values
    where = "UTAStopID IN("+",".join([str(i) for i in list])+")"
    print where
           
    arcpy.SelectLayerByAttribute_management("routesTableView","NEW_SELECTION",where)
    routesCount = arcpy.GetCount_management("routesTableView")
    print str(routesCount)+" related route records have been selected to be deleted.\n"
    
    arcpy.DeleteRows_management("routesTableView")
    arcpy.DeleteFeatures_management(oldStopsFL)

else:
    print "All of the old stops intersect with the new stops.\n"
    print "Checking to see if new stops were added.\n"
    
#Check to see if new stops have been created
arcpy.SelectLayerByAttribute_management(oldStopsFL,"CLEAR_SELECTION")    
arcpy.SelectLayerByLocation_management(newStopsFL,"INTERSECT",oldStopsFL,"","NEW_SELECTION")
newStopsCount2 = arcpy.GetCount_management(newStopsFL)

#If not all new stops intersect with old stops, then new stops need to be
#added to the oldstops file. 

if int(newStopsCount2.getOutput(0))<int(newStopsCount.getOutput(0)):

    arcpy.SelectLayerByLocation_management(newStopsFL, None,None,"","SWITCH_SELECTION")
    
    newStopsFC = arcpy.CopyFeatures_management(newStopsFL, scratch+"/newStopsFC")
    newStopsCount3 = arcpy.GetCount_management(newStopsFC)
    print str(newStopsCount3)+" new stops have been created since the last update.\n"
    print "The following new stops are being appended the exisiting stops feature class:"

    sc1 = arcpy.SearchCursor(newStopsFC)
    for row in sc1:
        print row.UTAStopID     
    del row
    del sc1
                                       
    #Create a spatial join between new stops and their intersecting routes
    spatialJoin = scratch+"\spatialJoin"
    arcpy.SpatialJoin_analysis(routes,newStopsFL,spatialJoin,"JOIN_ONE_TO_ONE","KEEP_COMMON","","WITHIN_A_DISTANCE",20)
    print arcpy.GetMessages(0)
    
    #Append the geometry of the new stops to the old stop layer
    arcpy.AddField_management(newStopsFC,"newID","LONG")
    print arcpy.GetMessages(0)
    arcpy.CalculateField_management(newStopsFC,"newID","!UTAStopID!","PYTHON")
    print arcpy.GetMessages(0)
    arcpy.DeleteField_management(newStopsFC,["StopId","StreetNum","OnStreet","AtStreet","City","InService","Bench","Shelter","Lighting","Garbage","Bicycle","Transfer","LocationUs","UTAStopID"])  
    print arcpy.GetMessages(0)
    
    #Create field map  objects and properties in order to append new stops to old stops FC
    #Resource: http://pro.arcgis.com/en/pro-app/arcpy/classes/fieldmappings.htm

    fieldmapping = arcpy.FieldMappings()
    fm_stopName =arcpy.FieldMap() 
    fm_UTAStopID = arcpy.FieldMap()

    fieldmapping.addTable(newStopsFC) #input
            
    fm_stopName.addInputField(newStopsFC, "StopName")
    f_stopName = fm_stopName.outputField
    f_stopName.name = "StopName"
    fm_stopName.outputField = f_stopName
    fieldmapping.addFieldMap(fm_stopName)
    
    fm_UTAStopID.addInputField(newStopsFC,"newID")
    f_UTAStopID = fm_UTAStopID.outputField
    f_UTAStopID.name = "UTAStopID"
    fm_UTAStopID.outputField = f_UTAStopID
    fieldmapping.addFieldMap(fm_UTAStopID)
    
    arcpy.Append_management(newStopsFC,oldStopsFL,"NO_TEST",fieldmapping) 

    #Fill in routes table (related table)
    #Use a cursor to read the selected route files
    #And an insert cursor to add data to the old routes file

    sc2 = arcpy.SearchCursor(spatialJoin)
    for rows in sc2:

        #Get field values
        lineAbbr = rows.LineAbbr #Route Number in actual routes table
        stopID = rows.UTAStopID

        #Use insert cursor to write values being read above to the routes table
        intcur = arcpy.InsertCursor(routesTable)
        icur = intcur.newRow()
        icur.setValue("RouteNum", lineAbbr)
        icur.setValue("UTAStopID",stopID)
        intcur.insertRow(icur)
        del intcur
        
    del rows
    del sc2

    #Select out records that were just added
    routesTableTV = arcpy.MakeTableView_management(routesTable, workspace+"\routesTableTV")
    arcpy.SelectLayerByAttribute_management(routesTableTV,"NEW_SELECTION","Website = ''")
    
    #Add URL to routes table
    fields = ("RouteNum","Website")
    with arcpy.da.UpdateCursor(routesTable,fields) as cursor:
        for row in cursor:
            if(row[0] == "11"):
                row[1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route11"
            elif(row [0] == "17"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route17"
            elif(row [0] == "2"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route2"
            elif (row[0] =="21"):
                row[1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route21"
            elif (row[0] =="213"):
                row[1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route213"
            elif (row [0] == "223"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route223"
            elif (row [0] == "228"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route228"
            elif (row [0] == "2X"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route2X"
            elif (row [0] == "3"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route3"
            elif (row [0] == "313"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route313"
            elif (row [0] == "354"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route354"
            elif (row [0] == "455"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route455"
            elif (row [0] == "473"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route473"
            elif (row [0] == "9"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route9"
            elif (row [0] == "6"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route6"
            elif (row [0] == "902"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route902"

            cursor.updateRow(row)

            #Delete spatial join
            arcpy.Delete_management(spatialJoin)
            arcpy.Delete_management(newStopsFC)

else:
                           
    print "no new stops were added.\Updates are complete.n\checking for valid URL's now...\n\n"

#Delete Temp Files
arcpy.Delete_management(clippedStops)

#Check that URL links are valid
import BusStops_CheckURL
BusStops_CheckURL 
    
print "done.\ncheck both route and stops tables for null values"

