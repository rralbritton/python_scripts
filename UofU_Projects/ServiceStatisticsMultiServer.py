#Name:          ServiceStatistics.py
#Purpose:       retrieves usage statistics (total number of requests, maximum and average
#               response time, and total timed-out requests) from each production server
#               over a specified period of time (in minutes). The script generates a merged
#               CSV file from all servers then runs summary statistics in arcpy to get a 
#               single table of statistics for a service across all production servers.
#Resource:      http://server.arcgis.com/en/server/latest/administer/windows/example-export-service-statistics-to-a-file.htm
#Date:          August 25, 2016

# For HTTP calls
import httplib, urllib, urllib2, json
# For time-based functions
import time, uuid
from time import gmtime, strftime
# For system tools
import sys, os, shutil
from os import listdir
# For reading passwords without echoing
import getpass
# For writing csv files & merging
import csv, glob, pandas
from itertools import izip
from collections import defaultdict
#For creating merged statistics
import arcpy

workspace = arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\python_automation\reports\\"
arcpy.env.overwriteOutput = True

#Admin Credentials
username = "AD\FM-GIS-Job"
password = "j0b@cc0unt"
serverPort = 6080 # assumes server is enabled for HTTP access, HTTPS only sites will require (minor) script changes
   
serverList = [
                'fm-agstemplate.fm.utah.edu'
                ,'fm-ags0.fm.utah.edu'
                ,'fm-ags1.fm.utah.edu'
                , 'fm-ags2.fm.utah.edu'
                , 'fm-ags3.fm.utah.edu'
                , 'fm-ags4.fm.utah.edu'
                , 'fm-ags5.fm.utah.edu'
             ]

def find_csv_filenames( path_to_dir, suffix=".csv" ):
    filenames = listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]

