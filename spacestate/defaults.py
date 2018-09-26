"""
I contain the default base configuration variables and values  that may be adapted for either different deployment
situations or even run-time. If these variables are not overridden anywhere, these are the values. We should not have
any configuration values that are not defined here, making this the list of all available settings.
"""

DEBUG=False
MQTT_BROKER_URL = 'localhost'  # use the free broker from HIVEMQ
MQTT_BROKER_PORT = 1883  # default port for non-tls connection
MQTT_BROKER_CONN_STRING = 'tcp:%s:%s' % (MQTT_BROKER_URL, MQTT_BROKER_PORT)
MQTT_KEEPALIVE = 60  # set the time interval for sending a ping to the broker to 5 seconds

SPACESTATE_URL = "http://techinc.nl/space/spacestate"
SPACESTATE_POLL_FREQ = 5.0
SPACESTATE_MQTT_TOPIC = 'spacestate'

