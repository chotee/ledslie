from datetime import datetime

import paho.mqtt.client as mqtt

import msgpack
import pprint

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")
    client.subscribe("ledslie/#")


def on_raw(mqtt_msg):
    pprint.pprint(mqtt_msg.payload)

def on_msgpack(mqtt_msg):
    payload = msgpack.unpackb(mqtt_msg.payload)
    pprint.pprint(payload)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, mqtt_msg):
    topic = mqtt_msg.topic
    print('%s %s ' % (datetime.now(), topic))
    func = {
        'frames': on_raw,
        'logs': on_raw,
        'sequences': on_msgpack,
    }[topic.split('/')[1]]

    func(mqtt_msg)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()