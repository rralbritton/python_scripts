#Name:          updateOffsiteLocations.py
#Purpose:       Check the Orion Database for new offsite locations and add those
#               locations to the GIS network\offsite_locations feature dataset
#Last Update:   December 8, 2017

import arcpy, os, traceback, smtplib
from geopy.geocoders import ArcGIS
from email.MIMEText import MIMEText

def sendEmail(inputFile, Status):
    
    Sender = "GISAutomation@fm.utah.edu"
    Recp = "Rachel.Albritton@fm.utah.edu"
    SUBJECT = "New network Offsite Location " + Status
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
    
#Set Up Workspace
workspace = arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde"
arcpy.env.overwriteOuput = True
geocoder = ArcGIS()

#Input Data
gisOffsiteLocations = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\UUSD.DBO.network\UUSD.DBO.offsite_locations"
networkOffsiteLocations = r'\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\Orion_GISView.sde\GIS.dbo.Offsite_Locations'
inputFile = r'\\ad.utah.edu\sys\FM\gis\gis_scheduled_tasks\nw_offsite.txt'
gisOffsiteList = []
networkOffsiteList = []

try:
    #create list of offsite network buildings 
    sc = arcpy.SearchCursor(networkOffsiteLocations)
    for row in sc:
        networkOffsiteList.append(row.BuildingNumber)
    del row
    del sc

    #create list of offsite gis offsite buildings
    cursor = arcpy. SearchCursor(gisOffsiteLocations)
    for line in cursor:
        gisOffsiteList.append(line.building_number)
        
    del line
    del cursor

    #find buildings in offsite network list that are not in gis offsite list
    s = set(gisOffsiteList)
    difference = set([x for x in networkOffsiteList if x not in s])

    #Since the set will include build #49 which is on campus
    #We only want to add data id the set is greater then one
    if len(difference)> 1:
        inFile = open(inputFile, 'w')
        inFile.write('Set of Buildings to be added to the nework offsite locations:\n')
        
        #Start an edit session
        edit = arcpy.da.Editor(workspace)
        edit.startEditing()
        edit.startOperation()

        for i in difference:
            cur = arcpy.SearchCursor(networkOffsiteLocations)
            for r in cur:
                if r.BuildingNumber == i and r.BuildingNumber != 49 and r.Address != None:
                    inFile.write(str(r.BuildingNumber)+'\n')
                    location = r.Address+", "+ r.City
                    geolocate = geocoder.geocode(location)
                    sr = arcpy.SpatialReference(4326)
                    
                    with arcpy.da.InsertCursor(gisOffsiteLocations,['building_number','building_name','address','city','zip_code','lat_WGS','long_WGS','SHAPE@XY']) as rows:
                        rows.insertRow([r.BuildingNumber,r.BuildingName,r.Address,r.City, r.ZipCode,geolocate.latitude,geolocate.longitude,arcpy.PointGeometry(arcpy.Point(geolocate.longitude, geolocate.latitude),sr)])
                del r
            del cur
                
        edit.stopOperation()
        edit.stopEditing(True)
        
    inFile.close()
    sendEmail(inputFile,"SUCCESS")

    print '\ndone'
    
except:

 # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    # Print Python error messages for use in Python / Python Window
    print(pymsg)
    print(msgs)
    inFile.write(pymsg)
    inFile.write(msgs)
    inFile.close()
    sendEmail(inputFile,"FAILED")
   
