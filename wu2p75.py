import socket
import time
import sys
import signal
import logging
import argparse
from wunderground_pws import WUndergroundAPI, units

host = "192.168.248.6"
port = 9998
interval = 600
station = 'KCALANDE10'
key = 'yourkeyhere'

s = None
logger = logging.getLogger('wu2p75')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter( logging.Formatter('[%(levelname)s](%(name)s): %(message)s') )
logger.addHandler(console_handler)

wu = WUndergroundAPI(
    api_key=key,
    default_station_id=station,
    units=units.METRIC_UNITS,
)

def interrupt_handler(signum, frame):
  logger.debug("Caught SIGINT closing connection...")
  try:
    s.close()
    logger.debug("closed")
  except:
    pass
  logger.debug("Exiting")
  sys.exit(0)


def fetch():
  # first get the weather data from WU
  logger.debug("Getting data from WU...")
  try:
    result = wu.current()['observations'][0]
  except:
    logger.error("Error fetching data from WU")
    return
  logger.debug("Done")
  temp = result['metric']['temp']
  humid = result['humidity']
  pressure = result['metric']['pressure']
  logger.debug(f"p: {str(pressure)}mb, t: {str(temp)}C, h: {str(humid)}%")

  # connect to the mount through the persistent control channel
  try:
    s = socket.socket()
  except socket.error as e:
    logger.error("Error creating socket: %s" % e) 
    return
  logger.debug("Connecting to mount...")
  try:
    s.connect((host, port))
  except socket.error as e: 
    logger.error("Connection error: %s" % e) 
    return
  logger.debug("Connected, sending data")
  try:
    buffer = ":SX9A," + str(temp) + ".0#"
    s.send(buffer.encode())
    logger.debug("received: " + s.recv(1).decode())
    buffer = ":SX9B," + str(pressure) + "#"
    s.send(buffer.encode())
    logger.debug("received: " + s.recv(1).decode())
    buffer = ":SX9C," + str(humid) + "#"
    s.send(buffer.encode())
    logger.debug("received: " + s.recv(1).decode())
  except socket.error as e: 
    logger.error("Send error: %s" % e) 
    return
  logger.debug("Closing connection")
  s.close()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Pull temperature, pressure and humidity from WU and push it to an Onstep mount")
  parser.add_argument("-d", "--debug", help="Enable debug",  action='store_true', required=False)
  parser.add_argument("-a", "--host", help="IP or hostname of mount", default=host, required=False)
  parser.add_argument("-s", "--station", help="WU station identifier", default=station, required=False)
  parser.add_argument("-k", "--key", help="WU api key", default=key, required=False)
  parser.add_argument("-i", "--interval", help="sumber of second to pause between updates", default=interval, required=False)
  args = parser.parse_args()
  if args.debug:
    console_handler.setLevel(level=logging.DEBUG)
  if args.host:
    host = args.host
  if args.station:
    station = args.station
  if args.key:
    key = args.key
  if args.interval:
    interval = args.interval
  signal.signal(signal.SIGINT, interrupt_handler)
  while True:
    fetch()
    logger.debug(f"Sleeping for {interval}s")
    time.sleep(interval)
