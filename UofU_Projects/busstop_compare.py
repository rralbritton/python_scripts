#Name:          updateUTABusStopsData.py
#
#Purpose:       To update the UTA bus stop locations and associated routes table that is used
#               in the campus map. This script clips the UTA bus stop data to the campus area,
#               and buffers those stop points so that they intersect with the UTA Routes FC.
#               Several tests were done to determine an intial buffer size of 12 meters. This
#               allows most stops to intersect with routes, however, there is currenty 15-20 that
#               need a larger buffer. This subset of points is extracted out and given a buffer of 18m.
#               Both sets of buffers are spatailly joined with the routes FC and cursors are used to
#               to read/write the realted routes data. As of summer 2017 there 2 stops that should be
#               double checked manually to see if realted routes have changed. These are noted at the
#               end of the script.
#               Analysis/updates are done in test then loaded into production
#
#Author:        Rachel Albritton
#
#Last Updated:  June 21, 2017
##########################################################################################################

import arcpy, os, traceback

#workspace & parameters
arcpy.env.overwriteOutput = True
workspace = arcpy.env.workspace  = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde"
scratch = r"S:\Rachel\Data\UTA_Data.gdb"
edit = arcpy.da.Editor(workspace)

#Input Data
#FGDB 
clipBoundary = r"S:\Rachel\Data\Cartography.gdb\Carto_Bound_old" 
newStops = r"S:\Rachel\Data\BusStops_UTA_04232018.gdb\BusStops_UTA"
routes = r"S:\Rachel\Data\BusRoutes_UTA_04232018.gdb\BusRoutes_UTA" #the actual routes are not stored in the SDE because they're unneeded.

#Enterprise DB
oldStops = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\uusd.DBO.Transportation\UUSD.DBO.uta_campus_bus_stops" #whats currently in prod
routesTable = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\UUSD.DBO.uta_campus_bus_routes" #whats currently in prod

print "Checking & Updating Stop Locations...\n"

