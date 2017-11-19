import pytest

from ledslie.defaults import DISPLAY_WIDTH, DISPLAY_HEIGHT, FONT_DIRECTORY
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT, LEDSLIE_TOPIC_TYPESETTER
import ledslie.processors.typesetter
from ledslie.processors.messages import TextSingleLineLayout, TextTrippleLinesLayout
from ledslie.processors.typesetter import Typesetter
from ledslie.processors.service import Config
from ledslie.tests.fakes import FakeMqttProtocol, FakeLogger


class TestTypesetter(object):

    @pytest.fixture
    def tsetter(self):
        self.config = Config('.')
        self.config.from_object('ledslie.defaults')
        endpoint = None
        factory = None
        s = Typesetter(endpoint, factory, self.config)
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

    def test_ledslie_typesetter_1line(self, tsetter):
        topic = LEDSLIE_TOPIC_TYPESETTER
        msg = TextSingleLineLayout()
        msg.text = 'Foo bar quux.'
        assert 0 == len(tsetter.protocol._published_messages)
        tsetter.onPublish(topic, bytes(msg), qos=0, dup=False, retain=False, msgId=0)
        assert 1 == len(tsetter.protocol._published_messages)

    def test_ledslie_typesetter_3lines(self, tsetter):
        topic = LEDSLIE_TOPIC_TYPESETTER
        msg = TextTrippleLinesLayout()
        msg.lines = ["One", "Two", "Three"]
        assert 0 == len(tsetter.protocol._published_messages)
        tsetter.onPublish(topic, bytes(msg), qos=0, dup=False, retain=False, msgId=0)
        assert 1 == len(tsetter.protocol._published_messages)
