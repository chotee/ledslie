import os
import sqlite3
import sys
import time

import paho.mqtt.client as mqtt


class RecordParts:
    def __init__(self, conn):
        self.conn = conn
        self.reset()

    def reset(self):
        self.wh = None
        self.pulse = None
        self.status = None

    def complete(self):
        return all([self.wh, self.pulse, self.status])


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("space/power/#")


def epoch_ns():
    return int(time.time() * 10**9)


def insert_record(parts: RecordParts):
    status_uptime = int(parts.status.split(b": ")[1])
    wh = float(parts.wh)
    pulse = int(parts.pulse)
    ts = epoch_ns()
    c = parts.conn.cursor()
    c.execute("INSERT INTO power (ts, wh, pulse, status_uptime) VALUES (?, ?, ?, ?)", (ts, wh, pulse, status_uptime))
    parts.conn.commit()
    #print("record: {}".format(RecordParts.__dict__))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata: RecordParts, msg):
    #print(msg.topic+" "+str(msg.payload))
    key = msg.topic.split('/')[-1]
    setattr(userdata, key, msg.payload)
    if userdata.complete():
        insert_record(userdata)
        userdata.reset()

def event_client(conn):
    client = mqtt.Client(userdata=RecordParts(conn))
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("mqtt.ti", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()


def create_db(db_filename: str):
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute("""CREATE TABLE power (
    ts bigint,
    wh float,
    pulse int,
    status_uptime int);""")
    conn.commit()
    conn.close()


def main(argv: dict):
    db_filename = 'power.sqlite'
    if not os.path.exists(db_filename):
        create_db(db_filename)
    event_client(sqlite3.connect(db_filename))

if __name__ == "__main__":
    main(sys.argv)
