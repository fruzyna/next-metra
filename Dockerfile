FROM python:3

# install app and prereqs in /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt
RUN mkdir -p /usr/src/app/next-metra/config
COPY metra.py metra-server.py /usr/src/app/next-metra/
RUN ln -s /usr/src/app/next-metra/config /config

# set default environment variables
ENV WR_WORKERS=1
ENV TZ=America/Chicago

# prepare container for app
WORKDIR next-metra
EXPOSE 80
VOLUME /config

# run python server
CMD uvicorn --host 0.0.0.0 --port 80 --workers $WR_WORKERS metra-server:app
