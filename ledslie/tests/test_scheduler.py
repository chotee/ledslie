import msgpack
import pytest

import ledslie.processors.scheduler
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_UNNAMED, LEDSLIE_TOPIC_SEQUENCES_PROGRAMS
from ledslie.messages import ImageSequence
from ledslie.processors.scheduler import Scheduler
from ledslie.tests.fakes import FakeMqttProtocol, FakeLogger
from ledslie.processors.scheduler import Catalog


class TestCatalog(object):
    def test_init(self):
        catalog = Catalog()
        assert catalog.is_empty()
        assert not catalog.has_content()

        seq = ImageSequence()
        program_id = "First"
        seq.program = program_id
        seq.sequence = ["Foo"]
        catalog.add_program(program_id, seq)

        assert not catalog.is_empty()
        assert catalog.has_content()

        seq = ImageSequence()
        program_id = "Second"
        seq.program = program_id
        seq.sequence = ["Bar", "Quux"]
        catalog.add_program(program_id, seq)

        return catalog

    def test_get_frames(self):
        catalog = self.test_init()
        assert "Foo" == catalog.next_frame()
        assert "Bar" == catalog.next_frame()
        assert "Quux" == catalog.next_frame()
        assert "Foo" == catalog.next_frame()

    def test_empty_catalog(self):
        catalog = Catalog()
        try:
            catalog.next_frame()
        except IndexError:
            pass
        else:
            assert "Should not get here!"



class TestScheduler(object):

    @pytest.fixture
    def sched(self):
        endpoint = None
        factory = None
        s = Scheduler(endpoint, factory)
        s.protocol = FakeMqttProtocol()
        return s

    def test_on_connect(self, sched):
        ledslie.processors.scheduler.log = FakeLogger()
        protocol = FakeMqttProtocol()
        sched.connectToBroker(protocol)

    def test_on_message(self, sched):
        topic = LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + "test"
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
        sched.catalog.add_program(None, ImageSequence().load(self._test_sequence(sched)))
        assert 0 == len(sched.protocol._published_messages)

        sched.send_next_frame()  # Frame 0
        assert 1 == len(sched.protocol._published_messages)
        assert ('ledslie/frames/1', b'0' * image_size) == sched.protocol._published_messages[-1]

        sched.send_next_frame()  # Frame 1
        assert 2 == len(sched.protocol._published_messages)
        assert ('ledslie/frames/1', b'1' * image_size) == sched.protocol._published_messages[-1]
        #
        sched.send_next_frame()  # Frame 2
        assert 3 == len(sched.protocol._published_messages)
        assert ('ledslie/frames/1', b'2' * image_size) == sched.protocol._published_messages[-1]
        #
        sched.send_next_frame()  # End of program!
        # assert 3 == len(sched.protocol._published_messages)
        # sched.send_next_frame()  # End of program!  # this should not happen.
        # assert 3 == len(sched.protocol._published_messages)

    def test_sequence_wrong(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        topic = LEDSLIE_TOPIC_SEQUENCES_UNNAMED + "/test"
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
