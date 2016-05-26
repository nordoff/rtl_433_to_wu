rtl_433_to_wu
=============

Convert rtl_433 output to weatherunderground updates

This is a simple service that listens to the output of your Acurite 5-n-1 weather sensor and uploads it to weatherunderground.com.

Installation
------------
*Hardware*
* Acurite 5-n-1 weather sensor (provides rainfall, humidity, temperature, windspeed, wind direction)
* [USB RTL receiver](http://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/) (also available on amazon)

*Software*
* [rtl_433](https://github.com/merbanan/rtl_433) to be installed.
* rtl_433 requires [rtl-sdr](http://sdr.osmocom.org/trac/wiki/rtl-sdr)

Other information
-----------------
*Rainfall totals*
The rainfall totals are sawtooth counts, that is, the total accumulates from the top of the hour (or day) starting at zero.

How to use
----------
Softlink weatherd.py to your service directory: /etc/init.d/ or wherever
it runs with `weatherd.py start|stop|restart`
Requres a configuration file named weather.ini containing the following
```
[station]
id=your_station_id
pw=station_pw
test=True|False ;set to true to simply print the URI string
```
