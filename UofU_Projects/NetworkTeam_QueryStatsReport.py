#Name:          QueryStatistics.py
#Purpose:       retrieves usage statistics (average response time and number of failed requests)
#               from each production server for Network Team Services. 
#               The script generates a merged CSV file from all servers then
#               runs summary statistics in arcpy to get a 
#               single table of statistics for a service across all production servers.
#ASsumptions:   The report already exists 
#Date:          May 4, 2018

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
#For emailing reults
import smtplib, email
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.mime.application import MIMEApplication

workspace = arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_directories\scheduled_scripts\\"
arcpy.env.overwriteOutput = True

#Admin Credentials
username = "AD\FM-GIS-Job"
password = "j0b@cc0unt"
serverPort = 6443 
   
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
    
    serviceName = "services/mapservices/Network_Team.MapServer"
    interval= 10080 #In minutes. [1440 = 24 hours, 10080 = 1 week, 43200 = 30 days, 525600 = 1 year (365 days)]
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
       
        #Report Being Queried
        reportName = 'network_team_avg_resp_times'
     
        # Query report
        statsQueryReportURL = "https://{0}:{1}/arcgis/admin/usagereports/{2}/data".format(serverName, serverPort, reportName)
        print statsQueryReportURL +'\n'
        postdata = { 'filter' : { 'machines' : '*'} }
        reportData = postAndLoadJSON(statsQueryReportURL, token, postdata)
        
        # Get list of timeslices covered by this report
        timeslices = reportData['report']['time-slices']
        
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

        #remove orginal exports
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
    concatDF.to_csv(csvDirectory+serviceName.split(".")[0].split("/")[2]+"_MergedCSVReport_"+str(strftime("%Y%m%d", gmtime()))+".csv",index=None)
    print "CSV files Merged"
    print "Running Statistics..."
    
    #Import CSV merged tables into arcgis and run summary statistics
    #Create dbf from csv so that the table has OID numbers
    tempInput = csvDirectory+serviceName.split(".")[0].split("/")[2]+"_MergedCSVReport_"+str(strftime("%Y%m%d", gmtime()))+".csv"
    tempTable = arcpy.TableToTable_conversion(tempInput,csvDirectory,"tempTable.dbf")   
    summaryStats = workspace+serviceName.split(".")[0].split("/")[2]+"_summaryStats_"+str((strftime("%Y%m%d", gmtime())+".dbf"))
    arcpy.Statistics_analysis(tempTable, summaryStats,[["RequestsFa","SUM"],["RequestAvg","MEAN"]],["DATE"])

    #Create Meaningful Field Names for resulting output table
    arcpy.AddField_management(summaryStats,"FailedReq","DOUBLE","","","","Failed Requests")
    arcpy.AddField_management(summaryStats,"AvgTime","DOUBLE","","","","Avg Response Time")
    arcpy.CalculateField_management(summaryStats,"FailedReq","!SUM_Reques!","PYTHON")
    arcpy.CalculateField_management(summaryStats,"AvgTime","!MEAN_Reque!","PYTHON")
    arcpy.DeleteField_management(summaryStats,"SUM_Reques")
    arcpy.DeleteField_management(summaryStats,"MEAN_Reque")
    print "statistics table complete"

    #Export Final to CSV format
    export = summaryStats.split(".dbf")[0]+".csv"
    fields = arcpy.ListFields(summaryStats)
    field_names = [field.name for field in fields]
    with open(export,'wb') as e:
        w = csv.writer(e)
        w.writerow(field_names)

        for row in arcpy.SearchCursor(summaryStats):
            field_vals = [row.getValue(field.name) for field in fields]
            w.writerow(field_vals)
        del row
    
    #Delete Temp Directory
    shutil.rmtree(csvDirectory)

    #Email Results
    #Recipient's Email
    Recp = ['Rachel.Albritton@fm.utah.edu'] 
    Sender = "Network_Team_Updates@fm.utah.edu"
    msg = MIMEMultipart()
    msg['Subject'] = "Network Team Response Times"
    msg['From'] = Sender
    msg['To'] = ",".join(Recp)

    #Attach CSV file
    filename = export
    fp=open(filename,'rb')
    att = email.mime.application.MIMEApplication(fp.read(),_subtype="csv")
    fp.close()
    att.add_header('Content-Disposition','attachment',filename=os.path.basename(filename))
    msg.attach(att)

    # Send the message via the SMTP server
    Host = "smtp.utah.edu"
    s = smtplib.SMTP(Host)
    s.sendmail(Sender, Recp, msg.as_string())
    s.quit()
    
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
        print response.getcode()
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
    httpConn = httplib.HTTPSConnection(serverName, serverPort)
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
