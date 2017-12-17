import pytest
from datetime import datetime, timedelta

from ledslie.content.ovinfo import OVInfoContent, Transports
from ledslie.tests.fakes import FakeMqttProtocol


class TestTransports(object):

    def test_add_and_overview(self):
        now = datetime(2017, 12, 15, 12, 30, 0)
        tports = Transports()
        assert [] == tports.pass_overview(now=now)

        five_mins = datetime(2017, 12, 15, 12, 35, 0)
        tports.add_pass("13", "CS", 1, five_mins)  # Add a pass information. Will pass in 5 mins.
        assert [['13', 'CS', [datetime(2017, 12, 15, 12, 35, 0)]]] == tports.pass_overview(now=now)
        ten_mins = datetime(2017, 12, 15, 12, 40, 0)
        fifteen_mins = datetime(2017, 12, 15, 12, 45, 0)
        tports.add_pass("13", "CS", 2, ten_mins)  # Add other pass information on the same route .
        assert [['13', 'CS', [datetime(2017, 12, 15, 12, 35, 0),
                              datetime(2017, 12, 15, 12, 40, 0)]]] == tports.pass_overview(now=now)
        tports.add_pass("17", "W/E", 2, fifteen_mins)
        assert [
                   ['13', 'CS', [datetime(2017, 12, 15, 12, 35, 0), datetime(2017, 12, 15, 12, 40, 0)]],
                   ['17', 'W/E', [datetime(2017, 12, 15, 12, 45, 0)]]
               ] == tports.pass_overview(now=now)
        now = datetime(2017, 12, 15, 12, 36, 0)  # moving time forward 6 minutes. We should no longer see the first.
        assert [
                   ['13', 'CS', [datetime(2017, 12, 15, 12, 40, 0)]],
                   ['17', 'W/E', [datetime(2017, 12, 15, 12, 45, 0)]]
               ] == tports.pass_overview(now=now)

        # Adding a earlier passing transport after a later one. Passing order should always be nearest first.
        tports.add_pass("17", "W/E", 3, ten_mins)
        assert [
                   ['13', 'CS', [datetime(2017, 12, 15, 12, 40, 0)]],
                   ['17', 'W/E', [datetime(2017, 12, 15, 12, 40, 0), datetime(2017, 12, 15, 12, 45, 0)]]
               ] == tports.pass_overview(now=now)

        # Lines with no pending passes should not be reported at all
        now = datetime(2017, 12, 15, 12, 41, 0)  # moving time forward 6 minutes. We should no longer see the first.
        assert [
                   ['17', 'W/E', [datetime(2017, 12, 15, 12, 45, 0)]]
               ] == tports.pass_overview(now=now)

        # Updates in the journey information should update the estimate.
        tports.add_pass("17", "W/E", 2, datetime(2017, 12, 15, 12, 48, 0))
        assert [
                   ['17', 'W/E', [datetime(2017, 12, 15, 12, 48, 0)]]
               ] == tports.pass_overview(now=now)


class TestOVInfo(object):
    @pytest.fixture
    def ovinfo(self) -> OVInfoContent:
        endpoint = None
        factory = None
        ovinfo = OVInfoContent(endpoint, factory)
        ovinfo.connectToBroker(FakeMqttProtocol())
        return ovinfo

    # def test_publish_ov_info(self, ovinfo: OVInfoContent):
    #     assert "foo" == ovinfo.publish_ov_info()

    def test_create_ov_display(self, ovinfo: OVInfoContent):
        assert [] == ovinfo.create_ov_display()
        ovinfo.lines.add_pass("2", "CS", 1, datetime.now() + timedelta(minutes=10))
        ovinfo.lines.add_pass("2", "CS", 2, datetime.now() + timedelta(minutes=25))
        assert ["2→CS|10m 25m"] == ovinfo.create_ov_display()
        ovinfo.lines.add_pass("62", "SLL", 1, datetime.now() + timedelta(minutes=18))
        assert ["2→CS|10m 25m", "62→Lely|18m"] == ovinfo.create_ov_display()
        ovinfo.lines.add_pass("62", "AMS", 1, datetime.now() + timedelta(minutes=23))
        assert ["2→CS|10m 25m", "62→Amtl|23m", "62→Lely|18m"] == ovinfo.create_ov_display()


    def test_time_formatter(self, ovinfo: OVInfoContent):
        now = datetime(2017, 12, 15, 12, 30, 0)
        five_mins = datetime(2017, 12, 15, 12, 35, 0)
        assert '5m' == ovinfo.time_formatter(five_mins, now)

        fifteen_mins = datetime(2017, 12, 15, 12, 45, 0)
        assert '15m' == ovinfo.time_formatter(fifteen_mins, now)

        # After 30 mins or greater, it switches to showing the hour minutes
        thirty_mins = datetime(2017, 12, 15, 13, 0, 0)
        assert ':00' == ovinfo.time_formatter(thirty_mins, now)

        forty_mins = datetime(2017, 12, 15, 13, 10, 0)
        assert ':10' == ovinfo.time_formatter(forty_mins, now)

        # Longer then an hour, it will switch to the full time.
        hour = datetime(2017, 12, 15, 13, 30, 0)
        assert '13:30' == ovinfo.time_formatter(hour, now)

        hour_and_quarter = datetime(2017, 12, 15, 13, 45, 0)
        assert '13:45' == ovinfo.time_formatter(hour_and_quarter, now)

        after_the_hour = datetime(2017, 12, 15, 14, 5, 0)
        assert '14:05' == ovinfo.time_formatter(after_the_hour, now)
