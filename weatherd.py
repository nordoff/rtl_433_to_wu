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
import logging
import ConfigParser
import Daemon
import json

from decimal import Decimal

config = ConfigParser.ConfigParser()
config.read('/etc/weather.ini')

logger = logging.getLogger("weatherd")
logging.basicConfig(filename = '/var/log/weatherd.log', level=logging.INFO)


#parser = argparse.ArgumentParser(description='Weatherunderground updater')
#parser.add_argument('--id','-i', dest='id', help='station id/username')
#parser.add_argument('--password','-p',dest='pw', help='weatherunderground password')
#parser.add_argument('--test','-t',action='store_true',dest='testonly',help='dry run, only print GET string')
#args = parser.parse_args()


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
	logger.debug("update_wu [in]")
	try:
		params = urllib.urlencode({
			'action':'updateraw',
			'ID':config.get('station','id'),
			'PASSWORD':config.get('station','pw'),
			'dateutc':readings.timestamp,
			'winddir':readings.winddir_deg,
			'windspeedmph':readings.wind_mph,
			'humidity':readings.rh_pct,
			'tempf':readings.temp_f,
			'rainin':readings.rain_in, #rain in last hour
			'dailyrainin':readings.rain_daily_in, #rain in last day
			#'baromin':29.92,
			#dewpt eq from http://andrew.rsmas.miami.edu/bmcnoldy/Humidity.html
			'dewptf':243.04*(math.log(readings.rh_pct/100)+((17.625*readings.temp_f)/(243.04+readings.temp_f)))/(17.625-math.log(readings.rh_pct/100)-((17.625*readings.temp_f)/(243.04+readings.temp_f))),
			'softwaretype':'rtl_433_to_wu'})
	
		logger.debug(params)
		if (not config.has_option('station','test') or config.getboolean('station', 'test') == False):
			try:
	    			result = urllib.urlopen(wu_uri + "?%s" % params)	
	    			logger.info(result.read())
			except IOError as e:
				logger.error("IO Error: %s", e.strerror)
		else:
			logger.debug("Skipping GET of URL for test mode")
			logger.info(wu_uri + "?%s" % params)
	except ConfigParser.NoSectionError:
		logger.error("Missing config section")
	except Exception as e:
		logger.error(e.strerror)


class WeatherD(Daemon.Daemon):

	def run(self):
		logger.info("Starting weatherd")
		proc = subprocess.Popen(['/usr/local/bin/rtl_433','-M','newmodel','-F','json','-C','customary'], stdout=subprocess.PIPE)

		msgid_re = re.compile('(\d*-\d*-\d* \d*:\d*:\d*) Acurite 5n1 sensor (0x.{0,4}) Ch ([ABC]), Msg (\d\d)')
		msg38_re = re.compile('.*Msg 38, Wind (\d+\.?\d*) kmph \/ (\d+\.?\d*) mph, ([\+\-]?\d+\.?\d*) C ([\+\-]?\d+\.?\d*) F (\d+\.?\d*) % RH')
		msg31_re = re.compile('.*Msg 31, Wind (\d+\.?\d*) kmph \/ (\d+\.?\d*) mph (\d+\.?\d*).*rain gauge (\d+\.?\d*) in\.', flags=re.UNICODE)
		startup_re = re.compile('.*Msg 31, Total rain fall since last reset: (\d+\.?\d*)')

		got_msg31=False
		got_msg38=False
		rain_total = Decimal(0.0)
		rain_hour = Decimal(0.0)
		rain_day = Decimal(0.0)
		weather = Sensor()
		cur_hour = datetime.datetime.today().hour
		cur_day = datetime.datetime.today().day
		times = 0
		cur_rain = Decimal(0.0)
		at_startup=True

		while(1):
			line = proc.stdout.readline()
			msg = json.loads(line)
			if msg['model']=='Acurite-5n1':
				msgType = int(msg['message_type'])
				logger.debug("%s MsgId %s", msg['model'], msg['message_type'])
				if msgType == 56:
					got_msg38=True
					weather.timestamp = msg['time']
					weather.wind_mph = float(msg['wind_avg_mi_h'])
					weather.temp_f = float(msg['temperature_F'])
					weather.rh_pct = float(msg['humidity'])
					

				elif msgType == 49:
				
					got_msg31=True
					weather.timestamp = msg['time']
					weather.wind_mph = float(msg['wind_avg_mi_h'])
					weather.winddir_deg = float(msg['wind_dir_deg'])
					if at_startup:
						rain_total = Decimal(msg['rain_in'])
						at_startup = False
					cur_rain = Decimal(msg['rain_in']) - rain_total #inches rain since last message
						
					#handle hourly rain
					if (cur_hour != datetime.datetime.today().hour):
						logger.info("%s Resetting hourly rain total, was %1.1f", weather.timestamp, rain_hour)
						cur_hour = datetime.datetime.today().hour
						rain_hour = Decimal(0.0)
			    
					rain_hour += cur_rain
					weather.rain_in = rain_hour
				
					#handle daily rain
					if (cur_day != datetime.datetime.today().day):
						logger.info("%s Resetting daily rain total, was %1.1f",  weather.timestamp, rain_day)
						cur_day = datetime.datetime.today().day
						rain_day = Decimal(0.0)
				
					rain_day = rain_day + cur_rain
					weather.rain_daily_in = rain_day

					#total rain
					rain_total += cur_rain
				else:
					#total rain at startup
					so = startup_re.match(line)
					if (so is not None):
						rain_total = Decimal(so.group(1))
						logger.info("%s Got total rain of %1.3f in", datetime.datetime.now(), rain_total)

			if (got_msg38 and got_msg31):
				logger.info("%s Wind %1.1f mph, dir %03.1f deg, %1.3f F, RH %1.1f%%, Rain (last) %1.2f in, (1hr) %1.2f in, (1day) %1.2f in", weather.timestamp, weather.wind_mph, weather.winddir_deg, weather.temp_f, weather.rh_pct, cur_rain, weather.rain_in, weather.rain_daily_in)
				got_msg31=False
				got_msg38=False
				logger.debug("Updating weather")
				update_wu(weather)
				logger.debug("Weather updated")
				weather.reset()
				cur_rain = Decimal(0.0)

if __name__ == "__main__":
        daemon = WeatherD('/tmp/weatherd.pid')
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart" % sys.argv[0]
                sys.exit(2)
