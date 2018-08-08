##-------------------------------------------------------------------------------
 #Name:         OceanFront_Viewshed.py
 #Purpose:      Calculates viewshed, in degrees, for all points within a point file
 #Author:       Rachel Albritton
# Last Updated: October 19, 2013

#Inputs:        This script takes NINE inputs. Each are described below
                #0 = Workspace. This is typically where the folder data is located
                #1 = Output workspace, the folder where you want the results saved.
                #2 = Observation points
                #3 = Building footprints
                #4 = Elevation
                #5 = BareElevation = Elevation that parcel sits at
                #6 = Ocean
                #7 = Floor Field - the feild located within the observation point file
                     #that contains the number f floors for each record
                #8 = Year the anaylsis is for

#Assumptions:   This tool assumes that all data inputs have been projected into a
                #coordinate system that has linear units. Angular units will provide
                #incorrect results, and may cause the script to fail completely.

                #This script also assumes that null values that may be present
                #within the elevation data have been converted to a value of 0.
                #The Raster_Fix.py script located within this tool box will
                #complete this task.             
##-------------------------------------------------------------------------------

import arcpy, os, shutil, datetime
from arcpy import env
from arcpy.sa import*

#set workspaces
arcpy.env.workspace = arcpy.GetParameterAsText(0) 
outputWorkspace = arcpy.GetParameterAsText(1) 
arcpy.env.overwriteOutput = True

#Check out the ArcGIS 3D Analyst extension license
arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("Spatial")

arcpy.SetProgressor("default","Conducting Viewshed Analysis")

#Variables
ObsPts = arcpy.GetParameterAsText(2)
footprint =  arcpy.GetParameterAsText(3) 
Elevation = arcpy.GetParameterAsText(4)
BareElevation = arcpy.GetParameterAsText(5)
Ocean = arcpy.GetParameterAsText(6)
FloorField = arcpy.GetParameterAsText(7) 
Year = arcpy.GetParameterAsText(8)

#Set analysis extent to elevation raster
arcpy.env.extent = Elevation
arcpy.env.cellSize = Elevation

#Create a temp folder to hold intermediate files.
#Some of these folders will be deleted after the analysis has runs successfuly.
IntermediateFiles = outputWorkspace+"\\IntermediateFiles_"+Year
Final_Floor_Viewsheds = outputWorkspace+"\\Final_Viewsheds_"+Year
SummaryTables = outputWorkspace+"\\Summary_Tables_"+Year
ElevAvgTables=outputWorkspace+"\\ElevAvg_Tables_"+Year
ArcLengths = outputWorkspace+"\\ArcLengths_"+Year

if not os.path.exists(IntermediateFiles): os.makedirs(IntermediateFiles)
if not os.path.exists(Final_Floor_Viewsheds) : os.makedirs(Final_Floor_Viewsheds)
if not os.path.exists(SummaryTables) : os.makedirs(SummaryTables)
if not os.path.exists(ElevAvgTables): os.makedirs(ElevAvgTables)
if not os.path.exists(ArcLengths): os.makedirs(ArcLengths)

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName

