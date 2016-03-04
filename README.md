rtl_433_to_wu
=============

Convert rtl_433 output to weatherunderground updates

This is a simple script that listens to the output of your Acurite 5-n-1 weather sensor and uploads it to weatherunderground.com.

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
This is not a proper service - I usually just kick it off with nohup:
    `nohup weatherd.py -i MYSTATION -p mypasswd`
```
usage: weatherd.py [-h] [--id ID] [--password PW] [--test]

Weather Underground updater

optional arguments:
  -h, --help            show this help message and exit
  --id ID, -i ID        station id/username
  --password PW, -p PW  weatherunderground password
  --test, -t            dry run, only print GET string
```
