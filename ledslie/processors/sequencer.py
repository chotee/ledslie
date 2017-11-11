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

from zlib import crc32

import paho.mqtt.client as mqtt
from collections import deque

import msgpack
from threading import Timer

from flask.config import Config

class GenericProcessor(object):
    pass


class Image(object):
    def __init__(self, img_data, **kwargs):
        self.img_data = img_data
        for name, value in kwargs.items():
            setattr(self, name, value)

    def __bytes__(self):
        return self.img_data

class ImageSequence(object):
    def __init__(self, config):
        self.config = config
        self.id = None
        self.sequence = []

    def load(self, payload):
        self.id, seq = msgpack.unpackb(payload)
        for image, image_info in seq:
            if len(image) != self.config.get('DISPLAY_WIDTH') * self.config.get('DISPLAY_HEIGHT'):
                break
            try:
                image_duration = image_info[b'duration']
            except KeyError:
                break
            self.sequence.append(Image(image, duration=image_duration))
        return self

    def __iter__(self):
        return iter(self.sequence)


class Sequencer(GenericProcessor):
    def __init__(self, config):
        self.config = config
        self.queue = deque()
        self.timer = None

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("ledslie/sequences/1")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, mqtt_msg):
        queue_started_empty = len(self.queue) == 0
        seq = ImageSequence(self.config).load(mqtt_msg.payload)
        client.publish("ledslie/logs/sequencer", "Incoming %s" % seq.id)
        self.queue.extend(seq)
        if queue_started_empty and self.queue:
            self.schedule_image(client)

    def send_image(self, client, image):
        client.publish("ledslie/frames/1", bytes(image))
        client.publish("ledslie/logs/sequencer", "Published image %s" % crc32(bytes(image)))

    def schedule_image(self, client):
        image = self.queue.popleft()
        self.send_image(client, image)
        if self.queue:  # there's still work in the queue
            client.publish("ledslie/logs/sequencer", "Scheduling next image for %dms. %d images in queue" %
                           (image.duration, len(self.queue)))
            self.timer = Timer(image.duration/1000.0, self.schedule_image, [client]).start()
        else:
            client.publish("ledslie/logs/sequencer", "Image Queue empty")

    def run(self, client):
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(self.config.get('MQTT_BROKER_URL'),
                       self.config.get('MQTT_BROKER_PORT'),
                       self.config.get('MQTT_KEEPALIVE'))
        client.loop_forever()


if __name__ == '__main__':
    config = Config('.')
    config.from_object('ledslie.defaults')
    config.from_envvar('LEDSLIE_CONFIG')
    client = mqtt.Client()
    Sequencer(config).run(client)
