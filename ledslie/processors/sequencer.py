from zlib import crc32

import paho.mqtt.client as mqtt
from collections import deque

import msgpack
from threading import Timer

from flask.config import Config

class GenericProcessor(object):
    pass


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
        seq_id, sequence = msgpack.unpackb(mqtt_msg.payload)
        client.publish("ledslie/logs/sequencer", "Incoming %s" % seq_id)
        for image, image_info in sequence:
            if len(image) != self.config.get('DISPLAY_WIDTH') * self.config.get('DISPLAY_HEIGHT'):
                return
            try:
                image_duration = image_info[b'duration']
            except KeyError:
                return
            self.queue.append([image_duration, image])
        client.publish("ledslie/logs/sequencer", "Send %s" % seq_id)
        if queue_started_empty and self.queue:
            self.schedule_image(client)

    def send_image(self, client, image):
        client.publish("ledslie/frames/1", image)
        crc32(image)
        client.publish("ledslie/logs/sequencer", "Published image %s" % crc32(image))

    def schedule_image(self, client):
        image_duration, image = self.queue.popleft()
        self.send_image(client, image)
        if self.queue:  # there's still work in the queue
            client.publish("ledslie/logs/sequencer", "Scheduling next image for %dms. %d images in queue" %
                           (image_duration, len(self.queue)))
            self.timer = Timer(image_duration/1000.0, self.schedule_image, [client]).start()
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
