#!/usr/bin/env python
"""
    Ledslie, a community information display
    Copyright (C) 2017  Chotee@openended.eu

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Start without arguments it's the typesetter
# Start with arguments "show 'hello world'" and it will show you how 'hello world' will be rendered.

import os, sys
from base64 import a85encode

from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw

from flask.config import Config
import paho.mqtt.client as mqtt
import msgpack

from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES, LEDSLIE_TOPIC_TYPESETTER

SCRIPT_DIR = os.path.split(__file__)[0]
os.chdir(SCRIPT_DIR)

config = Config(".")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(LEDSLIE_TOPIC_TYPESETTER)


def generate_id():
    return a85encode(os.urandom(4)).decode("ASCII")


def typeset_1line(msg):
    image = Image.new("L", (config.get("DISPLAY_WIDTH"),
                            config.get("DISPLAY_HEIGHT")))
    draw = ImageDraw.Draw(image)
    fontFileName = "DroidSansMono.ttf"
    font_path = _get_font_filepath(fontFileName)
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
    fontFileName = "DroidSansMono.ttf"
    font_path = _get_font_filepath(fontFileName)
    try:
        font = ImageFont.truetype(font_path, 9)
    except OSError as exc:
        print("Can't find the font file '%s': %s" % (font_path, exc))
        return None
    for i, msg in enumerate(lines):
        draw.text((0, (i*8)-2), msg, (255), font=font)
    return image


def _get_font_filepath(fontFileName):
    return os.path.realpath(os.path.join(config.get("FONT_DIRECTORY"), fontFileName))


def send_image(client, image_id, image_data):
    data_objs = [image_id, image_data]
    # print("Sending the image data:")
    # pprint(data_objs)
    data = msgpack.packb(data_objs)
    client.publish(LEDSLIE_TOPIC_SEQUENCES, data)


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
    config.from_object('ledslie.defaults')
    config.from_envvar('LEDSLIE_CONFIG')
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(config.get('MQTT_BROKER_URL'),
                   config.get('MQTT_BROKER_PORT'),
                   config.get('MQTT_KEEPALIVE'))
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
