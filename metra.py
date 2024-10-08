import urllib3
import json
import re

from configparser import ConfigParser
from datetime import datetime, date, time, timedelta
from threading import Thread
from time import sleep, monotonic

USERNAME = ""
PASSWORD = ""

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# read from config file
config = ConfigParser()
config.read("config/metra.ini")
USERNAME = config.get("DEFAULT", "username", fallback=USERNAME)
PASSWORD = config.get("DEFAULT", "password", fallback=PASSWORD)

# assert the API key username and password are valid
assert len(USERNAME) == 32, "32 character username required"
assert len(PASSWORD) == 32, "32 character password required"


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
        # skip previous days
        r_date = date.today() if start_date < date.today() else start_date
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

    @property
    def minutes(self) -> int:
        delta = self.time - datetime.now()
        return int(delta.days * 24 * 60 + delta.seconds / 60)

    @property
    def time_until(self) -> str:
        minutes = self.minutes
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes % 60 == 0:
            return f"{minutes // 60} hours"
        else:
            return f"{minutes // 60} hr {minutes % 60:0=2d} min"

    def __str__(self):
        direction = "In-Bound" if self.inbound else "Out-Bound"
        live = " [LIVE]" if self.live else ""
        return f'{self.line} {self.train} ({direction}) to {self.stop_id} in {self.time_until}{live}'


class Metra:

    def __init__(self):
        # get all services from Metra
        services = {s["service_id"]: s for s in make_request("https://gtfsapi.metrarail.com/gtfs/schedule/calendar")}

        # get all trips from Metra and build trips for desired line
        self.trips = {t["trip_id"]: Trip(t["trip_id"], t["direction_id"] == 1, services[t["service_id"]])
                      for t in make_request("https://gtfsapi.metrarail.com/gtfs/schedule/trips")}

        # get all scheduled stops from Metra and add stops to appropriate line
        for stop in make_request("https://gtfsapi.metrarail.com/gtfs/schedule/stop_times"):
            self.trips[stop["trip_id"]].add_stop(stop["stop_id"], stop["arrival_time"])

        # flatten list of stops from trips
        self.stops = []
        for tid in self.trips:
            self.stops += self.trips[tid].stops

        self.lines = list({stop.line for stop in self.stops})
        self.lines.sort()
        self.stations = list({stop.stop_id for stop in self.stops})
        self.stations.sort()

        self.live = []
        self.running = False
        self.last_update = -1

    def live_thread(self):
        while self.running:
            trains = make_request("https://gtfsapi.metrarail.com/gtfs/tripUpdates")
            live = []
            for train in trains:
                tid = train["trip_update"]["trip"]["trip_id"]
                if tid in self.trips:
                    for update in train["trip_update"]["stop_time_update"]:
                        arrival = update["arrival"]
                        if arrival is not None:
                            s_time = datetime.fromisoformat(arrival["time"]["low"]).astimezone()
                            l_date = s_time.date()
                            l_time = s_time.time().isoformat()
                            live.append(Stop(tid, update["stop_id"], self.trips[tid].inbound, l_date, l_time, True))

            self.live = live
            self.last_update = monotonic()
            sleep(30)

    def start(self):
        self.running = True
        Thread(target=self.live_thread, daemon=True).start()

    def stop(self):
        self.running = False

    def get_next(self, line, stop, live=True, count=1):
        line = line.upper()
        stop = stop.upper()

        # get all trains in the next 6 hours (allow up to 15 minutes late)
        now = datetime.now()
        upcoming = []
        trains = []
        for s in self.stops:
            # random overlapping schedules produce duplicated trains, only prevent each train once
            if s.stop_id == stop and s.line.startswith(line) and s.train not in trains and \
                    now - timedelta(minutes=15) < s.time < now + timedelta(hours=6):
                trains.append(s.train)
                upcoming.append(s)

        if live:
            # determine if there is a more accurate (live) time
            for s in self.live:
                if s.stop_id == stop:
                    # replace a matching stop with its live counterpart
                    if s.train in trains:
                        upcoming[trains.index(s.train)] = s
                    # add a stop if it is entirely missing (likely very late)
                    else:
                        upcoming.append(s)
                        upcoming.sort(key=lambda u: u.time)

        # filter out passed trains
        upcoming = [s for s in upcoming if now < s.time]

        # sort trains by time
        upcoming.sort(key=lambda u: u.time)

        # find the number of requested in-bound and out-bound trains
        inbound = [s for s in upcoming if s.inbound][:count]
        outbound = [s for s in upcoming if not s.inbound][:count]

        if count == 1:
            return inbound[0], outbound[0]
        else:
            return inbound, outbound
