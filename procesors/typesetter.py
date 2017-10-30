#!/usr/bin/env python

# Start without arguments it's the typesetter
# Start with arguments "show 'hello world'" and it will show you how 'hello world' will be rendered.

import os, sys
from base64 import a85encode
from pprint import pprint

from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

import paho.mqtt.client as mqtt
import msgpack

CURDIR = os.path.split(__file__)[0]

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("ledslie/typesetter/1")


def generate_id():
    return a85encode(os.urandom(4)).decode("ASCII")


def typeset(msg):
    image = Image.new("L", (144, 24))
    draw = ImageDraw.Draw(image)
    font_path = os.path.realpath(os.path.join(CURDIR, "..", "resources", "DroidSansMono.ttf"))
    print("font_path %s" % font_path)
    font = ImageFont.truetype(font_path, 20)
    draw.text((0, 0), msg, (255), font=font)
    return image


def send_image(client, image_id, image_data):
    data_objs = [image_id, image_data]
    print("Sending the image data:")
    pprint(data_objs)
    data = msgpack.packb(data_objs)
    client.publish("ledslie/sequences/1", data)


def on_message(client, userdata, mqtt_msg):
    data = msgpack.unpackb(mqtt_msg.payload)
    client.publish("ledslie/logs/typesetter", "Typesetting '%s'" % data.get(b'text', 'Empty'))
    pprint(data)
    msg = data[b'text'].decode('UTF-8')
    image_bytes = typeset(msg).tobytes()
    send_image(client, generate_id(), [[image_bytes, {'duration': data.get('duration', 5000)}],])


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) == 3 and sys.argv[1] == 'show':
        show_text = sys.argv[2]
        img = typeset(show_text)
        img.show()
    else:
        main()
