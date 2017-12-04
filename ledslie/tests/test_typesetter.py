import pytest

import ledslie.processors.typesetter
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT, LEDSLIE_TOPIC_TYPESETTER_1LINE, \
    LEDSLIE_TOPIC_TYPESETTER_3LINES, LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, LEDSLIE_TOPIC_SEQUENCES_UNNAMED
from ledslie.messages import TextSingleLineLayout, TextTripleLinesLayout, FrameSequence
from ledslie.processors.service import Config
from ledslie.processors.typesetter import Typesetter
from ledslie.tests.fakes import FakeMqttProtocol, FakeLogger


class TestTypesetter(object):

    @pytest.fixture
    def tsetter(self):
        endpoint = None
        factory = None
        s = Typesetter(endpoint, factory)
        s.protocol = FakeMqttProtocol()
        return s

    def test_on_connect(self, tsetter):
        ledslie.processors.typesetter.log = FakeLogger()
        protocol = FakeMqttProtocol()
        tsetter.connectToBroker(protocol)

    def test_typeset_simple_text(self, tsetter):
        topic = LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT
        payload = "Hello world!"
        assert 0 == len(tsetter.protocol._published_messages)
        tsetter.onPublish(topic, payload, qos=0, dup=False, retain=False, msgId=0)
        assert 1 == len(tsetter.protocol._published_messages)
        seq_topic, seq_data = tsetter.protocol._published_messages[-1]
        assert seq_topic == LEDSLIE_TOPIC_SEQUENCES_UNNAMED

    def test_ledslie_typesetter_1line(self, tsetter):
        topic = LEDSLIE_TOPIC_TYPESETTER_1LINE
        msg = TextSingleLineLayout()
        msg.text = 'Foo bar quux.'
        assert 0 == len(tsetter.protocol._published_messages)
        tsetter.onPublish(topic, msg.serialize(), qos=0, dup=False, retain=False, msgId=0)
        assert 1 == len(tsetter.protocol._published_messages)
        seq_topic, seq_data = tsetter.protocol._published_messages[-1]
        assert seq_topic == LEDSLIE_TOPIC_SEQUENCES_UNNAMED

    def test_ledslie_typesetter_3lines(self, tsetter):
        topic = LEDSLIE_TOPIC_TYPESETTER_3LINES
        msg = TextTripleLinesLayout()
        msg.lines = ["Ledslie \u00a9 GNU-AGPL3 ~ ;-)",
                     "https://wiki.techinc.nl/index.php/Ledslie",
                     "https://github.com/techinc/ledslie"]
        assert 0 == len(tsetter.protocol._published_messages)
        tsetter.onPublish(topic, msg.serialize(), qos=0, dup=False, retain=False, msgId=0)
        assert 1 == len(tsetter.protocol._published_messages)
        seq_topic, seq_data = tsetter.protocol._published_messages[-1]
        assert seq_topic == LEDSLIE_TOPIC_SEQUENCES_UNNAMED
        assert len(seq_data) > Config()['DISPLAY_SIZE']

    def test_ledslie_typesetter_fields(self, tsetter):
        topic = LEDSLIE_TOPIC_TYPESETTER_1LINE
        msg = TextSingleLineLayout()
        msg.text = 'Foo bar quux.'
        msg.duration = 1000
        msg.program = 'foobar'
        assert 0 == len(tsetter.protocol._published_messages)
        tsetter.onPublish(topic, msg.serialize(), qos=0, dup=False, retain=False, msgId=0)
        assert 1 == len(tsetter.protocol._published_messages)

        seq_topic, seq_data = tsetter.protocol._published_messages[-1]
        assert (LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + "foobar") == seq_topic
        seq = FrameSequence().load(seq_data)
        assert 1000 == seq.duration

    def test_font_size(self, monkeypatch, tsetter):
        msg = TextSingleLineLayout()
        msg.font_size = 13
        msg.text = "lala"
        def typetype(font_path, font_size):
            assert font_size == 13
        monkeypatch.setattr("PIL.ImageFont.truetype", typetype)
        tsetter.typeset_1line(msg)
