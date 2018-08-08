#Title:         busstops_checkurl.py
#Purpose:       The UTA website has an automatic redirect page that will read as valid,
#               therefore giving a incorrect response code when checking if the URLs are still valid.
#               The site redirect page title reads "404". So this script reads the title of the page
#               and reports back any titles containing '404'.
#Last Updated:  August 10, 2016   

import urllib2, bs4
from bs4 import BeautifulSoup

url_list = [
    'http://www.rideuta.com/mc/?page=Bus-BusHome-Route2',
    'http://www.rideuta.com/mc/?page=Bus-BusHome-Route2X',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/3-3rd-Avenue',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/6-6th-Avenue',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/9-9th-South',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/11-11th-Avenue',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/17-1700-South',
    'http://www.rideuta.com/mc/?page=Bus-BusHome-Route21',
    'http://www.rideuta.com/mc/?page=Bus-BusHome-Route213',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/220-Highland-Drive-1300-East',
    'http://www.rideuta.com/mc/?page=Bus-BusHome-Route223',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/228-Foothill-Blvd-2700-East',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/313-South-Valley-U-of-U-Fast-Bus',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/354-Sandy-U-of-U-Fast-Bus',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/455-UofU-Davis-County-Weber-State-University',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/473-SLC-Ogden-Hwy-Express',
    'http://www.rideuta.com/Rider-Tools/Schedules-and-Maps/902-PC-SLC-Connect'
    ]

for url in url_list:
    
    try:
        u = urllib2.urlopen(url)
        html = u.read()

        soup = BeautifulSoup(html, "html.parser")
        title = soup.html.head.title
        if "404" in title.contents:
            print "404: "+ url
    
##        if u.getcode() < 300:
##            print url+" is OK\n"
##            u.close()
##        elif u.getcode() >=300: #and u.getcode() <400:
##            print str(u.getcode())+": "+url+" is being REDIRECTED"
##            u.close()
##        
    except urllib2.HTTPError, e:
        print url+ " - " + " ERROR CODE: " + str(e.getcode())
        pass
    except urllib2.URLError, e:
        print url+" is NON-RESPONSIVE - " +str(e.args)
        pass
    
print "All other URL's returned valid title codes"


