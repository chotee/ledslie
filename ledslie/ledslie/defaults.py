## Default config values
DEBUG=False
MQTT_BROKER_URL = 'localhost'  # use the free broker from HIVEMQ
MQTT_BROKER_PORT = 1883  # default port for non-tls connection
MQTT_KEEPALIVE = 60  # set the time interval for sending a ping to the broker to 5 seconds
# app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
# app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
# app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

SERIAL_BAUDRATE = 115200
SERIAL_PORT = '/dev/ttyUSB0'  # set to "fake" to run without serial port.
