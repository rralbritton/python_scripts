#Name:          ServiceLogReports.py

# For Http calls
import httplib, urllib, urllib2, json

# For system tools
import sys, os

# For reading passwords without echoing
import getpass

# For time-based functions
import time, datetime
from time import strftime
from datetime import timedelta

#Email report
import smtplib
from email.MIMEText import MIMEText

###Admin Credentials
##username = 
##password =

serverPort = 6080 # assumes server is enabled for HTTP access, HTTPS only sites will require (minor) script changes
   
serverList = [
                'fm-ags0.fm.utah.edu'
                , 'fm-ags1.fm.utah.edu'
                , 'fm-ags2.fm.utah.edu'
                , 'fm-ags3.fm.utah.edu'
                , 'fm-ags4.fm.utah.edu'
                , 'fm-ags5.fm.utah.edu'
             ]

inputFile = r"\\ad.utah.edu\sys\fm\gis\python_automation\ServerLogReports.txt"
infile = open(inputFile,'w')

def email():
     #Email Report
     Sender = "GISAutomationScript@fm.utah.edu"
     Recp = 'Rachel.Albritton@fm.utah.edu'
     body = open(inputFile, 'r')
     msg = MIMEText(body.read())
     body.close()

     msg['Subject'] = "Service Log Reports"
     msg['From'] = Sender
     msg['To'] = Recp

     # Send the message via our own SMTP server, but don't include the
     # envelope header.
     Host = "smtp.utah.edu"
     s = smtplib.SMTP(Host)
     s.sendmail(Sender, Recp, msg.as_string())
     s.quit()
     os.remove(inputFile)
     
#Defines the entry point into the script
def main(argv=None):
    
   
    # Ask for map service name
  
    serviceList = [

        'telecom/Outside_Infrastructure_Fill_Rates.MapServer'
        ,'telecom/Outside_Infrastructure_Open_Conduits.MapServer'
        ,'telecom/UIT_Basemap.MapServer'
        ,'telecom/UIT_Enclosures.MapServer'
        ,'telecom/UIT_InterductBanks.MapServer'
        ,'telecom/UIT_TubeBanks.MapServer'
        ,'telecom/UIT_TubeRoutes.MapServer'
        ,'telecom/UITBuildingLabels.MapServer'
        ,'mapservices/wireless_survey.MapServer'

        ]

    for mapService in serviceList:

         infile.write("-----------------------\n"+mapService.upper()+"\n-----------------------\n")
         print "-----------------------\n"+mapService.upper()+"\n-----------------------\n"
         
         for serverName in serverList:
              
      
            # Get a token
            token = getToken(username, password, serverName, serverPort)
            if token == "":
                print "Could not generate a token with the username and password provided."
                return
            
            # Construct URL to query the logs
            logQueryURL = "/arcgis/admin/logs/query"
            logFilter = "{'services': ['" + mapService + "']}"
           
            # Supply the log level, filter, token, and return format
            now = datetime.datetime.now()
            params = urllib.urlencode({
                'startTime': now.strftime('%Y-%m-%dT%H:%M:%S,%f'),  
                'endTime': (now-datetime.timedelta(hours = 24)).strftime('%Y-%m-%dT%H:%M:%S,%f'), 
                'level': 'WARNING',
                'token': token,
                'pageSize': 100,
                'f': 'JSON',
                'filter': { "codes":[],
                            "processIds":[],
                            "services": [mapService],
                            }
               })

            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            
            # Connect to URL and post parameters
            httpConn = httplib.HTTPConnection(serverName, serverPort)
            request = httpConn.request("POST",logQueryURL, params, headers)      
            
            # Read response
            response = httpConn.getresponse()
            if (response.status != 200):
                httpConn.close()
                print "Error while querying logs."
                return
            else:
                data = response.read()
                parsed = json.loads(data)

            # Check that data returned is not an error object
            if not assertJsonSuccess(data):          
                print "Error returned by operation. " + data
            else:
                
                infile.write(serverName.upper()+"\n")
                infile.write (json.dumps(parsed, indent=4, sort_keys=True))
                
                print serverName.upper()
                print json.dumps(parsed, indent=4, sort_keys=True)
            
            httpConn.close()
            
    infile.close()
    email()
    return

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
        print "Error while fetching tokens from admin URL. Please check the URL and try again."
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
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True

# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
