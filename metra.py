#!/usr/bin/python3
import argparse
import urllib3
import json
import re

from configparser import ConfigParser
from datetime import datetime, date, time, timedelta
from time import sleep

USERNAME = ""
PASSWORD = ""

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# read from config file
config = ConfigParser()
config.read("metra.ini")
USERNAME = config.get("DEFAULT", "username", fallback=USERNAME)
PASSWORD = config.get("DEFAULT", "password", fallback=PASSWORD)
DEFAULT_LINE = config.get("DEFAULT", "default_line", fallback="UP-NW")
DEFAULT_STOP = config.get("DEFAULT", "default_stop", fallback="DESPLAINES")

# assert the API key username and password are valid
assert len(USERNAME) == 32, "32 character username required"
assert len(PASSWORD) == 32, "32 character password required"

# parse command line arguments
parser = argparse.ArgumentParser(description='Continuously report upcoming Metra trains to a given station.')
parser.add_argument("-l", "--line", dest="line", default=DEFAULT_LINE, help='short train line name (UP-NW)')
parser.add_argument("-s", "--stop", dest="stop", default=DEFAULT_STOP, help='station identifier (DESPLAINES)')
args = parser.parse_args()

def make_request(url: str):
    """Make a web request using the set username and password to the given URL."""
    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth=f"{USERNAME}:{PASSWORD}")
    res = http.request("GET", url, headers=headers)

    if res.status != 200:
        print("Invalid response", res.status)
        exit(1)

    return json.loads(res.data)

class Trip:

    def __init__(self, trip: str, inbound: bool, service: dict):
        self.trip = trip
        self.inbound = inbound
        self.dates = []
        self.stops = []

        # generate a list of dates from the start, end, and service
        start_date = date.fromisoformat(service["start_date"])
        end_date = date.fromisoformat(service["end_date"])
        r_date = start_date
        while r_date <= end_date:
            if service[WEEKDAYS[r_date.weekday()]]:
                self.dates.append(r_date)

            r_date += timedelta(days=1)

    def add_stop(self, stop_id: str, time_str: str):
        """Add stops for each date at the given time."""
        for s_date in self.dates:
            self.stops.append(Stop(self.trip, stop_id, self.inbound, s_date, time_str))

class Stop:

    def __init__(self, trip_id: str, stop_id: str, inbound: bool, stop_date: date, time_str: str, live=False):
        self.trip_id = trip_id
        self.stop_id = stop_id
        self.inbound = inbound
        self.live = live

        # break out the line and train from the trip ID
        parts = self.trip_id.split("_")
        self.line = parts[0]
        self.train = re.sub(r"\D+", "", parts[1])

        # parse the time string and adjust it forward if it is the next day
        try:
            stop_time = time.fromisoformat(time_str)
        except ValueError:
            parts = time_str.split(":")
            stop_time = time(int(parts[0]) - 24, int(parts[1]))
            stop_date += timedelta(days=1)

        # combine date and time into datetime
        self.time = datetime.combine(stop_date, stop_time)

    def __str__(self):
        minutes = int((self.time - datetime.now()).seconds / 60)
        return f"{self.line} {self.train} ({"In-Bound" if self.inbound else "Out-Bound"}) to {self.stop_id} in {minutes} minutes {"[LIVE]" if self.live else ""}"

# get all services from Metra
services = {s["service_id"]:s for s in make_request("https://gtfsapi.metrarail.com/gtfs/schedule/calendar")}

# get all trips from Metra and build trips for desired line
trips = {t["trip_id"]:Trip(t["trip_id"], t["direction_id"] == 0, services[t["service_id"]]) for t in make_request("https://gtfsapi.metrarail.com/gtfs/schedule/trips")
         if t["trip_id"].startswith(args.line)}

# get all scheduled stops from Metra and add stops to appropriate line
for stop in make_request("https://gtfsapi.metrarail.com/gtfs/schedule/stop_times"):
    tid = stop["trip_id"]
    if tid.split("_")[0] == args.line and stop["stop_id"] == args.stop:
        trips[tid].add_stop(stop["stop_id"], stop["arrival_time"])

# flatten list of stops from trips
stops = []
for tid in trips:
    stops += trips[tid].stops

while True:
    # find the first (in the future) in-bound and out-bound trains
    first_inbound = None
    first_outbound = None
    for s in stops:
        if s.time > datetime.now():
            if s.inbound and (first_inbound is None or s.time < first_inbound.time):
                first_inbound = s
            elif not s.inbound and (first_outbound is None or s.time < first_outbound.time):
                first_outbound = s

    # determine if there is a more accurate time
    trains = make_request("https://gtfsapi.metrarail.com/gtfs/tripUpdates")
    for train in trains:
        tid = train["trip_update"]["trip"]["trip_id"]
        if tid in trips:
            for update in train["trip_update"]["stop_time_update"]:
                if update["stop_id"] == args.stop:
                    arrival = update["arrival"]
                    if arrival is not None:
                        s_time = datetime.fromisoformat(arrival["time"]["low"]).astimezone()
                        estimated = Stop(tid, args.stop, trips[tid].inbound, s_time.date(), s_time.time().isoformat(), True)
                        for stop in stops:
                            if stop.trip_id == tid and stop.stop_id == args.stop:
                                if trips[tid].inbound:
                                    first_inbound = estimated
                                else:
                                    first_outbound = estimated

                                break

    print("----------")
    print(first_inbound)
    print(first_outbound)
    sleep(60)