def DegViewshed (FLOOR, HEIGHT):
    """Calculates a parcels viewshed, in degrees"""

    #Select Record
    arcpy.SelectLayerByAttribute_management(PointsFL,"NEW_SELECTION",SQL)
    
    #Set Observer Height (OffSETA)
    arcpy.CalculateField_management(PointsFL,"OFFSETA",HEIGHT,"PYTHON_9.3")
    
    #perform viewshed analysis
    arcpy.SetProgressorLabel("Performing Viewshed Analysis for point "+str(value))
    outViewshed = IntermediateFiles+"\\vs_"+str(FLOOR)+"_"+str(value).split(".")[0]
    arcpy.Viewshed_3d(outCon,PointsFL,outViewshed)

    #convert viewshed to polygon
    arcpy.SetProgressorLabel("Converting viewshed"+str(value)+" on floor "+str(FLOOR)+" to polygon.")
    OutPoly = IntermediateFiles+"\\"+os.path.basename(outViewshed).split(".")[0]+"_poly.shp"
    arcpy.RasterToPolygon_conversion(outViewshed,OutPoly)

    #Intersect viewshed polygon with buffer clip
    #This will allow the viewshed poly to inherit attribute fields needed for later analysis
    FinalView = Final_Floor_Viewsheds+"\\FinalViewshed_"+str(FLOOR)+"_"+str(value)+".shp"
    arcpy.Intersect_analysis([BufferClip,OutPoly],FinalView)
    
    #Select features in viewshed polygon with Gridcode = 1
    #If no records with grid = 1 exist, scriptwill skip to setting viewshed in degrees to 0
    
    #Convert viewshed polygon to layer
    ViewshedLayer = outName(FinalView,"lyr")
    arcpy.MakeFeatureLayer_management(FinalView,ViewshedLayer)

    #Select records with gridcode = 1
    arcpy.SelectLayerByAttribute_management(ViewshedLayer,"NEW_SELECTION","GRIDCODE ="+str(1)+"") 

    #Get count of the # of records selected in viewshed poly layer
    VsLyrCount = int(arcpy.GetCount_management(ViewshedLayer).getOutput(0))
    
    NoView = SummaryTables+"\\summary_"+str(FLOOR)+"_"+str(value)+".dbf"
    YesView = SummaryTables+"\\summary_"+str(FLOOR)+"_"+str(value)+".dbf"
    StatsField0 = [["GRIDCODE","SUM"]]
    CaseField0 = ["ID","SPOT",FloorField]               
    StatsField1 = [["LENGTH","SUM"]]
    CaseField1 = ["GRIDCODE","ID","SPOT",FloorField]
    VsArcLengths = ArcLengths+"\\ArcLength_"+str(FLOOR)+"_"+str(value)+".shp"
    
    if VsLyrCount == 0: #no viewable areas exist
        arcpy.SelectLayerByAttribute_management(ViewshedLayer,"CLEAR_SELECTION")
        arcpy.SetProgressorLabel("Calculating viewshed statistics for parcel "+str(value))
        arcpy.Statistics_analysis(ViewshedLayer,NoView, StatsField0,CaseField0)

        #Add field to summary table to hold viewshed value of 0
        #Add field to note which floor viewshed corresponds to
        arcpy.AddField_management(NoView, "FLR_RAN","SHORT")
        arcpy.AddField_management(NoView, "VIEW_"+Year,"DOUBLE")
        arcpy.AddField_management(NoView,"OFFSETA","SHORT")
        arcpy.CalculateField_management(NoView,"FLR_RAN",FLOOR)
        arcpy.CalculateField_management(NoView,"VIEW_"+Year,0)
        arcpy.CalculateField_management(NoView,"OFFSETA",HEIGHT)

    else: #Calculate viewshed, in degrees, for selected records
        arcpy.SetProgressorLabel("Getting arc length for parcel"+str(value)+" at the "+str(FLOOR)+" floor.")
        arcpy.Intersect_analysis([BufferLine,ViewshedLayer],VsArcLengths,"",10,"LINE")#Intersect with any line within 10 ft. 
        arcpy.AddField_management(VsArcLengths, "Length","DOUBLE")
        arcpy.CalculateField_management(VsArcLengths,"Length","!SHAPE.length@miles!","PYTHON_9.3")
        arcpy.Statistics_analysis(VsArcLengths,YesView,StatsField1,CaseField1)

        #Add fields to output summary table
        arcpy.AddField_management(YesView,"FLR_RAN","SHORT")
        arcpy.AddField_management(YesView,"VIEW_"+Year,"DOUBLE")
        arcpy.AddField_management(YesView,"OFFSETA","SHORT")
        arcpy.CalculateField_management(YesView,"FLR_RAN",FLOOR)
        arcpy.CalculateField_management(YesView,"OFFSETA",HEIGHT)
        arcpy.CalculateField_management(YesView,"VIEW_"+Year,"((!SUM_LENGTH!/3.14)*180)","PYTHON_9.3")
        arcpy.SelectLayerByAttribute_management(ViewshedLayer,"CLEAR_SELECTION")

