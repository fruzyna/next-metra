#!/usr/bin/python3
import argparse
from time import sleep

from metra import Metra, config

# read from config file
DEFAULT_LINE = config.get("DEFAULT", "default_line", fallback="UP-NW")
DEFAULT_STOP = config.get("DEFAULT", "default_stop", fallback="DESPLAINES")

# parse command line arguments
parser = argparse.ArgumentParser(description='Continuously report upcoming Metra trains to a given station.')
parser.add_argument("-l", "--line", dest="line", default=DEFAULT_LINE, help='short train line name (UP-NW)')
parser.add_argument("-s", "--stop", dest="stop", default=DEFAULT_STOP, help='station identifier (DESPLAINES)')
parser.add_argument("-i", "--interval", dest="interval", default=60, help='update interval in seconds')
args = parser.parse_args()

# fetch initial data from Metra, then start polling for live data
metra = Metra()
metra.start()

try:
    while metra.running:
        # wait for live data to be fetched
        while metra.last_update < 0:
            sleep(1)

        first_inbound, first_outbound = metra.get_next(args.line, args.stop)

        print("----------")
        print(first_inbound)
        print(first_outbound)
        sleep(args.interval)

except KeyboardInterrupt:
    metra.stop()
