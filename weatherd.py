#!/usr/bin/python

import subprocess
import os
import signal
import time
import sys
import re
import urllib
import argparse
import datetime
import math

parser = argparse.ArgumentParser(description='Weatherunderground updater')
parser.add_argument('--id','-i', dest='id', help='station id/username')
parser.add_argument('--password','-p',dest='pw', help='weatherunderground password')
parser.add_argument('--test','-t',action='store_true',dest='testonly',help='dry run, only print GET string')
args = parser.parse_args()


wu_uri = 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'

class Sensor:
	wind_mph = None
	temp_f = None
	rh_pct = None
	winddir_deg = None
	rain_in = 0.0 #hourly rain
	rain_daily_in = 0.0 #daily rain
	timestamp = None
	def reset(self):
		self.wind_mph = None
		self.temp_f = None
		self.rh_pct = None
		self.winddir_deg = None
		self.rain_in = None
		self.rain_daily_in = None
		self.timestamp = None

def update_wu(readings):
	params = urllib.urlencode({
		'action':'updateraw',
		'ID':args.id,
		'PASSWORD':args.pw,
		'dateutc':readings.timestamp,
		'winddir':readings.winddir_deg,
		'windspeedmph':readings.wind_mph,
		'humidity':readings.rh_pct,
		'tempf':readings.temp_f,
		'rainin':readings.rain_in,
		'dailyrainin':readings.rain_daily_in,
		#'baromin':29.92,
		#dewpt eq from http://andrew.rsmas.miami.edu/bmcnoldy/Humidity.html
		'dewptf':243.04*(math.log(readings.rh_pct/100)+((17.625*readings.temp_f)/(243.04+readings.temp_f)))/(17.625-math.log(readings.rh_pct/100)-((17.625*readings.temp_f)/(243.04+readings.temp_f))),
		'softwaretype':'rtl_433_to_wu'})

	if (args.testonly):
	    print params
	else:
	    result = urllib.urlopen(wu_uri + "?%s" % params)	
	    print result.read()

proc = subprocess.Popen(['/home/pi/rtl_433/build/src/rtl_433','-R','39'], stdout=subprocess.PIPE)

msgid_re = re.compile('(\d*-\d*-\d* \d*:\d*:\d*) Acurite 5n1 sensor (0x.{0,4}) Ch ([ABC]), Msg (\d\d)')
msg38_re = re.compile('.*Msg 38, Wind (\d+\.?\d*) kmph \/ (\d+\.?\d*) mph, ([\+\-]?\d+\.?\d*) C ([\+\-]?\d+\.?\d*) F (\d+\.?\d*) % RH')
msg31_re = re.compile('.*Msg 31, Wind (\d+\.?\d*) kmph \/ (\d+\.?\d*) mph (\d+\.?\d*).*rain gauge (\d+\.?\d*) in\.', flags=re.UNICODE)
startup_re = re.compile('.*Msg 31, Total rain fall since last reset: (\d+\.?\d*)')

got_msg31=False
got_msg38=False
rain_total = 0.0
rain_hour = 0.0
rain_day = 0.0
weather = Sensor()
cur_hour = datetime.time.hour
cur_day = datetime.date.day
times = 0

while(1):
	line = proc.stdout.readline()
	msgobj = msgid_re.match(line)
	if(msgobj):
		#print("%s MsgId %s" % (msgobj.group(1), msgobj.group(4)))
		if int(msgobj.group(4)) == 38:
			msg38mo = msg38_re.match(line)
			if (msg38mo != None):
				got_msg38=True
				weather.timestamp = msgobj.group(1)
				weather.wind_mph = float(msg38mo.group(2))
				weather.temp_f = float(msg38mo.group(4))
				weather.rh_pct = float(msg38mo.group(5))
			

		elif int(msgobj.group(4)) == 31:
			msg31mo = msg31_re.match(line)
			if (msg31mo != None):
				got_msg31=True
				weather.timestamp = msgobj.group(1)
				weather.wind_mph = float(msg31mo.group(1))
				weather.winddir_deg = float(msg31mo.group(3))
				if (times != 0):
					cur_rain = float(msg31mo.group(4)) #inches rain since last message
				else:
					cur_rain = 0.02
				times = times + 1	
				#handle hourly rain
				if (cur_hour != datetime.time.hour):
					print("%s Resetting hourly rain total, was %1.1f" % (weather.timestamp, rain_hour))
					cur_hour = datetime.time.hour
					rain_hour = 0.0
		    
				rain_hour = rain_hour + cur_rain
				weather.rain_in = rain_hour
			
				#handle daily rain
				if (cur_day != datetime.date.day):
					print("%s Resetting daily rain total, was %1.1f" % (weather.timestamp, rain_day))
					cur_day = datetime.date.day
					rain_day = 0.0
			
				rain_day = rain_day + cur_rain
				weather.rain_daily_in = rain_day

				#total rain
				rain_total = rain_total + cur_rain
		else:
			#total rain at startup
			so = startup_re.match(line)
			if (so is not None):
				rain_total = float(so.group(1))
				print "%s Got total rain of %1.3f in" % (datetime.datetime.now(), rain_total)

	if (got_msg38 and got_msg31):
		print("Wind %1.1f mph, dir %03.1f deg, %1.3f F, RH %1.1f%%, Rain (1hr) %1.1f in, (1day) %1.1f in" %(weather.wind_mph, weather.winddir_deg, weather.temp_f, weather.rh_pct, weather.rain_in, weather.rain_daily_in))
		print("rain_hour %1.1f, rain_day %1.1f, rain_total %1.1f" % (rain_hour, rain_day, rain_total))
		got_msg31=False
		got_msg38=False
		update_wu(weather)
		weather.reset()

