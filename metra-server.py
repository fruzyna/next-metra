from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime

from metra import Metra

# fetch initial data from Metra, then start polling for live data
metra = Metra()
metra.start()

# create an instance of FastAPI
app = FastAPI()

LIVE_STR = '<div class="live"></div> '
STYLES = '\
.live {\
    display: inline-block;\
    width: 20px;\
    height: 20px;\
    border-radius: 50%;\
    background-color: red;\
}'
LINES = ''.join([f'<option value="{line}">{line}</option>' for line in metra.lines])
STOPS = ''.join([f'<option value="{stop}">{stop}</option>' for stop in metra.stations])

# build a map of lines to stops
stop_map = {line: set() for line in metra.lines}
for stop in metra.stops:
    stop_map[stop.line].add(stop.stop_id)

stop_map = {line: sorted(list(stop_map[line])) for line in metra.lines}

# build a JS function to update the stops dropdown by the selected line
stop_filter = "(event) => { map = " + str(stop_map) + ";\
document.getElementById('stop').innerHTML = map[event.target.value].map(stop => " \
              "`<option values='${stop}'>${stop}</option>`).join('');\
console.log(map, event.target.value, map[event.target.value]);}"

base_headers = '<meta charset="utf-8"/>\
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">'


# build index to select line and stop
@app.get('/', response_class=HTMLResponse)
async def index():
    return f'<!DOCTYPE html>\
        <html lang="en">\
            <head>\
                {base_headers}\
                <title>Metra Status</title>\
            </head>\
            <body>\
                <center>\
                    <h1>Next Metra Trains at </h1>\
                    <form action="/stop">\
                        <label for="line">Line:</label>\
                        <select id="line" name="line" onchange="({stop_filter})(event)">{LINES}</select><br><br>\
                        <label for="stop">Stop:</label>\
                        <select id="stop" name="stop">{STOPS}</select><br><br>\
                        <input type="submit" value="Search">\
                    </form>\
                </center>\
            </body>\
        </html>'


def build_line(stop) -> str:
    return f"#{stop.train} - {stop.time_until}<br>"


# build stop page using data from API and query parameters
@app.get('/stop', response_class=HTMLResponse)
async def stop(line="UP-NW", stop="DESPLAINES", count=3):
    line = line.upper()
    stop = stop.upper()

    inbound, outbound = metra.get_next(line, stop, count=int(count))
    if int(count) == 1:
        inbound = [inbound]
        outbound = [outbound]

    next_trains = ''
    if inbound:
        next_trains = f'<h3>Inbound - #{inbound[0].train}<h3>\
            <h2>{LIVE_STR if inbound[0].live else ""}{inbound[0].time_until}</h2>\
            {"".join([build_line(inbound[i]) for i in range(1, len(inbound))])}'
    else:
        next_trains += '<h3>Inbound - None</h3>'

    if outbound:
        next_trains += f'<h3>Outbound - #{outbound[0].train}</h3>\
            <h2>{LIVE_STR if outbound[0].live else ""}{outbound[0].time_until}</h2>\
            {"".join([build_line(outbound[i]) for i in range(1, len(outbound))])}'
    else:
        next_trains += '<h3>Outbound - None</h3>'

    return f'<!DOCTYPE html>\
        <html lang="en">\
            <head>\
                {base_headers}\
                <title>Metra {line} Status</title>\
                <style>{STYLES}</style>\
            </head>\
            <body>\
                <center>\
                    <h2>Next {line} Trains at </h2>\
                    <h1>{stop}</h1>\
                    {next_trains}\
                </center>\
            </body>\
        </html>'


# build stop page using data from API and query parameters
@app.get('/time', response_class=HTMLResponse)
async def time():
    now = datetime.now()

    return f'<!DOCTYPE html>\
        <html lang="en">\
            <head>\
                {base_headers}\
                <title>Server Time</title>\
            </head>\
            <body>\
                <center>\
                    <h2>Current Server Time</h2>\
                    <h2>{now.strftime("%A, %B %d")}</h2>\
                    <h1>{now.strftime("%H:%M:%S")}</h1>\
                </center>\
            </body>\
        </html>'
