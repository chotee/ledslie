import pytest

from ledslie.defaults import DISPLAY_WIDTH, DISPLAY_HEIGHT, FONT_DIRECTORY
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT
from ledslie.processors.typesetter import on_message, config
from ledslie.tests.fakes import FakeMQTTMessage


class TestTypesetter(object):
    def test_on_message(self, client):
        userdata = None
        mqtt_msg = FakeMQTTMessage(topic=LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT, payload="Some text")
        config.from_object('ledslie.defaults')
        on_message(client, userdata, mqtt_msg)
