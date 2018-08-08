#Name:          Raster_NoData.py
#Purpose:       Replace "NoData" values in a raster with 0
#Assumptions:   Assumes that the input raster is in a non GRID format
#Inputs:        This script takes 2 inputs
                #0  = Input Raster
                #1  = Name and location of output raster

#Outputs:       The script will produce 1 output, an output raster.
#Author:        Rachel Albritton
#Last Update:   October 15, 2013
#------------------------------------------------------------------------------

import arcpy, os
from arcpy import env
from arcpy.sa import*

# Check out the ArcGIS 3D Analyst extension license
arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

#Variables
Elevation = arcpy.GetParameterAsText(0)
OutRaster = arcpy.GetParameterAsText(1)#File name saved

#Convert .tif to GRID
GridElev = os.path.dirname(OutRaster)+"\\grid_"+Elevation.split(".")[0][:7]
arcpy.CopyRaster_management(Elevation, GridElev)
arcpy.AddMessage("\n"+arcpy.GetMessages()+"\n")

#Convert floating point to integer
outInt = Int(GridElev)
outInt.save(os.path.dirname(OutRaster)+"\\int_rast")
arcpy.AddMessage(arcpy.GetMessages()+"\n")

#Identify Null Cells
outIsNull = IsNull(outInt) #Identify NoData Areas
outIsNull.save(os.path.dirname(OutRaster)+"\\rast_null")
outCon = Con(outIsNull,0,outInt) #Use Con tool to change building footprint to elevation of 0 while leaving all other building footprints as is
outCon.save(os.path.dirname(OutRaster)+"\\rast_con")

#It is assumed that negative elevation values correspond to the oceanfloor and not the surface of the ocean
#These values can be changed to 0 using the Con tool
outCon2 = Con(outCon,outCon,0, "VALUE > 1")
outCon2.save(OutRaster)

#Delete intermediate data
arcpy.Delete_management(GridElev)
arcpy.Delete_management (outInt)
arcpy.Delete_management(outIsNull)
arcpy.Delete_management(outCon)

arcpy.AddMessage("Raster NoData tool complete")
