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
	rain_in = None #hourly rain
	rain_daily_in = None #daily rain
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
		'id':args.id,
		'password':args.pw,
		'dateutc':readings.timestamp,
		'winddir':readings.winddir_deg,
		'windspeedmph':readings.wind_mph,
		'humidity':readings.rh_pct,
		'tempf':readings.temp_f,
		'rainin':readings.rain_in,
		'dailyrainin':readings.rain_daily_in,
		#'baromin':29.92,
		#'dewptf':29,
		'softwaretype':'rtl_433_to_wu'})

	if (args.testonly):
	    print params
	else:
	    result = urllib.urlopen(wu_uri + "?%s" % params)	
	    print result.read()

proc = subprocess.Popen('/home/pi/rtl_433/build/src/rtl_433', stdout=subprocess.PIPE)

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
			

		elif int(msgobj.group(4)) == 31:
			msg31mo = msg31_re.match(line)
			got_msg31=True
			weather.timestamp = msgobj.group(1)
			weather.wind_mph = float(msg31mo.group(1))
			weather.winddir_deg = float(msg31mo.group(3))
			cur_rain = float(msg31mo.group(4)) #inches rain since last message
			
			#handle hourly rain
			if (cur_hour != datetime.time.hour):
				cur_hour = datetime.time.hour
				rain_hour = 0.0
		    
			rain_hour = rain_hour + cur_rain
			weather.rain_in = rain_hour
			
			if (cur_day != datetime.date.day):
				cur_day = datetime.date.day
				rain_day = 0.0
			
			rain_day = rain_day + cur_rain
			weather.daily_rain_in = rain_day
			rain_total = rain_total + cur_rain
		else:
			so = startup_re.match(line)
			if (so is not None):
				rain_total = float(so.group(1))
				print "Got total rain of %1.3f in" % rain_total

	if (got_msg38 and got_msg31):
		print("Wind %1.3f mph, %1.3f F, %f" %(weather.wind_mph, weather.temp_f, weather.rh_pct))
		print("Wind %3.1f mph, dir %03.1f deg, Rain %1.2f" % (weather.wind_mph, weather.winddir_deg, weather.rain_in))
		got_msg31=False
		got_msg38=False
		update_wu(weather)
		weather.reset()