#Open error log file
infile = open(outputWorkspace+"\\Error_Log_"+Year+".txt","w")

#Perform field check for viewshed parameters within the observation point attribute table.
#Script will add field to the attribute table if the field does not already exist.
#Needed fields are SPOT - used to define the surface elevations for the observation points.
#Azimuth -define the horizontal angle limits to the scan (start and end points in degrees).
#Radius - defines the search distance when identifying areas visible from each observation point.
#Cells that are beyond a certain distance can be excluded from the analysis.

VSFieldList = ["SPOT","OFFSETA","AZIMUTH1","AZIMUTH2","RADIUS1","RADIUS2"]
arcpy.SetProgressorLabel("Checking fields in observation point attribute table")

for FieldList in VSFieldList:
    ObsPtsFieldList=arcpy.ListFields(ObsPts,FieldList)
    fieldNames=[field.name for field in ObsPtsFieldList]

    if FieldList in fieldNames:
        print "Field", FieldList, "found in", ObsPts
    else:
        print"Field", FieldList, "NOT found in", ObsPts
        arcpy.AddField_management(ObsPts,FieldList, "DOUBLE")
        print FieldList, "created"

#Populate viewshed parameters with correct values for viewshed
Az1Cal = 0
Az2Cal = 180
Rad1Cal = 0
Rad2Cal = 5280

arcpy.CalculateField_management(ObsPts,"AZIMUTH1",Az1Cal)
arcpy.CalculateField_management(ObsPts,"AZIMUTH2",Az2Cal)
arcpy.CalculateField_management(ObsPts,"RADIUS1",Rad1Cal)
arcpy.CalculateField_management(ObsPts,"RADIUS2",Rad2Cal)
    
#Create Feature Layers
arcpy.SetProgressorLabel("Creating feature layers")
PointsFL = outName(ObsPts,"_Lyr")
footprintFL = outName(footprint,"_Lyr")
arcpy.MakeFeatureLayer_management(ObsPts, PointsFL)
arcpy.MakeFeatureLayer_management(footprint,footprintFL)

#Select observation points one by one
arcpy.SetProgressorLabel("Starting viewshed analysis...")
RangeCount = int(arcpy.GetCount_management(PointsFL).getOutput(0))

#Count number of parcels being processed
arcpy.AddMessage("Calculating viewshed for "+str(RangeCount)+" parcels")

sc = arcpy.SearchCursor(PointsFL)

