#UTA_retrieveNewData.py

import urllib2, datetime, smtplib, sys, os, traceback
from ftplib import FTP
from email.MIMEText import MIMEText

def sendEmail():
    
    Sender = "UTA.Data.Updates@fm.utah.edu"
    Recp = "Rachel.Albritton@fm.utah.edu"
    SUBJECT = "UTA Data Updates"
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


#Variables
inputFile = r"\\ad.utah.edu\sys\FM\gis\uit_scheduled_tasks\uta_new_data_email.txt"

try:
    
    #Open textfile
    infile = open(inputFile,'w')
    
    ftp = FTP('ftp.agrc.utah.gov')   # connect to host, default port
    ftp.login()

    ftp.cwd('UtahSGID_Vector/UTM12_NAD83/TRANSPORTATION/PackagedData/_Statewide/UtahTransitSystems')
    #ftp.retrlines('NLST')
    date = ftp.sendcmd('MDTM UtahTransitSystems_gdb.zip')
    newDate = date[4:12]
    print newDate
    today = (datetime.date.today()).strftime('%Y%m%d')

    if newDate >= today:
        print 'true'
        infile.write("New UTA Data is available for download.")
        infile.write("\n\nhttps://gis.utah.gov/data/sgid-transportation/transit/")
        infile.close()
        ftp.close()
        sendEmail()  
    else:  
        ftp.close()
        infile.close()
        os.remove(inputFile)
    
    print "done"
    
except:
    
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])


    # Print Python error messages for use in Python / Python Window
    print(pymsg)
    infile.write("\nAn ERROR Occured:\n" + pymsg)
    ftp.close()
    infile.close()
    sendEmail()
