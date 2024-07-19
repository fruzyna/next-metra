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

# build stop page using data from API and query parameters
@app.get('/stop', response_class=HTMLResponse)
async def stop(line="UP-NW", stop="DESPLAINES"):
    line = line.upper()
    stop = stop.upper()

    first_inbound, first_outbound = metra.get_next(line, stop)

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
                    Inbound: #{first_inbound.train}<br>\
                    <h2>{LIVE_STR if first_inbound.live else ""}{first_inbound.minutes} minutes</h2>\
                    Outbound: #{first_outbound.train}<br>\
                    <h2>{LIVE_STR if first_outbound.live else ""}{first_outbound.minutes} minutes</h2>\
                </center>\
            </body>\
        </html>'
