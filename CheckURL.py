import urllib2

url_list = ['http://www.google.com', 'http://www.apple.com', 'http://www.yahoo.com']

try:
    for url in url_list:
        urllib2.urlopen(url)
       # print "link is good"
except urllib2.HTTPError, e:
    print(e.code, "link is broken")
except urllib2.URLError, e:
    print(e.args)