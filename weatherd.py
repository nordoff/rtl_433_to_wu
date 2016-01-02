#!/bin/python

import urllib

params = urllib.urlencode({
    'action':'updateraw', 
    'id':'myid',
    'password':'mypw',
    'dateutc':'now', 
    'winddir':180, 
    'windspeedmph':2, 
    'humidity':50,
    'tempf':20,
    'rainin':0.0,
    'dailyrainin':0.0,
    'baromin':29.92,
    'dewptf':29,
    'softwaretype':'rtl_433_to_wu'})
    
print params
wu_uri = 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'
result = urllib.urlopen(wu_uri + "?%s" % params)

print result.read()