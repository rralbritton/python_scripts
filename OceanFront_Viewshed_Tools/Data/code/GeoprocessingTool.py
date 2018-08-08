#Name:      WebGeoprocessingTool.py
#Purpose:   Selects a parcel by address and creates the ability to create a
#           choice list of addresses for the web application.
#Date:      November 5, 2013

import arcpy, os
from arcpy import env
from arcpy.sa import*

arcpy.env.workspace = "C:\\DatabaseConnections\\surf_city.sde" #Connection File location
arcpy.env.overwriteOutput = True 

#Check out the ArcGIS 3D Analyst extension license
arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("Spatial")

def outName(input,post="_Output"):
    """Returns output name."""
    outName=os.path.basename(input).split(".")[0]+post
    return outName

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

#Variables
ObsPts = arcpy.GetParameterAsText (0) 
Field = arcpy.GetParameterAsText(1)
Address = arcpy.GetParameterAsText (2)
outPoint = arcpy.GetParameterAsText(3)

#Create Feature Layers
PointsFL = outName(ObsPts,"_lyr")
arcpy.MakeFeatureLayer_management(ObsPts, PointsFL)

#Select parcel by hadd attribute
SQL= whereClause(PointsFL,Field,Address)   
arcpy.SelectLayerByAttribute_management(PointsFL,"NEW_SELECTION",SQL)

#Copy selected feature to temp  feature class
arcpy.CopyFeatures_management(PointsFL,outPoint)
arcpy.AddMessage(arcpy.GetMessages())
    
arcpy.AddMessage("Script complete")