# Defines the entry point into the script
def main(argv=None):
    
    serviceName = "services/mapservices/routes.MapServer"
    interval= 1440 #In minutes. [1440 = 24 hours, 10080 = 1 week, 43200 = 30 days, 525600 = 1 year (365 days)]
    tableViews = []

    #Create a Temp Directory for CSV files to be stored
    csvDirectory = workspace+"CSVReports/"
    if not os.path.exists(csvDirectory): os.makedirs(csvDirectory)
     
    for serverName in serverList:

        # Get a token
        token = getToken(username, password, serverName, serverPort)
        if token == "":
            print("Could not generate a token with the username and password provided.")
            return
       
        # Ask for FromTime
        fromTime = 0
        while fromTime == 0:
            fromTime = '2016-08-01 00:00' #YYYY-MM-DD HH:MM format (e.g. 2014-05-10 14:00)
            try: fromTime = int(time.mktime(time.strptime(fromTime, '%Y-%m-%d %H:%M'))*1000) 
            except:
                print('Unable to parse input. Ensure date and time is in YYYY-MM-DD HH:MM format.')
                fromTime = 0
        
        # Ask for ToTime
        toTime = 0
        while toTime == 0:
            toTime = '2016-08-24 23:59'
            # Convert input to Python struct_time and then to Unix timestamp in ms
            try: toTime = int(time.mktime(time.strptime(toTime, '%Y-%m-%d %H:%M'))*1000)
            except: 
                print('Unable to parse input. Ensure date and time is in YYYY-MM-DD HH:MM format.')
                toTime = 0
                               
        # Construct URL to query the logs
        statsCreateReportURL = "http://{0}:{1}/arcgis/admin/usagereports/add".format(serverName, serverPort)

        # Create unique name for temp report
        reportName = uuid.uuid4().hex 

        # Create report JSON definition
        statsDefinition = {'reportname' : reportName, 'since' : 'CUSTOM', 
               'queries' : [{'resourceURIs' : [serviceName],
               'metrics' : ['RequestCount', 'RequestsFailed', 'RequestsTimedOut', 
               'RequestMaxResponseTime', 'RequestAvgResponseTime'] }],
               'from' : fromTime, 'to': toTime, 'aggregationInterval' : interval,
               'metadata' : {'temp' : True, 'tempTimer' : int(time.time() * 1000)}}

        postdata = { 'usagereport' : json.dumps(statsDefinition) }
        createReportResult = postAndLoadJSON(statsCreateReportURL, token, postdata)
        
        # Query newly created report
        statsQueryReportURL = "http://{0}:{1}/arcgis/admin/usagereports/{2}/data".format(serverName, serverPort, reportName)
        postdata = { 'filter' : { 'machines' : '*'} }
        reportData = postAndLoadJSON(statsQueryReportURL, token, postdata)
        #print(reportData)
        
        # Get list of timeslices covered by this report
        timeslices = reportData['report']['time-slices']
        #print(timeslices)
        
        header = ["Date"]
        for timeslice in timeslices:
            t = time.localtime(timeslice/1000.0)
            header.append(time.strftime('%Y-%m-%d', t))
        
        # Open output file
        fileName = csvDirectory+serviceName.split(".")[0].split("/")[2]+"_"+serverName+".csv"
        csvTranspose = fileName.split(".csv")[0]+"_trans.csv"
        output = open(fileName, 'wb')
        csvwriter = csv.writer(output, dialect='excel')
        csvwriter.writerow(header)
        
        # Dig into the report for the data for individual services
        for serviceMetric in reportData['report']['report-data'][0]:
            name = serviceMetric['metric-type']
            data = serviceMetric['data']
            csvwriter.writerow([name] + data)
        
        output.close()
        
        #Transpose files csv reports
        a = izip(*csv.reader(open(fileName, "rb")))
        csv.writer(open(csvTranspose, "wb")).writerows(a)     
        print csvTranspose+" created."

        # Cleanup (delete) statistics report
        statsDeleteReportURL = "http://{0}:{1}/arcgis/admin/usagereports/{2}/delete".format(serverName, serverPort, reportName)
        deleteReportResult = postAndLoadJSON(statsDeleteReportURL, token)
        os.remove(fileName)

    #Merge seperate CSV files into a single file
    #Resource: https://www.youtube.com/watch?v=KoRT-v0SzMs

    #Get list of CSV files    
    fileList = glob.glob(csvDirectory+"/*.csv")

    #Stack dataframes (i.e spreadsheets) into a single file
    dfList =[]
    for filename in fileList:
        df=pandas.read_csv(filename, header=0)
        dfList.append(df)
    concatDF = pandas.concat(dfList, axis=0)

    #Export concatinated dataframes to new CSV file
    concatDF.to_csv(workspace+serviceName.split(".")[0].split("/")[2]+"_MergedCSVReport_"+str(strftime("%Y%m%d", gmtime()))+".csv",index=None)
    print "CSV files Merged"
    
    #Import CSV merged tables into arcgis and run summary statistics
    #Create dbf from csv so that the table has OID numbers
    tempInput = workspace+serviceName.split(".")[0].split("/")[2]+"_MergedCSVReport_"+str(strftime("%Y%m%d", gmtime()))+".csv"
    tempTable = arcpy.TableToTable_conversion(tempInput,csvDirectory,"tempTable.dbf")   
    summaryStats = tempInput.split("_MergedCSVReport_"+str(strftime("%Y%m%d", gmtime()))+".csv")[0]+"_summaryStats_"+str(strftime("%Y%m%d", gmtime())+".dbf")
    arcpy.Statistics_analysis(tempTable, summaryStats,[["RequestCou","SUM"],["RequestsFa","SUM"],["RequestsTi","SUM"],["RequestMax","MAX"],["RequestAvg","MEAN"]],["DATE"])

    #Create Meaningful Field Names for resulting output table
    arcpy.AddField_management(summaryStats, "TotalCnt","DOUBLE","","","","Total Count")
    arcpy.AddField_management(summaryStats,"FailedReq","DOUBLE","","","","Failed Requests")
    arcpy.AddField_management(summaryStats,"TimedOut","DOUBLE","","","","Timed Out Requests")
    arcpy.AddField_management(summaryStats,"MaxTime","DOUBLE","","","","Max Response Time")
    arcpy.AddField_management(summaryStats,"AvgTime","DOUBLE","","","","Avg Response Time")
    arcpy.CalculateField_management(summaryStats,"TotalCnt","!SUM_Reques!","PYTHON")
    arcpy.CalculateField_management(summaryStats,"FailedReq","!SUM_Requ_1!","PYTHON")
    arcpy.CalculateField_management(summaryStats,"TimedOut","!SUM_Requ_2!","PYTHON")
    arcpy.CalculateField_management(summaryStats,"MaxTime","!MAX_Reques!","PYTHON")
    arcpy.CalculateField_management(summaryStats,"AvgTime","!MEAN_Reque!","PYTHON")
    arcpy.DeleteField_management(summaryStats,"FREQUENCY")
    arcpy.DeleteField_management(summaryStats,"SUM_Reques")
    arcpy.DeleteField_management(summaryStats,"SUM_Requ_1")
    arcpy.DeleteField_management(summaryStats,"SUM_Requ_2")
    arcpy.DeleteField_management(summaryStats,"MAX_Reques")
    arcpy.DeleteField_management(summaryStats,"MEAN_Reque")
    print "statistics table complete"
          
    #Delete Temp Directory
    shutil.rmtree(csvDirectory)
    
    return

# A function that makes an HTTP POST request and returns the result JSON object
def postAndLoadJSON(url, token = None, postdata = None):
    if not postdata: postdata = {}
    # Add token to POST data if not already present and supplied
    if token and 'token' not in postdata: postdata['token'] = token 
    # Add JSON format specifier to POST data if not already present
    if 'f' not in postdata: postdata['f'] = 'json' 
    
    # Encode data and POST to server
    postdata = urllib.urlencode(postdata)
    response = urllib2.urlopen(url, data = postdata)
    
    if (response.getcode() != 200):
        response.close()
        raise Exception('Error performing request to {0}'.format(url))

    data = response.read()
    response.close()

    # Check that data returned is not an error object
    if not assertJsonSuccess(data):          
        raise Exception("Error returned by operation. " + data)

    # Deserialize response into Python object
    return json.loads(data)

#A function to generate a token given username, password and the adminURL.
def getToken(username, password, serverName, serverPort):
    # Token URL is typically http://server[:port]/arcgis/admin/generateToken
    tokenURL = "/arcgis/admin/generateToken"
    
    # URL-encode the token parameters
    params = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})
    
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    
    # Connect to URL and post parameters
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", tokenURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print("Error while fetching tokens from the admin URL. Please check the URL and try again.")
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):            
            return
        
        # Extract the token from it
        token = json.loads(data)       
        return token['token']            

#A function that checks that the input JSON object
#  is not an error object.    
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print("Error: JSON object returns an error. " + str(obj))
        return False
    else:
        return True
        
# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
