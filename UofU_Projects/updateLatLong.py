#Name:          updateLatLong.py
#Purpose:       Calculates latitude and longitude WGS values for structures feature class.
#               the record must have a building number that is not 0, -1 or NULL
#Last Updated:  November 2,2017
#Author:        Rachel Albritton

import arcpy, os, traceback, smtplib
from email.MIMEText import MIMEText

def sendEmail(inputFile):
    
    Sender = "GISAutomation@fm.utah.edu"
    Recp = "Rachel.Albritton@fm.utah.edu"
    SUBJECT = "Structures Lat/Long Updates ERRORS"
    body = open(inputFile, 'r')
    msg = MIMEText(body.read())
    body.close()
    
    msg['Subject'] = SUBJECT 
    msg['From'] = Sender
    msg['To'] = Recp

    
    # Send the message via the SMTP server
    Host = "smtp.utah.edu"
    s = smtplib.SMTP(Host)
    s.sendmail(Sender, Recp, msg.as_string())
    s.quit()
    os.remove(inputFile)

#Setup Workspace
workspace = arcpy.env.workspace =  r'\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde' 
temp = 'C:/temp'
if not os.path.exists(temp): os.makedirs(temp)
arcpy.env.overwriteOuput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(4326)
arcpy.env.geographicTransformations = 'WGS_1984_(ITTRF00)_To_NAD_1983'

#Input Data
structures = '\\uusd.dbo.structure' 

try: 
    #Search for NULL lat/long values
    structure_lyr = arcpy.MakeFeatureLayer_management(structures,'structure_lyr')
    arcpy.SelectLayerByAttribute_management(structure_lyr,'NEW_SELECTION','building_number NOT IN (0,-1) AND building_number IS NOT NULL')
    arcpy.SelectLayerByAttribute_management(structure_lyr,'SUBSET_SELECTION','lattitude IS NULL OR longitude IS NULL')
    count = int(arcpy.GetCount_management(structure_lyr).getOutput(0))
    print count

    if count > 0:
        #Create a temp centroid point file
        centroids = temp+'\\centroids.shp'
        arcpy.FeatureToPoint_management(structure_lyr,centroids)
        arcpy.CalculateField_management(centroids,'longitude','!SHAPE.centroid.x!','PYTHON_9.3')
        arcpy.CalculateField_management(centroids,'lattitude','!SHAPE.centroid.y!','PYTHON_9.3')
        centroid_lyr = arcpy.MakeFeatureLayer_management(centroids, "centroid_lyr")

        join = arcpy.AddJoin_management(structure_lyr,'building_number',centroid_lyr,'building_n','KEEP_COMMON')
        arcpy.CalculateField_management(structure_lyr, 'uusd.dbo.structure.lattitude','!centroids.lattitude!','PYTHON')
        arcpy.CalculateField_management(structure_lyr, 'uusd.dbo.structure.longitude','!centroids.longitude!','PYTHON')
        arcpy.RemoveJoin_management(structure_lyr)
        
        arcpy.Delete_management(centroids)
    
    print 'done'            

except:
    #write email
    inputFile = 'C:/temp/inputFile.txt'
    infile = open(inputFile, 'w')
    
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    # Print Python error messages for use in Python / Python Window
    print(pymsg)
    print(msgs)
    infile.write(pymsg+'\n\n'+msgs)
    infile.close()
    sendEmail(inputFile)             

    if os.path.exists('C:/temp/centroids.shp'):
        arcpy.Delete_management('C:/temp/centroids.shp')
