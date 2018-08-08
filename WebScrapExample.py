import urllib2
from bs4 import BeautifulSoup

#get website
wiki = "https://en.wikipedia.org/wiki/List_of_state_and_union_territory_capitals_in_India"

#get content from website
content = urllib2.urlopen(wiki)

#Prettify HTMLto make HTML easier to parse
soup = BeautifulSoup(content,'html.parser')
    #print (soup.prettify()) #worked

print soup.title.string
print soup.td
