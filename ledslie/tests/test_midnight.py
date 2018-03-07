import pytest

from ledslie.content.midnight import create_midnight_groups, all_gmts, MidnightContent
from ledslie.tests.fakes import FakeMqttProtocol


def test_all_gmts():
    assert all_gmts()[0.0] == 'GMT-1'


def test_create_midnight_groups():
    assert create_midnight_groups()


class TestMidnightContent:
    @pytest.fixture
    def midnightContent(self) -> MidnightContent:
        endpoint = None
        factory = None
        midnight = MidnightContent(endpoint, factory)
        midnight.connectToBroker(FakeMqttProtocol())
        return midnight

    def test_midnight_message(self, midnightContent):
        assert "GMT-1" == midnightContent.midnight_message(0.0).lines[2]

    def test_publishMidnight(self, midnightContent):
        assert midnightContent.publishMidnight(0.0)

