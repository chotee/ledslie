#!/usr/bin/env python3
import logging
import asyncio
import serial

import paho.mqtt.client as mqtt

from .defaults import SERIAL_PORT, SERIAL_BAUD, MQTT_TOPIC_FROM_SERIAL, MQTT_BROKER_URL, MQTT_BROKER_PORT, \
    MQTT_KEEPALIVE

log = logging.basicConfig(level=logging.DEBUG)

s = serial.Serial(SERIAL_PORT, SERIAL_BAUD)

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    log.info("MQTT Connected. Code %s" % rc)

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, MQTT_KEEPALIVE)


def _parse_line(data):
    parts = data.split(" ", 4)
    sender_id = parts[3]
    data_part = parts[4].split("=", 1)[1]
    return sender_id, data_part


def serial2mqtt():
    '''
    read a line and print.
    '''
    text = ""
    msg = s.read().decode()
    while (msg != '\n'):
        text += msg
        msg = s.read().decode()
    log.debug(text)
    sender_id, message = _parse_line(text)
    mqtt_client.publish(MQTT_TOPIC_FROM_SERIAL+"/"+sender_id, message)


print("Starting")
loop = asyncio.get_event_loop()
loop.add_reader(s, serial2mqtt)
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.close()
print("Finished")
