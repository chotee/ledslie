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
# app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
# app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
# app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

FONT_DIRECTORY = '../../resources/fonts/'

SERIAL_BAUDRATE = 115200
SERIAL_PORT = '/dev/ttyACM0'  # set to "fake" to run without serial port.

DISPLAY_WIDTH = 144
DISPLAY_HEIGHT = 24
DISPLAY_SIZE = DISPLAY_WIDTH * DISPLAY_HEIGHT
DISPLAY_DEFAULT_DELAY = 5000  # Delay in miliseconds
