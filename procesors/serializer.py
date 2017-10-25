import paho.mqtt.client as mqtt

import msgpack
import serial

serial_port = serial.Serial('/dev/ttyUSB0', baudrate=115200)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("ledslie/frames/1")


def send_serial(data):
    serial_port.write(data)


def prepare_image(image_data):
    shifted_data = bytearray()
    shifted_data.append(1 << 7) ## start with a new frame marker, a byte with the high byte 1
    for b in image_data:
        shifted_data.append(b >> 1)  # Downshift the data one byte. making the highbyte 0.
    return shifted_data


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, mqtt_msg):
    frame_image, frame_data = msgpack.unpackb(mqtt_msg.payload)
    data = prepare_image(frame_image)
    send_serial(data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()