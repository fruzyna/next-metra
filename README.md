# next-metra

Script that reports the next in&amp;out-bound Metra train every minute.

## API Key

This scripts requires an API key (username and password) from Metra to access their GTFS API.
You can request a pair [here](https://metra.com/developers).
Once you receive your key pair, place them in the username and password fields in a `metra.ini` file, see the example format below.
```
[DEFAULT]
username=12345678901234567890123456789012
password=12345678901234567890123456789012
default_line=UP-NW
default_stop=DESPLAINES
```

## Usage

```
usage: metra.py [-h] [-l LINE] [-s STOP]

Continuously report upcoming Metra trains to a given station.

options:
  -h, --help            show this help message and exit
  -l LINE, --line LINE  short train line name (UP-NW)
  -s STOP, --stop STOP  station identifier (DESPLAINES)
```