try:
    #Get new stops
    clippedStops = scratch+"/uta_clipped_stops"
    arcpy.Clip_analysis(newStops, clipBoundary, clippedStops)
    arcpy.DeleteField_management(clippedStops,["StopId","StreetNum","OnStreet","AtStreet","City","InService","Bench","Shelter","Lighting","Garbage","Bicycle","Transfer","LocationUs"])

    #Counts record #'s in both new and old sets
    oldStopsCount = int(arcpy.GetCount_management(oldStops).getOutput(0))
    print "There are "+str(oldStopsCount)+" old stops.\n"

    newStopsCount = int(arcpy.GetCount_management(clippedStops).getOutput(0))
    print "There are "+str(newStopsCount)+" new stops.\n"

    #Create Feature Layers for selection analysis
    clippedStopsFL = arcpy.MakeFeatureLayer_management(clippedStops,"clippedStopsFL")
    oldStopsFL = arcpy.MakeFeatureLayer_management(oldStops,"oldStopsFL")

    #Any old stop that does not intersect with a new stop should be deleted
    #Select by Location
    arcpy.SelectLayerByLocation_management(oldStopsFL,"WITHIN_A_DISTANCE",clippedStopsFL,2,"NEW_SELECTION")
    arcpy.SelectLayerByAttribute_management(oldStopsFL,"SWITCH_SELECTION")
    oldStopsCount2 = int(arcpy.GetCount_management(oldStopsFL).getOutput(0))

    if oldStopsCount2 > 0:  #if all of the old stops are not selected, the non-selected ones no longer exist

        print str(oldStopsCount2) +" stops no longer exist and are being deleted."
        
        #Delete stops that don't intersect with new stops
        #Must delete the associated related records first
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
        arcpy.DeleteRows_management(oldStopsFL)
        oldStopsCount3 = arcpy.GetCount_management(oldStopsFL).getOutput(0)
        print "Old Stops Layer now has "+oldStopsCount3+" stops."

    else:
        print "All of the old stops intersect with the new stops.\n"
        print "Checking to see if new stops were added.\n\n"

    #Check to see if new stops have been created
    arcpy.SelectLayerByAttribute_management(oldStopsFL,"CLEAR_SELECTION")    
    arcpy.SelectLayerByLocation_management(clippedStopsFL,"WITHIN_A_DISTANCE",oldStopsFL,2,"NEW_SELECTION")
    arcpy.SelectLayerByAttribute_management(clippedStopsFL,"SWITCH_SELECTION")
    newStopsCount2 = int(arcpy.GetCount_management(clippedStopsFL).getOutput(0))

    #If newStops2 Count > 0 then new stops have been added

    if newStopsCount2 > 0:
        
        print str(newStopsCount2) +" new stops added.\nnew stops are being appended to the existing stops layer now.\n"
        stopsToAdd = scratch+"/stopsToAdd"
        arcpy.CopyFeatures_management(clippedStopsFL,stopsToAdd)
        
        #append new stops to old stops
        #Create field map  objects and properties in order to append new stops to old stops FC
        #Resource: http://pro.arcgis.com/en/pro-app/arcpy/classes/fieldmappings.htm

        fieldmapping = arcpy.FieldMappings()
        fm_stopName =arcpy.FieldMap() 
        fm_UTAStopID = arcpy.FieldMap()

        fieldmapping.addTable(stopsToAdd) #input
                
        fm_stopName.addInputField(stopsToAdd, "StopName")
        f_stopName = fm_stopName.outputField
        f_stopName.name = "StopName"
        fm_stopName.outputField = f_stopName
        fieldmapping.addFieldMap(fm_stopName)
        
        fm_UTAStopID.addInputField(stopsToAdd,"StopAbbr")
        f_UTAStopID = fm_UTAStopID.outputField
        f_UTAStopID.name = "UTAStopID"
        fm_UTAStopID.outputField = f_UTAStopID
        fieldmapping.addFieldMap(fm_UTAStopID)

        arcpy.Append_management(stopsToAdd,oldStopsFL,"NO_TEST",fieldmapping) 
        oldStopsCount4 = arcpy.GetCount_management(oldStopsFL).getOutput(0)
        print "Old Stops Layer now has "+oldStopsCount4+" stops after Append.\n"
      
    else:
                               
        print "no new stops were added.\n"

    print "All stop locations have been updated.\nUpdating route information now"
        
    #begin by finding all stops that are within 12m of route line(s)
    #NOTE: A 12m Buffer is the Max distance that can be used without a buffer intersecting
    #a routeline that it should not intersect.
    #This inital buffer will leave approx 15 lines w/o route associations.
    #A second buffer analysis with an 18m buffer was tested to be sufficent to capture moset of the
    #remaing stop/route intersections. 
    routesFL = arcpy.MakeFeatureLayer_management(routes, "routesFL")
    arcpy.SelectLayerByLocation_management(oldStopsFL,"WITHIN_A_DISTANCE",routesFL,12,"NEW_SELECTION")
    bufferedStops12 = scratch+"/bufferedStops12"
    arcpy.Buffer_analysis(oldStopsFL, bufferedStops12,12,"FULL","ROUND","LIST",["UTAStopID","StopName"],"PLANAR")

    #Second Buffer Analysis
    #Remove records with UTAStopID 126551. This stop is at an intersection
    #and the buffer intersects routes that are not assigned to the stop. Do this one manually.
    #Also remove UTAStopID 101919. This stop is approximately 66m away from the route, and will be done
    #seperately.
    arcpy.SelectLayerByAttribute_management(oldStopsFL,"SWITCH_SELECTION")
    arcpy.SelectLayerByAttribute_management(oldStopsFL,"REMOVE_FROM_SELECTION","UTAStopID IN(126551,101919)")
    count = int(arcpy.GetCount_management(oldStopsFL).getOutput(0))
    print count
    bufferedStops18 = scratch+"/bufferedStops18"
    arcpy.Buffer_analysis(oldStopsFL,bufferedStops18,18,"FULL","ROUND","LIST",["UTAStopID","StopName"],"PLANAR")

    #Merge buffer files
    bufferMerge = scratch+"/bufferMerge"
    arcpy.Merge_management([bufferedStops12, bufferedStops18],bufferMerge)
    
    #Delete all related records in the routes table except for UTAStopIDs 101919 & 126551
    routesTableView = arcpy.MakeTableView_management(routesTable, "routesTableView")
    arcpy.SelectLayerByAttribute_management(routesTableView, "NEW_SELECTION", "UTAStopID NOT IN(101919,126551)")
    arcpy.DeleteRows_management(routesTableView)

    #Create a spatial join between buffered stops and routes
    #Fill in routes table (related table)
    #Use a cursor to read the selected route files
    #And an insert cursor to add data to the old routes file

    spatialJoin = scratch+"/spatialJoin"
    bufferMergeFL = arcpy.MakeFeatureLayer_management(bufferMerge,'bufferMergeFL')
    arcpy.SpatialJoin_analysis(bufferMergeFL,routesFL,spatialJoin, "JOIN_ONE_TO_MANY","","","INTERSECT")

    sc = arcpy.SearchCursor(spatialJoin)
    print "Spatial Join :"
    for row in sc:
        
        #Get Field Values
        lineAbbr = row.LineAbbr
        stopID = row.UTAStopID

        if lineAbbr != None:
            print str(stopID)+" - "+ str(lineAbbr)
            
            #Use insert cursor to write values to the routes table
            intcur = arcpy.InsertCursor(routesTable)
            icur = intcur.newRow()
            icur.setValue("RouteNum", lineAbbr)
            icur.setValue("UTAStopID",stopID)
            intcur.insertRow(icur)
            del intcur
            
        del row
    del sc

    #Add URL to routes table
    fields = ("RouteNum","Website")
    edit.startEditing(False, True) #Multi-User mode must be set to true or error will occur
    edit.startOperation()
    with arcpy.da.UpdateCursor(routesTable,fields) as cursor:
        for row in cursor:
            if(row[0] == "11"):
                row[1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/11-11th-Avenue"
            elif(row [0] == "17"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/17-1700-South"
            elif(row [0] == "2"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route2"
            elif (row[0] =="21"):
                row[1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route21"
            elif (row[0] =="213"):
                row[1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route213"
            elif (row[0] =="220"):
                row[1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/220-Highland-Drive-1300-East"
            elif (row [0] == "223"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route223"
            elif (row [0] == "228"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/228-Foothill-Blvd-2700-East"
            elif (row [0] == "2X"):
                row [1] = "http://www.rideuta.com/mc/?page=Bus-BusHome-Route2X"
            elif (row [0] == "3"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/3-3rd-Avenue"
            elif (row [0] == "313"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/313-South-Valley-U-of-U-Fast-Bus"
            elif (row [0] == "354"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/354-Sandy-U-of-U-Fast-Bus"
            elif (row [0] == "455"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/455-UofU-Davis-County-Weber-State-University"
            elif (row [0] == "473"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/473-SLC-Ogden-Hwy-Express"
            elif (row [0] == "9"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/9-9th-South"
            elif (row [0] == "6"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/6-6th-Avenue"
            elif (row [0] == "902"):
                row [1] = "http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/902-PC-SLC-Connect"

            cursor.updateRow(row)
    edit.stopOperation()
    edit.stopEditing(True)

    #Check that URL links are valid
    import BusStops_CheckURL
    BusStops_CheckURL
            
    print "\nCheckout UTAStopIDs 126551 & 101919 to see if associated routes have changed"
    print "\nreview buffer data and check data quality"
    print "\nreview routes table and make sure there are no null website fields"
    print "done"

except:
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    arcpy.AddError(pymsg)
    print(pymsg)
  
    





