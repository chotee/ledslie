import pytest

from ledslie.defaults import DISPLAY_WIDTH, DISPLAY_HEIGHT, FONT_DIRECTORY
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT
import ledslie.processors.typesetter
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
