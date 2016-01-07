#!/bin/python

import subprocess
import os
import signal
import time
import sys
import re
import urllib

wu_uri = 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'

class Sensor:
	wind_mph = None
	temp_f = None
	rh_pct = None
	winddir_deg = None
	rain_in = None
	timestamp = None
	def reset(self):
		self.wind_mph = None
		self.temp_f = None
		self.rh_pct = None
		self.winddir_deg = None
		self.rain_in = None
		self.timestamp = None

def update_wu(readings):
	params = urllib.urlencode({
		'action':'updateraw',
		'id':'myid',
    		'password':'mypw',
    		'dateutc':readings.timestamp,
    		'winddir':readings.winddir_deg,
    		'windspeedmph':readings.wind_mph,
    		'humidity':readings.rh_pct,
    		'tempf':readings.temp_f,
    		'rainin':readings.rain_in,
    		#'dailyrainin':0.0,
    		#'baromin':29.92,
    		#'dewptf':29,
    		'softwaretype':'rtl_433_to_wu'})

	print params
	#result = urllib.urlopen(wu_uri + "?%s" % params)	
	#print result.read()

proc = subprocess.Popen('/home/pi/rtl_433/build/src/rtl_433', stdout=subprocess.PIPE,)

msgid_re = re.compile('(\d*-\d*-\d* \d*:\d*:\d*) Acurite 5n1 sensor (0x.{0,4}) Ch ([ABC]), Msg (\d\d)')
msg38_re = re.compile('.*Msg 38, Wind (\d+\.?\d*) kmph \/ (\d+\.?\d*) mph, ([\+\-]?\d+\.?\d*) C ([\+\-]?\d+\.?\d*) F (\d+\.?\d*) % RH')
msg31_re = re.compile('.*Msg 31, Wind (\d+\.?\d*) kmph \/ (\d+\.?\d*) mph (\d+\.?\d*).*rain gauge (\d+\.?\d*) in\.', flags=re.UNICODE)


got_msg31=False
got_msg38=False
weather = Sensor()

while(1):
	line = proc.stdout.readline()
	msgobj = msgid_re.match(line)
	if(msgobj):
		print("%s MsgId %s" % (msgobj.group(1), msgobj.group(4)))
		if int(msgobj.group(4)) == 38:
			msg38mo = msg38_re.match(line)
			got_msg38=True
			weather.timestamp = msgobj.group(1)
			weather.wind_mph = float(msg38mo.group(2))
			weather.temp_f = float(msg38mo.group(4))
			weather.rh_pct = float(msg38mo.group(5))
			print("Wind %1.3f mph, %1.3f F, %f" %(weather.wind_mph, weather.temp_f, weather.rh_pct))

		elif int(msgobj.group(4)) == 31:
			msg31mo = msg31_re.match(line)
			got_msg31=True
			weather.timestamp = msgobj.group(1)
			weather.wind_mph = float(msg31mo.group(1))
			weather.winddir_deg = float(msg31mo.group(3))
			weather.rain_in = float(msg31mo.group(4)) #inches rain since last message
			print("Wind mph %3.1f, dir %03.1f deg, Rain %1.2f" % (weather.wind_mph, weather.winddir_deg, weather.rain_in))

	if (got_msg38 and got_msg31):
		got_msg31=False
		got_msg38=False
		update_wu(weather)
		weather.reset()

