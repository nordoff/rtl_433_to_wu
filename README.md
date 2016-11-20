rtl_433_to_wu
=============

Convert rtl_433 output to weatherunderground updates

This is a simple service that listens to the output of your Acurite 5-n-1 weather sensor and uploads it to weatherunderground.com. You can find one on [amazon](https://www.amazon.com/AcuRite-06004RM-Direction-Temperature-Humidity/dp/B00T0K8MNI/ref=sr_1_23?s=furniture&srs=11102085011&ie=UTF8&qid=1476489637&sr=1-23), sometimes Costco has a 5n1 with a display for cheaper.

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
Softlink weatherd to your service directory: /etc/init.d/ or wherever. Make sure the path in it points to wherever you put your cloned folder
it runs with `weatherd.py start|stop|restart` or `sudo service weatherd start|stop|restart`
Requres a configuration file named weather.ini in /etc/ containing the following
```
[station]
id=your_station_id (This should be ALL CAPS)
pw=station_pw
test=True|False ;set to true to simply print the URI string
```
