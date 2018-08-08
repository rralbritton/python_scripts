#Email_Multi_Attachments.py

import smtplib,os
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

Files = os.listdir(r"\\ad.utah.edu\sys\FM\gis\ags_directories\DDC_Web\Photos")
Folder = r"\\ad.utah.edu/sys/FM/gis/ags_directories/DDC_Web/Photos/"

#Sender Email
Sender = "Rachel.Albritton@fm.utah.edu"

#Recipient's Email
Recp = "Rachel.Albritton@fm.utah.edu"

SUBJECT = "Pic Test"

msg = MIMEMultipart()
msg['Subject'] = SUBJECT 
msg['From'] = Sender
msg['To'] = Recp

#Get Photo(s)
for file in Files:
    FullPath = Folder+file
    if file.endswith(".jpg"):
        fp = open(FullPath,'rb')
        img = MIMEImage(fp.read())
        fp.close()
        msg.attach(img)

# Send the message via the SMTP server
Host = "smtp.utah.edu"
s = smtplib.SMTP(Host)
s.sendmail(Sender, [Recp], msg.as_string())
s.quit()

print "done"
