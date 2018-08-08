#Name:          decode_polyline.py
#Purpose:       decode encoded polylines from ride system JSON service endpoint
#               And create feature classes of that data
#Reference:     The decode_polyline definition was slightly modified from
#               https://stackoverflow.com/questions/15380712/how-to-decode-polylines-from-google-maps-direction-api-in-php
#Author:        Rachel Albritton
#Last Updated:  8/24/2017
######################################################################################

import urllib2, json, os
import re
import arcpy

def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        #print str(lat / 100000.0) +"\t"+ str(lng / 100000.0)
        infile.write(str(lat / 100000.0) +"\t"+ str(lng / 100000.0)+"\n")

#Setup Workspace
workspace = r"S:\Rachel\Data\Scratch"
arcpy.env.overwriteOutput = True

#Create dictionary {LineName:EncodedPolyline}
shuttleDict = {}

#Request data
response = urllib2.urlopen('https://uofu.ridesystems.net/services/jsonprelay.svc/GetRoutesForMapWithScheduleWithEncodedLine?apikey=ride1791')
data = json.load(response)

#Populate dictionary with data
for element in data:
    
    firstString = re.sub(r'\s+', '',element['Description'])
    secondString = re.sub('[-.]', '',firstString)
    shuttleDict[secondString] = element['EncodedPolyline']
    
#Create Polylines from dictionary data
for k,v in shuttleDict.items():

    if v != "":
        
        #Setup ASCII File
        inputfile = workspace + "\\" + k +".txt"
        infile = open(inputfile,'w')
        infile.write('Latitude\tLongitude\n')
 
        #DecodeLine  
        decode_polyline(v)
        infile.close()

        #Make XY Event Layer
        points = arcpy.MakeXYEventLayer_management(inputfile,'Longitude','Latitude')
        
        #Convert Points to Lines
        line = arcpy.PointsToLine_management(points, inputfile.split(".")[0]+".shp")
        
        #Project to UTM Coordinates
        lines_final = "S:\Rachel\Data\ShuttleTracker_Data.gdb\Routes\\" + k
        outCS = arcpy.SpatialReference(26912)
        arcpy.Project_management(line, lines_final,outCS)
        
        #Delete Scratch Data
        print k + " line done"
        arcpy.Delete_management(points)
        arcpy.Delete_management(line)
        os.remove(inputfile)

print '\nScript Complete'  

