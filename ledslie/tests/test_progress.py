from datetime import datetime

import pytest

from ledslie.content.progress import Progress
from ledslie.tests.fakes import FakeMqttProtocol


class TestProgress(object):
    @pytest.fixture
    def progress(self):
        endpoint = None
        factory = None
        progress = Progress(endpoint, factory)
        progress.connectToBroker(FakeMqttProtocol())
        return progress

    def test_create_day_progress(self, progress):
        assert "00:00         0.0%" == progress._create_day_progress(datetime(2017, 12, 31,  0,  0, 0))[0]
        assert "12:00        50.0%" == progress._create_day_progress(datetime(2017, 12, 31, 12,  0, 0))[0]
        assert "23:59        99.9%" == progress._create_day_progress(datetime(2017, 12, 31, 23, 59, 0))[0]

    def test_create_month_progress(self, progress):
        assert "January 05   14.5%" == progress._create_month_progress(datetime(2018,  1,   5,  12,  0, 0))[0]
        assert "January 31   99.7%" == progress._create_month_progress(datetime(2018,  1,  31,  22,  0, 0))[0]
        assert "February 01   0.0%" == progress._create_month_progress(datetime(2018,  2,   1,   0,  0, 0))[0]
        assert "November 30  98.3%" == progress._create_month_progress(datetime(2018, 11, 30,  12,  0, 0))[0]

    def test_create_year_progress(self, progress):
        assert "Day 1         0.0%" == progress._create_year_progress(datetime(2018,  1,  1,   0,   0,  0))[0]
        assert "Day 166      45.2%" == progress._create_year_progress(datetime(2018,  6, 15,   0,   0,  0))[0]
        assert "Day 365     100.0%" == progress._create_year_progress(datetime(2018, 12, 31,  23,  59, 59))[0]