for row in sc:

    try: 
        #Get Parcel ID value
        value = row.ID
        count = row.FID+1
        FlrCnt = row.getValue(FloorField)

        #Get bare earth elevation of parcel
        arcpy.SetProgressorLabel("Changing elevation footprint to bare earth elevation for point "+str(value))
        SQL = "Id =" +str(value)+""
        arcpy.SelectLayerByAttribute_management(PointsFL,"NEW_SELECTION",SQL)
        arcpy.SelectLayerByLocation_management(footprintFL,"INTERSECT",PointsFL)

        arcpy.env.workspace = IntermediateFiles #need to change workspace so that the .save files get saved correctly
        outExtractByMask = ExtractByMask(BareElevation,footprintFL)
        outExtractByMask.save(IntermediateFiles+"\\ebm_"+str(value))

        ElevAvg = ElevAvgTables+"\\avgelev_"+str(value)+".dbf"
        arcpy.Statistics_analysis(outExtractByMask,ElevAvg,[["VALUE","MEAN"]])
        
        arcpy.AddField_management(ElevAvg,"Pt_ID","SHORT")
        arcpy.CalculateField_management(ElevAvg,"Pt_ID",value)
        arcpy.AddJoin_management(PointsFL,"Id",ElevAvg,"Pt_ID","KEEP_COMMON")
        
        Field1 = os.path.basename(ObsPts).split(".")[0]+".SPOT"
        Field2 = "!"+os.path.basename(ElevAvg).split(".")[0]+".MEAN_VALUE!"
        arcpy.CalculateField_management(PointsFL,Field1,Field2,"PYTHON_9.3")
        arcpy.RemoveJoin_management(PointsFL)
        
        #Set parcel elevation to 0 this will be replaced by SPOT value caclualted above
        RastFootprint = IntermediateFiles+"\\fp_"+str(value).split(".")[0]
        arcpy.PolygonToRaster_conversion(footprintFL,"FID",RastFootprint,"MAXIMUM_AREA","",6)
        outIsNull = IsNull(RastFootprint) #Identify NoData Areas
        outIsNull.save(IntermediateFiles+"\\null1_"+str(value))
        outCon = Con(outIsNull,Elevation,0,"") #Use Con tool to change building footprint to elevation of 0 while leaving all other building footprints as is
        outCon.save(IntermediateFiles+"\\con1_"+str(value)) #Final raster to be used in viewshed analysis
        
        #buffer selected viewpoint
        arcpy.SetProgressorLabel("Buffering point "+str(value))
        outBuffer = IntermediateFiles+"\\buffer_"+str(value)+".shp"
        arcpy.Buffer_analysis(PointsFL,outBuffer,"1 mile")

        #Convert buffer polygon to line
        BufferLine = IntermediateFiles+"\\BufferLine_"+str(value)+".shp"
        arcpy.FeatureToLine_management(outBuffer,BufferLine)

        #Clip buffer to Ocean
        arcpy.SetProgressorLabel("Clipping point "+str(value)+" buffer to ocean")
        BufferClip = IntermediateFiles+"\\buffer_clipped_"+str(value).split(".")[0]+".shp"
        arcpy.Clip_analysis(outBuffer, Ocean, BufferClip)
       
        if FlrCnt ==1: #parcel floor count =1
            arcpy.AddMessage("\nParcel "+str(value)+" has 1 story to process. Calculating viewshed now...")
            print "\nParcel ",str(value)," has 1 story to process. Calculating viewshed now..."
            
            DegViewshed(1,10) #Calculate the viewshed with an observer height of 10 feet then move to point

            arcpy.AddMessage("First floor viewshed for parcel "+str(value)+" has been completed...")                  
            print "First floor viewshed for parcel ",str(value)," has been completed..."
            arcpy.AddMessage(str(count)+" of "+str(RangeCount)+"parcles has been completed.\n")
            print str(count)," of "+str(RangeCount)," parcels has been processed.\n"

        else: #if parcel has 1.5 floors or greater do this
            arcpy.AddMessage("\nParcel "+str(value)+" has 2 stories to process. Calculating viewsheds now...")
            print "\nParcel ",str(value)," has 2 stories to process. Calculating viewsheds now..."
            DegViewshed(1,10) #Calculate first floor view, then
            arcpy.AddMessage("First floor viewshed for parcel "+str(value)+" has been completed...")
            print "First floor viewshed for parcel ",str(value)," has been completed..."               
            
            DegViewshed(2,20) #Calculate second floor view
            arcpy.AddMessage("Second floor viewshed for parcel "+str(value)+" has been completed...")                  
            print "Second floor viewshed for parcel ",str(value)," has been completed..."
            arcpy.AddMessage("Viewsheds for "+str(count)+" of "+str(RangeCount)+" parcels have been processed.\n")
            print "Viewsheds for",str(count)," of ",str(RangeCount),"parcels have been processed.\n"

    except:

        arcpy.AddMessage("***An error occured processing parcel "+str(value)+". Refer to error log for details.")
        print "***An error occured processing parcel "+str(value)+". Refer to error log for details."
        infile.write("An error occured processing parcel "+str(value)+".\n")
        infile.write(arcpy.GetMessages()+"\n")
        arcpy.SelectLayerByAttribute_management(PointsFL, "CLEAR_SELECTION")
        arcpy.SelectLayerByLocation_management(footprintFL,"CLEAR_SELECTION")
        del row
        del sc
    del row
