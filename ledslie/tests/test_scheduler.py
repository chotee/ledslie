import pytest

import json

import ledslie.processors.scheduler
from ledslie.config import Config
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_UNNAMED, LEDSLIE_TOPIC_SEQUENCES_PROGRAMS
from ledslie.messages import FrameSequence, SerializeFrame, Frame
from ledslie.processors.scheduler import Scheduler
from ledslie.tests.fakes import FakeMqttProtocol, FakeLogger, FakeLEDScreen
from ledslie.processors.animate import AnimateStill


class TestScheduler(object):
    @pytest.fixture
    def sched(self):
        endpoint = None
        factory = None
        s = Scheduler(endpoint, factory)
        s.led_screen = FakeLEDScreen()
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

    def test_remove_program(self, sched):
        topic = LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + "test"
        self.test_on_message(sched)
        assert not sched.catalog.is_empty()
        sched.onPublish(topic, b"", qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.is_empty()

        # Removing a non-existent program should not be a problem.
        sched.onPublish(topic, b"", qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.is_empty()

    def _test_sequence(self, sched: Scheduler):
        sequence_info = {}
        image_size = sched.config.get('DISPLAY_SIZE')
        image_sequence = [
            [SerializeFrame(bytearray(b'0' * image_size)), {'duration': 100}],
            [SerializeFrame(bytearray(b'1' * image_size)), {'duration': 100}],
            [SerializeFrame(bytearray(b'2' * image_size)), {'duration': 100}],
        ]
        payload = json.dumps([image_sequence, sequence_info])
        return payload.encode()

    def test_send_next_frame(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        sched.catalog.add_program(None, FrameSequence().load(self._test_sequence(sched)))
        assert 0 == len(sched.led_screen._published_frames)

        sched.send_next_frame()  # Frame 0
        assert 1 == len(sched.led_screen._published_frames)
        assert bytearray(b'0000') == sched.led_screen._published_frames[-1].img_data[0:4]

        sched.send_next_frame()  # Frame 1
        assert 2 == len(sched.led_screen._published_frames)
        assert bytearray(b'1111') == sched.led_screen._published_frames[-1].img_data[0:4]

        sched.send_next_frame()  # Frame 2
        assert 3 == len(sched.led_screen._published_frames)
        assert bytearray(b'2222') == sched.led_screen._published_frames[-1].img_data[0:4]
        #
        sched.send_next_frame()  # End of program!

    def test_sequence_wrong(self, sched):
        image_size = sched.config.get('DISPLAY_SIZE')
        topic = LEDSLIE_TOPIC_SEQUENCES_UNNAMED + "/test"
        sequence = [
            ['666', {'duration': 100}],  # Wrong number of bytes in the image
        ]
        payload = json.dumps([sequence, {}]).encode()
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.is_empty()

        sequence = [
            [SerializeFrame(b'0'*image_size), {}],  # No duration information, will default to the standard one.
        ]
        payload = json.dumps([sequence, {}]).encode()
        assert sched.catalog.is_empty()
        sched.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert sched.catalog.has_content()

    def test_AnimateStill(self, sched):
        seq = FrameSequence()
        img_data = bytearray(Config().get('DISPLAY_SIZE'))
        seq.add_frame(Frame(img_data, 2000))
        animated_seq = AnimateStill(seq[0])
        assert Config().get('DISPLAY_HEIGHT') == len(animated_seq)
        assert sum([frame.duration for frame in animated_seq.frames]) == 2000

        seq.add_frame(Frame(img_data, None))
        animated_seq = AnimateStill(seq[1])
        assert Config()['DISPLAY_DEFAULT_DELAY'] == sum([frame.duration for frame in animated_seq.frames])
