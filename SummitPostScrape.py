#SummitPostScrape.py

import urllib2
from bs4 import BeautifulSoup

#get website
url = "http://www.summitpost.org/appalachian-trail-mileage-chart/593282"

#get content from website
content = urllib2.urlopen(url).read()
soup = BeautifulSoup(content)

print soup.find_all('tr')
#for i in soup.find_all('tr')


