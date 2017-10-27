from zlib import crc32

import paho.mqtt.client as mqtt

import serial

fake = True

if not fake:
    serial_port = serial.Serial('/dev/ttyUSB0', baudrate=115200)
else:
    print("running fake.")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("ledslie/frames/1")


def send_serial(data):
    if fake:
        print("would serialize %d bytes of %d now" % (
            len(data), crc32(data)))
    else:
        serial_port.write(data)


def prepare_image(image_data):
    shifted_data = bytearray()
    shifted_data.append(1 << 7) ## start with a new frame marker, a byte with the high byte 1
    for b in image_data:
        shifted_data.append(b >> 1)  # Downshift the data one byte. making the highbyte 0.
    return shifted_data


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, mqtt_msg):
    image = mqtt_msg.payload
    data = prepare_image(image)
    send_serial(data)
    client.publish("ledslie/logs/serializer", "Send image %s of %d bytes" % (
        crc32(image), len(image)))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()