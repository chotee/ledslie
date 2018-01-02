from datetime import datetime

import pytest

from ledslie.content.astral import AstralContent
from ledslie.tests.fakes import FakeMqttProtocol


class TestAstralContent(object):
    @pytest.fixture
    def astral(self) -> AstralContent:
        endpoint = None
        factory = None
        astral = AstralContent(endpoint, factory)
        astral.connectToBroker(FakeMqttProtocol())
        return astral

    def test_publish_astral(self, astral: AstralContent):
        # moon message
        astral.publish_astral(datetime(2018, 1, 8, 12, 0, 0))
        assert 1 == len(astral.protocol._published_messages)
        astral.protocol._published_messages = []

        # Solar message
        astral.publish_astral(datetime(2018, 1, 1, 12, 30, 0))
        assert 1 == len(astral.protocol._published_messages)
        astral.protocol._published_messages = []

        # Moon and Solar message
        astral.publish_astral(datetime(2018, 1, 8, 12, 30, 0))
        assert 2 == len(astral.protocol._published_messages)
        astral.protocol._published_messages = []

        # No astral message.
        res = astral.publish_astral(datetime(2018, 1, 1, 15, 30, 0))
        assert res is None

    def test_moon_message(self, astral: AstralContent):
        assert None == astral.moon_message(datetime(2018, 1, 1, 12, 0, 0))
        assert "Full moon" == astral.moon_message(datetime(2018, 1, 8, 12, 0, 0))
        assert "New moon" == astral.moon_message(datetime(2018, 1, 17, 12, 0, 0))

    def test_sun_message(self, astral: AstralContent):
        assert None == astral.sun_message(astral._now(datetime(2018, 1, 1, 8, 15, 0)))
        assert "Sunrise in 20m" == astral.sun_message(astral._now(datetime(2018, 1, 1, 8, 30, 0)))
        assert "Sunrise in 5m" == astral.sun_message(astral._now(datetime(2018, 1, 1, 8, 45, 0)))
        assert "Sunrise now" == astral.sun_message(astral._now(datetime(2018, 1, 1, 8, 50, 0)))
        assert None == astral.sun_message(astral._now(datetime(2018, 1, 1, 8, 52, 0)))

        assert None == astral.sun_message(astral._now(datetime(2018, 1, 1, 12, 5, 0)))
        assert "Solar noon in 28m" == astral.sun_message(astral._now(datetime(2018, 1, 1, 12, 15, 0)))
        assert "Solar noon in 13m" == astral.sun_message(astral._now(datetime(2018, 1, 1, 12, 30, 0)))
        assert "Solar noon now" == astral.sun_message(astral._now(datetime(2018, 1, 1, 12, 43, 0)))
        assert None == astral.sun_message(astral._now(datetime(2018, 1, 1, 12, 45, 0)))

        assert None == astral.sun_message(astral._now(datetime(2018, 1, 1, 16, 5, 0)))
        assert "Sunset in 22m" == astral.sun_message(astral._now(datetime(2018, 1, 1, 16, 15, 0)))
        assert "Sunset in 7m" == astral.sun_message(astral._now(datetime(2018, 1, 1, 16, 30, 0)))
        assert "Sunset now" == astral.sun_message(astral._now(datetime(2018, 1, 1, 16, 37, 0)))
        assert None == astral.sun_message(astral._now(datetime(2018, 1, 1, 16, 39, 0)))

