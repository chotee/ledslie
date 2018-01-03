from datetime import datetime

import pytest

from ledslie.content.astralinfo import AstralContent
from ledslie.tests.fakes import FakeMqttProtocol


class TestAstralContent(object):
    @pytest.fixture
    def astralinfo(self) -> AstralContent:
        endpoint = None
        factory = None
        astral = AstralContent(endpoint, factory)
        astral.connectToBroker(FakeMqttProtocol())
        return astral

    def test_publish_astral(self, astralinfo: AstralContent):
        # moon message
        astralinfo.publish_astral(datetime(2018, 1, 8, 12, 0, 0))
        assert 1 == len(astralinfo.protocol._published_messages)
        astralinfo.protocol._published_messages = []

        # Solar message
        astralinfo.publish_astral(datetime(2018, 1, 1, 12, 30, 0))
        assert 1 == len(astralinfo.protocol._published_messages)
        astralinfo.protocol._published_messages = []

        # Moon and Solar message
        astralinfo.publish_astral(datetime(2018, 1, 8, 12, 30, 0))
        assert 2 == len(astralinfo.protocol._published_messages)
        astralinfo.protocol._published_messages = []

        # No astral message.
        res = astralinfo.publish_astral(datetime(2018, 1, 1, 15, 30, 0))
        assert res is None

    def test_moon_message(self, astralinfo: AstralContent):
        assert None == astralinfo.moon_message(datetime(2018, 1, 1, 12, 0, 0))
        assert "Full moon" == astralinfo.moon_message(datetime(2018, 1, 8, 12, 0, 0))
        assert "New moon" == astralinfo.moon_message(datetime(2018, 1, 17, 12, 0, 0))

    def test_sun_message(self, astralinfo: AstralContent):
        assert None == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 8, 15, 0)))
        assert "Sunrise in 20m" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 8, 30, 0)))
        assert "Sunrise in 5m" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 8, 45, 0)))
        assert "Sunrise now" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 8, 50, 0)))
        assert None == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 8, 52, 0)))

        assert None == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 12, 5, 0)))
        assert "Solar noon in 28m" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 12, 15, 0)))
        assert "Solar noon in 13m" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 12, 30, 0)))
        assert "Solar noon now" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 12, 43, 0)))
        assert None == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 12, 45, 0)))

        assert None == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 16, 5, 0)))
        assert "Sunset in 22m" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 16, 15, 0)))
        assert "Sunset in 7m" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 16, 30, 0)))
        assert "Sunset now" == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 16, 37, 0)))
        assert None == astralinfo.sun_message(astralinfo._now(datetime(2018, 1, 1, 16, 39, 0)))