del sc           


#Merge all summary tables into a single table
arcpy.SetProgressorLabel("Creating final viewshed table")

arcpy.env.workspace = SummaryTables
FinalTable = outputWorkspace+"\\Final_Viewsheds_"+Year+".dbf"
Tables = arcpy.ListTables()
arcpy.Merge_management(Tables,FinalTable)

#Delete uneeded fields from final table
arcpy.DeleteField_management(FinalTable,["FREQUENCY","SUM_GRIDCO"])

print "Final viewshed table for",Year,"is located in",outputWorkspace,"\n"
arcpy.AddMessage("Final viewshed table for "+Year+" is located in "+outputWorkspace+"\n")

#save copy of table to CSV format

import win32com.client
try:
    
    excel = win32com.client.Dispatch('Excel.Application')

    inDBF = FinalTable
    outCSV = FinalTable.split(".")[0]+".csv"

    workbook = excel.Workbooks.Open(inDBF)
    # 24 represents xlCSVMSDOS
    workbook.SaveAs(outCSV,FileFormat=24)
    workbook.Close(SaveChanges=0)
    excel.Quit()

    arcpy.AddMessage(FinalTable+" converted to a csv file, and saved in "+outputWorkspace+"\n")
    print FinalTable,"converted to a scv file and saved in",outputWorkspace,"\n"

except:
    arcpy.AddMessage("\nERROR: Could not convert final viewshed table to csv file\n")
    arcpy.AddMessage(arcpy.GetMessages())
    infile.write("Could not convert final viewshed table to csv file\n")
    infile.write(arcpy.GetMessages()+"\n\n")
    
#Delete individual summary tables
    arcpy.SetProgressorLabel("Deleting Summary Tables... ")
try:
    
    shutil.rmtree(SummaryTables)
    print SummaryTables, "folder successfully deleted from", outputWorkspace,"\n"
    arcpy.AddMessage(os.path.basename(SummaryTables) + " folder successfully deleted from "+ outputWorkspace+"\n")
except:
    print "\nERROR: Could not delete intermediate files from",outputWorkspace,"\nYou will need to delete these manually\n"
    arcpy.AddMessage("\nERROR: Could not delete individual tables in "+outputWorkspace+"\nYou will need to delete these manually\n")
    infile.write("Could not delete individual tables in "+outputWorkspace+"\nYou will need to delete these manually\n\n")

#Delete Elevation Stats tables
    arcpy.SetProgressorLabel("Deleting elevation tables...")
try:
    shutil.rmtree(ElevAvgTables)
    print "Average Elevation tables successfully deleted from",outputWorkspace,"\n"
    arcpy.AddMessage("Average Elevation tables successfully deleted from "+outputWorkspace+"\n")
    
except:
    print "\nERROR: Could not delete",ElevAvgTables,"folder.\nYou will need to delete this manually\n"
    arcpy.AddMessage("\nERROR: Could not delete "+ElevAvgTables+" folder.\nYou will need to delete this manually\n")
    infile.write("Could not delete "+ElevAvgTables+" folder.\nYou will need to delete this manually\n\n")

#Delete intermediate files
    arcpy.SetProgressorLabel("Deleting all other intermediate files...")
try:
    shutil.rmtree(IntermediateFiles)
    print IntermediateFiles, "folder successfully deleted from", outputWorkspace,"\n"
    arcpy.AddMessage(IntermediateFiles+ " folder successfully deleted from "+outputWorkspace+"\n")

except:
    print "\nERROR: Could not delete intermediate files in",IntermediateFiles,"\nYou will need to delete these manually\n"
    arcpy.AddMessage("\nERROR: Could not delete intermediate files in "+IntermediateFiles+"\nYou will need to delete these manually\n")

infile.close()
  
print "Script Complete\n"
arcpy.AddMessage("Script Complete")

