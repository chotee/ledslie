from zlib import crc32

import paho.mqtt.client as mqtt
from collections import deque

import msgpack
from threading import Timer

queue = deque()
timer = None

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("ledslie/sequences/1")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, mqtt_msg):
    queue_started_empty = len(queue) == 0
    seq_id, sequence = msgpack.unpackb(mqtt_msg.payload)
    client.publish("ledslie/logs/sequencer", "Incoming %s" % seq_id)
    for image, image_info in sequence:
        image_duration = image_info[b'duration']
        queue.append([image_duration, image])
    client.publish("ledslie/logs/sequencer", "Send %s" % seq_id)
    if queue_started_empty:
        schedule_image(client)


def send_image(client, image):
    client.publish("ledslie/frames/1", image)
    crc32(image)
    client.publish("ledslie/logs/sequencer", "Published image %s" % crc32(image))


def schedule_image(client):
    global timer
    image_duration, image = queue.popleft()
    send_image(client, image)
    if queue:  # there's still work in the queue
        client.publish("ledslie/logs/sequencer", "Scheduling next image for %dms. %d images in queue" %
                       (image_duration, len(queue)))
        timer = Timer(image_duration/1000.0, schedule_image, [client]).start()
    else:
        client.publish("ledslie/logs/sequencer", "Image Queue empty")



def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()


if __name__ == '__main__':
    main()