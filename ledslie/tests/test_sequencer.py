import pytest
import msgpack
from flask.config import Config
from paho.mqtt.client import MQTTMessage

from ledslie.processors.sequencer import Sequencer

class FakeClient(object):
    def __init__(self):
        self.pubed_messages = []

    def connect(self, host, port, keepalive):
        pass

    def subscribe(self, topic):
        pass

    def publish(self, topic, data):
        self.pubed_messages.append([topic, data])

    def loop_forever(self):
        pass

    def assert_message_pubed(self, topic):
        return [msg for msg in self.pubed_messages if msg[0].startswith(topic)]


class FakeTimer(object):
    def __init__(self, delay, func, *args, **kwargs):
        pass

    def start(self):
        pass


class TestSequencer(object):

    @pytest.fixture
    def client(self):
        return FakeClient()

    @pytest.fixture
    def seq(self, client):
        self.config = Config('.')
        self.config.from_object('ledslie.defaults')
        seq = Sequencer(self.config)
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
        assert len(client.assert_message_pubed('ledslie/frames/1')) == 0

    def test_sequence(self, monkeypatch, seq, client):
        monkeypatch.setattr("ledslie.processors.sequencer.Timer", FakeTimer)
        image_size = seq.config.get('DISPLAY_WIDTH') * seq.config.get('DISPLAY_HEIGHT')
        userdata = None
        mqtt_msg = MQTTMessage()
        seq_id = 666
        sequence = [
            ['0'*image_size, {'duration': 100}],
            ['1'*image_size, {'duration': 100}],
            ['2'*image_size, {'duration': 100}],
        ]
        mqtt_msg.payload = msgpack.packb([seq_id, sequence])
        seq.on_message(client, userdata, mqtt_msg)
        seq.schedule_image(client)
        seq.schedule_image(client)
        assert len(client.assert_message_pubed('ledslie/frames/1')) == 3
        assert client.assert_message_pubed('ledslie/frames/1') == [
            ['ledslie/frames/1', b'0'*image_size],
            ['ledslie/frames/1', b'1'*image_size],
            ['ledslie/frames/1', b'2'*image_size],
        ]

    def test_sequence_wrong(self, monkeypatch, seq, client):
        monkeypatch.setattr("ledslie.processors.sequencer.Timer", FakeTimer)
        image_size = seq.config.get('DISPLAY_WIDTH') * seq.config.get('DISPLAY_HEIGHT')
        sequence = [
            ['666', {'duration': 100}],  # Wrong number of bytes in the image
        ]
        userdata = None
        mqtt_msg = MQTTMessage()
        seq_id = 666
        mqtt_msg.payload = msgpack.packb([seq_id, sequence])
        seq.on_message(client, userdata, mqtt_msg)
        assert len(client.assert_message_pubed('ledslie/frames/1')) == 0

        sequence = [
            ['0'*image_size, {}],  # No duration information
        ]
        mqtt_msg.payload = msgpack.packb([seq_id, sequence])
        seq.on_message(client, userdata, mqtt_msg)
        assert len(client.assert_message_pubed('ledslie/frames/1')) == 0
        assert len(seq.queue) == 0

