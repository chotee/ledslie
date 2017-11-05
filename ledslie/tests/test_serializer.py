import msgpack
import pytest
from paho.mqtt.client import MQTTMessage

from ledslie.processors.sequencer import Sequencer

class FakeClient(object):
    def __init__(self):
        self.pubs = []

    def connect(self, host, port, keepalive):
        pass

    def subscribe(self, topic):
        pass

    def publish(self, topic, data):
        self.pubs.append([topic, data])

    def loop_forever(self):
        pass


class TestSequencer(object):

    @pytest.fixture
    def client(self):
        return FakeClient()

    @pytest.fixture
    def seq(self, client):
        seq = Sequencer()
        seq.run(client)
        return seq

    def test_run(self, seq):
        pass

    def test_on_connect(self, seq, client):
        userdata = None
        flags = None
        rc = None
        seq.on_connect(client, userdata, flags, rc)

    def test_on_message(self, seq, client):
        userdata = None
        mqtt_msg = MQTTMessage()
        seq_id = 666
        sequence = []
        mqtt_msg.payload = msgpack.packb([seq_id, sequence])
        seq.on_message(client, userdata, mqtt_msg)
