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


def typeset_1line(msg):
    image = Image.new("L", (144, 24))
    draw = ImageDraw.Draw(image)
    font_path = os.path.realpath(os.path.join(CURDIR, "..", "resources", "DroidSansMono.ttf"))
    try:
        font = ImageFont.truetype(font_path, 20)
    except OSError as exc:
        print("Can't find the font file '%s': %s" % (font_path, exc))
        return None
    draw.text((0, 0), msg, (255), font=font)
    return image


def typeset_3lines(lines):
    image = Image.new("L", (144, 24))
    draw = ImageDraw.Draw(image)
    font_path = os.path.realpath(os.path.join(CURDIR, "fonts", "DroidSansMono.ttf"))
    try:
        font = ImageFont.truetype(font_path, 9)
    except OSError as exc:
        print("Can't find the font file '%s': %s" % (font_path, exc))
        return None
    for i, msg in enumerate(lines):
        draw.text((0, (i*8)-2), msg, (255), font=font)
    return image


def send_image(client, image_id, image_data):
    data_objs = [image_id, image_data]
    # print("Sending the image data:")
    # pprint(data_objs)
    data = msgpack.packb(data_objs)
    client.publish("ledslie/sequences/1", data)


def on_message(client, userdata, mqtt_msg):
    data = msgpack.unpackb(mqtt_msg.payload)
    text_type = data[b'type']
    if text_type == b'1line':
        msg = data[b'text'].decode('UTF-8')
        client.publish("ledslie/logs/typesetter", "Typesetting '%s'" % msg)
        # pprint(data)
        image_bytes = typeset_1line(msg).tobytes()
    elif text_type == b'3lines':
        lines = [l.decode('UTF-8') for l in data[b'lines']]
        image_bytes = typeset_3lines(lines).tobytes()
    else:
        print("Unknown type %s" % text_type)
    if image_bytes is None:
        return
    send_image(client, generate_id(), [[image_bytes, {'duration': data.get('duration', 5000)}],])


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'show':
        show_text = sys.argv[2].split(',')
        img = typeset_3lines(show_text)
        if img:
            img.show()
        else:
            print("No image was generated.")
    else:
        main()
