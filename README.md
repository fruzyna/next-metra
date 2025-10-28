# next-metra

Scripts that reports the next in&amp;out-bound Metra trains.

## API Key

These scripts require an API key (username and password) from Metra to access their GTFS API.
You can request a pair [here](https://metra.com/developers).
Once you receive your key pair, place them in the username and password fields in a `metra.ini` file, see the example format below.
```
[DEFAULT]
token=123456789012345678901234567890123456789012345678901
default_line=UP-NW
default_stop=DESPLAINES
```

## CLI Usage

```
usage: metra-cli.py [-h] [-l LINE] [-s STOP]

Continuously report upcoming Metra trains to a given station.

options:
  -h, --help                        show this help message and exit
  -l LINE, --line LINE              short train line name (UP-NW)
  -s STOP, --stop STOP              station identifier (DESPLAINES)
  -i INTERVAL, --interval INTERVAL  update interval in seconds
```

## Server Startup
```
uvicorn --host 0.0.0.0 metra-server:app
```