import pytest
import msgpack
from flask.config import Config
from paho.mqtt.client import MQTTMessage
from twisted.internet.defer import Deferred, succeed
from twisted.internet.test.test_tcp import FakeProtocol

from ledslie.definitions import LEDSLIE_TOPIC_SERIALIZER, LEDSLIE_TOPIC_SEQUENCES
import ledslie.processors.scheduler
from ledslie.processors.scheduler import Scheduler, ImageSequence

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



class FakeMqttProtocol(FakeProtocol):
    def setWindowSize(self, size):
        pass

    def connect(self, name, keepalive=None):
        pass

    def subscribe(self, topic, qos=0):
        return succeed("subscribed to %s" % topic)

    def publish(self, topic, message):
        return succeed(None)


class FakeLogger(object):
    def error(self, msg, **kwargs):
        raise RuntimeError(msg.format(**kwargs))

    def info(self, msg, **kwargs):
        pass

    def debug(self, msg, **kwargs):
        pass


class TestScheduler(object):

    @pytest.fixture
    def sched(self):
        self.config = Config('.')
        self.config.from_object('ledslie.defaults')
        endpoint = None
        factory = None
        s = Scheduler(endpoint, factory, self.config)
        s.protocol = FakeMqttProtocol()
        return s

    def test_on_connect(self, sched):
        userdata = None
        flags = None
        rc = None
        ledslie.processors.scheduler.log = FakeLogger()
        protocol = FakeMqttProtocol()
        sched.connectToBroker(protocol)

    def test_on_message(self, sched):
        image_size = sched.config.get('DISPLAY_WIDTH') * sched.config.get('DISPLAY_HEIGHT')
        topic = LEDSLIE_TOPIC_SEQUENCES + "/test"
        payload = self._test_sequence(sched)
        qos = 0
        dup = False
        retain = False
        msgId = 0
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos, dup, retain, msgId)
        assert not sched.catalog.is_empty()

    def _test_sequence(self, sched):
        image_size = sched.config.get('DISPLAY_WIDTH') * sched.config.get('DISPLAY_HEIGHT')
        seq_id = 666
        sequence = [
            ['0' * image_size, {'duration': 100}],
            ['1' * image_size, {'duration': 100}],
            ['2' * image_size, {'duration': 100}],
        ]
        payload = msgpack.packb([seq_id, sequence])
        return payload

    def test_send_next_frame(self, sched):
        sched.catalog.add_sequence(None, ImageSequence(self.config).load(self._test_sequence(sched)))
        sched.send_next_frame()

    # def test_sequence(self, monkeypatch, seq, client):
    #     monkeypatch.setattr("ledslie.processors.sequencer.Timer", FakeTimer)
    #     userdata = None
    #     mqtt_msg = MQTTMessage()
    #     seq_id = 666
    #     sequence = [
    #         ['0'*image_size, {'duration': 100}],
    #         ['1'*image_size, {'duration': 100}],
    #         ['2'*image_size, {'duration': 100}],
    #     ]
    #     mqtt_msg.payload = msgpack.packb([seq_id, sequence])
    #     seq.on_message(client, userdata, mqtt_msg)
    #     seq.schedule_image(client)
    #     seq.schedule_image(client)
    #     assert len(client.assert_message_pubed(LEDSLIE_TOPIC_SERIALIZER)) == 3
    #     assert client.assert_message_pubed(LEDSLIE_TOPIC_SERIALIZER) == [
    #         [LEDSLIE_TOPIC_SERIALIZER, b'0'*image_size],
    #         [LEDSLIE_TOPIC_SERIALIZER, b'1'*image_size],
    #         [LEDSLIE_TOPIC_SERIALIZER, b'2'*image_size],
    #     ]
    #
    # def test_sequence_wrong(self, monkeypatch, seq, client):
    #     monkeypatch.setattr("ledslie.processors.sequencer.Timer", FakeTimer)
    #     image_size = seq.config.get('DISPLAY_WIDTH') * seq.config.get('DISPLAY_HEIGHT')
    #     sequence = [
    #         ['666', {'duration': 100}],  # Wrong number of bytes in the image
    #     ]
    #     userdata = None
    #     mqtt_msg = MQTTMessage()
    #     seq_id = 666
    #     mqtt_msg.payload = msgpack.packb([seq_id, sequence])
    #     seq.on_message(client, userdata, mqtt_msg)
    #     assert len(client.assert_message_pubed(LEDSLIE_TOPIC_SERIALIZER)) == 0
    #
    #     sequence = [
    #         ['0'*image_size, {}],  # No duration information
    #     ]
    #     mqtt_msg.payload = msgpack.packb([seq_id, sequence])
    #     seq.on_message(client, userdata, mqtt_msg)
    #     assert len(client.assert_message_pubed(LEDSLIE_TOPIC_SERIALIZER)) == 0
    #     assert len(seq.queue) == 0

