#!/usr/bin/env python
import logging

import paho.mqtt.client as mqtt
import requests

from defaults import MQTT_KEEPALIVE, MQTT_BROKER_PORT, MQTT_BROKER_URL, SPACESTATE_MQTT_TOPIC, SPACESTATE_URL, \
    SPACESTATE_POLL_FREQ

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

client = mqtt.Client()


def retrieve_state(url):
    req = requests.get(url)
    if req.status_code == 200:
        state = req.text
        log.info("Retrieved state '%s'", state)
        return state
    else:
        return None


def main():
    log.warning("starting spacestate.")
    client.enable_logger(log)
    client.will_set(SPACESTATE_MQTT_TOPIC, payload='UNKNOWN', qos=1, retain=True)
    client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
    log.info("Connected")
    while True:
        log.info("Loop")
        state = retrieve_state(SPACESTATE_URL)
        res = client.publish(SPACESTATE_MQTT_TOPIC, payload=state, qos=2, retain=True)
        # res.wait_for_publish()
        log.info("Published %s (%s)", state, res.mid)
        client.loop(timeout=SPACESTATE_POLL_FREQ)

if __name__ == '__main__':
    main()
