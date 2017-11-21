import pytest
import msgpack
from flask.config import Config

from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_UNNAMED, LEDSLIE_TOPIC_SEQUENCES_PROGRAMS
import ledslie.processors.scheduler
from ledslie.processors.scheduler import Scheduler
from ledslie.processors.messages import ImageSequence
from ledslie.tests.fakes import FakeMqttProtocol, FakeLogger


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
        ledslie.processors.scheduler.log = FakeLogger()
        protocol = FakeMqttProtocol()
        sched.connectToBroker(protocol)

    def test_on_message(self, sched):
        topic = LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + b"test"
        payload = self._test_sequence(sched)
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert not sched.catalog.is_empty()

    def _test_sequence(self, sched):
        sequence_info = {}
        image_size = sched.config.get('DISPLAY_SIZE')
        image_sequence = [
            ['0' * image_size, {'duration': 100}],
            ['1' * image_size, {'duration': 100}],
            ['2' * image_size, {'duration': 100}],
        ]
        payload = msgpack.packb([image_sequence, sequence_info])
        return payload

    def test_send_next_frame(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        sched.catalog.add_sequence(None, ImageSequence(self.config).load(self._test_sequence(sched)))
        assert 0 == len(sched.protocol._published_messages)

        sched.send_next_frame()  # Frame 0
        assert 1 == len(sched.protocol._published_messages)
        assert (b'ledslie/frames/1', b'0' * image_size) == sched.protocol._published_messages[-1]

        sched.send_next_frame()  # Frame 1
        assert 2 == len(sched.protocol._published_messages)
        assert (b'ledslie/frames/1', b'1' * image_size) == sched.protocol._published_messages[-1]

        sched.send_next_frame()  # Frame 2
        assert 3 == len(sched.protocol._published_messages)
        assert (b'ledslie/frames/1', b'2' * image_size) == sched.protocol._published_messages[-1]

        sched.send_next_frame()  # End of program!
        assert 3 == len(sched.protocol._published_messages)
        sched.send_next_frame()  # End of program!  # this should not happen.
        assert 3 == len(sched.protocol._published_messages)

    def test_sequence_wrong(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        topic = LEDSLIE_TOPIC_SEQUENCES_UNNAMED + b"/test"
        sequence = [
            ['666', {'duration': 100}],  # Wrong number of bytes in the image
        ]
        payload = msgpack.packb([sequence, {}])
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.is_empty()

        sequence = [
            ['0'*image_size, {}],  # No duration information, will default to the standard one.
        ]
        payload = msgpack.packb([sequence, {}])
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.has_content()
