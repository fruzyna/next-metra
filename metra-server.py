from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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

# build index to select line and stop
@app.get('/', response_class=HTMLResponse)
async def index():
    return f'<!DOCTYPE html>\
        <html lang="en">\
            <head>\
                <meta charset="utf-8"/>\
                <title>Metra Status</title>\
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">\
            </head>\
            <body>\
                <center>\
                    <h1>Next Metra Trains at </h1>\
                    <form action="/stop">\
                        <label for="line">Line:</label><br>\
                        <input type="text" id="line" name="line"><br><br>\
                        <label for="stop">Stop:</label><br>\
                        <input type="text" id="stop" name="stop"><br><br>\
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

    return f'<!DOCTYPE html>\
        <html lang="en">\
            <head>\
                <meta charset="utf-8"/>\
                <title>Metra {line} Status</title>\
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">\
                <style>{STYLES}</style>\
            </head>\
            <body>\
                <center>\
                    <h2>Next {line} Trains at </h2>\
                    <h1>{stop}</h1>\
                    <h3>Inbound - #{inbound[0].train}<h3>\
                    <h2>{LIVE_STR if inbound[0].live else ""}{inbound[0].time_until}</h2>\
                    {''.join([build_line(inbound[i]) for i in range(1, len(inbound))])}\
                    <h3>Outbound - #{outbound[0].train}</h3>\
                    <h2>{LIVE_STR if outbound[0].live else ""}{outbound[0].time_until}</h2>\
                    {''.join([build_line(outbound[i]) for i in range(1, len(outbound))])}\
                </center>\
            </body>\
        </html>'
