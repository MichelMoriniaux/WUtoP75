import socket
import time
import sys
import signal
import logging
from wunderground_pws import WUndergroundAPI, units

host = "192.168.248.6"
port = 9998
interval = 600
s = None
logging.basicConfig(level=logging.INFO)

wu = WUndergroundAPI(
    api_key='yourAPIkeyhere',
    default_station_id='KCALANDE10',
    units=units.METRIC_UNITS,
)

def interrupt_handler(signum, frame):
  logging.debug("Caught SIGINT closing connection...")
  try:
    s.close()
    logging.debug("closed")
  except:
    pass
  logging.debug("Exiting")
  sys.exit(0)


def fetch():
  # first get the weather data from WU
  logging.debug("Getting data from WU...")
  try:
    result = wu.current()['observations'][0]
  except:
    logging.error("Error fetching data from WU")
    return
  logging.debug("Done")
  temp = result['metric']['temp']
  humid = result['humidity']
  pressure = result['metric']['pressure']
  logging.debug(f"p: {str(pressure)}mb, t: {str(temp)}C, h: {str(humid)}%")

  # connect to the mount through the persistent control channel
  try:
    s = socket.socket()
  except socket.error as e:
    logging.error("Error creating socket: %s" % e) 
    return
  logging.debug("Connecting to mount...")
  try:
    s.connect((host, port))
  except socket.error as e: 
    logging.error("Connection error: %s" % e) 
    return
  logging.debug("Connected, sending data")
  try:
    s.send(":SX9A," + str(temp) + "#")
    s.send(":SX9B," + str(pressure) + "#")
    s.send(":SX9C," + str(humid) + "#")
  except socket.error as e: 
    logging.error("Send error: %s" % e) 
    return
  logging.debug("Closing connection")
  s.close()

if __name__ == '__main__':
  signal.signal(signal.SIGINT, interrupt_handler)
  while True:
    fetch()
    logging.debug(f"Sleeping for {interval}s")
    time.sleep(interval)
