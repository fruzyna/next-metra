# next-metra

Script that reports the next in&amp;out-bound Metra train every minute.

## API Key

This scripts requires an API key (username and password) from Metra to access their GTFS API.
You can request a pair [here](https://metra.com/developers).
Once you receive your key pair, place them in the USERNAME and PASSWORD fields at the top of `metra.py`.

## Usage

```
usage: metra.py [-h] [-l LINE] [-s STOP]

Continuously report upcoming Metra trains to a given station.

options:
  -h, --help            show this help message and exit
  -l LINE, --line LINE  short train line name (UP-NW)
  -s STOP, --stop STOP  station identifier (DESPLAINES)
```
