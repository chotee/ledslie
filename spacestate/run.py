#!/usr/bin/env python
import logging
import time

import paho.mqtt.publish as publish
# import paho.mqtt.client as mqtt
import requests

from defaults import MQTT_KEEPALIVE, MQTT_BROKER_PORT, MQTT_BROKER_URL, SPACESTATE_MQTT_TOPIC, SPACESTATE_URL, \
    SPACESTATE_POLL_FREQ

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def retrieve_state(url):
    req = requests.get(url)
    if req.status_code == 200:
        state = req.text
        log.debug("Retrieved state '%s'", state)
        return state
    else:
        return None


def main():
    old_state=None
    log.warning("Starting spacestate.")
    while True:
        log.debug("Loop")
        state = retrieve_state(SPACESTATE_URL)
        if not old_state or old_state != state:
            log.info("publishing '%s'", state)
            publish.single(topic=SPACESTATE_MQTT_TOPIC, payload=state, qos=2, retain=True,
                           hostname=MQTT_BROKER_URL, port=MQTT_BROKER_PORT)
            old_state = state
            log.debug("Done")
        log.debug("sleeping for %s", SPACESTATE_POLL_FREQ)
        time.sleep(SPACESTATE_POLL_FREQ)


if __name__ == '__main__':
    main()
