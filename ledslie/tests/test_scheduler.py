import pytest
import msgpack
from flask.config import Config
from paho.mqtt.client import MQTTMessage
from twisted.internet.defer import Deferred, succeed
from twisted.internet.test.test_tcp import FakeProtocol

from ledslie.definitions import LEDSLIE_TOPIC_SERIALIZER, LEDSLIE_TOPIC_SEQUENCES
import ledslie.processors.scheduler
from ledslie.processors.scheduler import Scheduler
from ledslie.processors.messages import ImageSequence


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
    def __init__(self):
        self._published_messages = []

    def setWindowSize(self, size):
        pass

    def connect(self, name, keepalive=None):
        pass

    def subscribe(self, topic, qos=0):
        return succeed("subscribed to %s" % topic)

    def publish(self, topic, message):
        self._published_messages.append((topic, message))
        return succeed(None)


class FakeLogger(object):
    def error(self, msg, **kwargs):
        pass
        #raise RuntimeError(msg.format(**kwargs))

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
        topic = LEDSLIE_TOPIC_SEQUENCES + "/test"
        payload = self._test_sequence(sched)
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert not sched.catalog.is_empty()

    def _test_sequence(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        sequence = [
            ['0' * image_size, {'duration': 100}],
            ['1' * image_size, {'duration': 100}],
            ['2' * image_size, {'duration': 100}],
        ]
        payload = msgpack.packb(sequence)
        return payload

    def test_send_next_frame(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        sched.catalog.add_sequence(None, ImageSequence(self.config).load(self._test_sequence(sched)))
        assert 0 == len(sched.protocol._published_messages)

        sched.send_next_frame()  # Frame 0
        assert 1 == len(sched.protocol._published_messages)
        assert ('ledslie/frames/1', b'0' * image_size) == sched.protocol._published_messages[-1]

        sched.send_next_frame()  # Frame 1
        assert 2 == len(sched.protocol._published_messages)
        assert ('ledslie/frames/1', b'1' * image_size) == sched.protocol._published_messages[-1]

        sched.send_next_frame()  # Frame 2
        assert 3 == len(sched.protocol._published_messages)
        assert ('ledslie/frames/1', b'2' * image_size) == sched.protocol._published_messages[-1]

        sched.send_next_frame()  # End of program!
        assert 3 == len(sched.protocol._published_messages)
        sched.send_next_frame()  # End of program!  # this should not happen.
        assert 3 == len(sched.protocol._published_messages)

    def test_sequence_wrong(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        topic = LEDSLIE_TOPIC_SEQUENCES + "/test"
        sequence = [
            ['666', {'duration': 100}],  # Wrong number of bytes in the image
        ]
        payload = msgpack.packb(sequence)
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.is_empty()

        sequence = [
            ['0'*image_size, {}],  # No duration information, will default to the standard one.
        ]
        payload = msgpack.packb(sequence)
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.has_content()
