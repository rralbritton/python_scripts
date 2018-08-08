#Selects a set of potential conservation areas based on there location (county) and exports these
#potential conservation areas and associated files to an output folder.
#Rachel Albritton (rralbrit)

import arcpy, os

#Set workspace to where tool data is saved
arcpy.env.workspace = "C:/GIS540_Project/ToolData" #Change to Set Parameter
print "Workspace set to:", arcpy.env.workspace,'\n'
arcpy.AddMessage("Workspace set to: "+arcpy.env.workspace)

#Set output workspace
outputWorkspace = "C:/GIS540_Project/OutputData"
print "Output data will be saved to:", outputWorkspace,'\n'
arcpy.AddMessage("Output data will be saved to:"+outputWorkspace+'\n')

arcpy.env.overwriteOutput=True

#Checkout Spatial Analyst License
arcpy.CheckOutExtension("Spatial")

def whereClause(table, field, values):
    """Takes a semicolon-delimited list of values and constructs a SQL WHERE
    clause to select those values within a given field and table."""

    # Add field delimiters
    fieldDelimited = arcpy.AddFieldDelimiters(arcpy.Describe(table).path, field)

    # Split multivalue at semicolons and strip quotes
    valueList = [value[1:-1]
                 if (value.startswith("'") and value.endswith("'"))
                 else value for value in values.split(';')]

    # Determine field type
    fieldType = arcpy.ListFields(table, field)[0].type

    # Add single-quotes for string field values
    if str(fieldType) == 'String':
        valueList = ["'%s'" % value for value in valueList]

    # Format WHERE clause in the form of an IN statement
    whereClause = "%s IN (%s)"%(fieldDelimited, ', '.join(valueList))
    return whereClause

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName
    


#Make Feature Layer from County Boundary Feature Class
InputFC = "C:\GIS540_Project\ToolData\hardcoded\SBR_NC_Counties.shp"
OutputFL = outName(InputFC,"_Layer")

try:
    arcpy.MakeFeatureLayer_management(InputFC, OutputFL)
except:
    arcpy.GetMessages()
    
#Select Attributes from County Boundary Layer
Field = "CO_NAME"
Counties = arcpy.GetParameterAsText(0) #change value 
SQL = whereClause(OutputFL, Field, Counties)

try:
    arcpy.SelectLayerByAttribute_management(OutputFL,"NEW_SELECTION", SQL)
    count = int(arcpy.GetCount_management(OutputFL).getOutput(0))
    print '\n',"There are", count, "counties selected from County Boundary layer.",'\n'
    
except:
    print arcpy.GetMessages()

#Copy Selected Feature Layer to new Feature Class
OutputFC = outputWorkspace+"/"+outName(InputFC,"_selected.shp")

try:
    
    arcpy.CopyFeatures_management(OutputFL, OutputFC)

    print "The following counties were exported to a new feature class:" #Add full path folder location once I figure out how to save to there
    sc = arcpy.SearchCursor(OutputFC)
    for line in sc:
        print line.CO_NAME
    del line
    del sc
    
except:
    print arcpy.GetMessages()

#Select potential conservation areas that intersect with selected counties

#Make potential conservation areas a feature layer
pcaFC = "C:/GIS540_Project/ToolData/hardcoded/SBR_NC_pca.shp" #change to user input
pcaFL = outName(pcaFC,"_Selected")

try:
    arcpy.MakeFeatureLayer_management(pcaFC, pcaFL)
    
except:
    arcpy.GetMessages()

#Select potential conservation areas that intersect with selected counties

try:
    arcpy.SelectLayerByLocation_management(pcaFL,"INTERSECT",OutputFL)
    pcacount = int(arcpy.GetCount_management(pcaFL).getOutput(0))
    print '\n',"There are", pcacount, "potential conservation areas that intersect with the selected counties shapefile.",'\n'

except:
    arcpy.GetMessages()

#Copy selected potential conservation areas to new feature class
pca_selected = outputWorkspace+"/"+outName(pcaFC,"_Selected.shp")

try:
    arcpy.CopyFeatures_management(pcaFL, pca_selected)
    pcaselect_count = int(arcpy.GetCount_management(pca_selected).getOutput(0))
    print "These", pcaselect_count,"potential conservation areas were successfully exported to:",outputWorkspace,"\n" 
except:
    arcpy.GetMessages()
    
#Batch clip associated files to selected pca shapefile
fcs = arcpy.ListFeatureClasses()
clipper = pca_selected

try:
    for fc in fcs:
        clipped = outputWorkspace+"/"+fc[:-4]+"_clip.shp" #fix output
        arcpy.Clip_analysis(fc,clipper,clipped)    
except:
    print arcpy.GetMessages(),'\n'

#Some clipped files may be empty and do not need to be ke[t fpr further process
#Use Get count tool to find empty shapefiles and delete them

try:
    clipped_files=outputWorkspace
    for files in clipped_files:
        arcpy.GetCount_management(files)
        if getOutput(0)==0:
            print files, "contained 0 records and was removed from outputWorkspace"
            arcpy.Delete_management(files)

except:
    arcpy.GetMessages()
print "The following files were successfully clipped to the selected potential conservation areas and are saved in", outputWorkspace,":",'\n'
   
files = os.listdir(outputWorkspace) #Can not use ListFeatureClasses since we need to list files in a directory other then the workspace
for file in files:
    if file.endswith(".shp"):
        print file
        
#would like to add script that gets count of all the records in all files in output directory.
#IF record count = 0, THEN delete file
#Problem: Can not use ListFeatureClasses since data is not in the workspace AND
#using os.listdir does not work either