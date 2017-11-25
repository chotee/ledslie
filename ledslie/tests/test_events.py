from datetime import date, timedelta

from ledslie.content.events import create_date_string, EventsContent


def test_create_date_string():
    now = date(2017, 11, 25)
    assert "Today" == create_date_string(now, now)

    tomorrow = now + timedelta(days=1)
    assert "Tomorrow" == create_date_string(tomorrow, now)

    some_date = now + timedelta(days=2)
    assert "Monday" == create_date_string(some_date, now)

    some_date = now + timedelta(days=5)
    assert "Thursday" == create_date_string(some_date, now)

    some_date = now + timedelta(days=6)
    assert "Fri 01" == create_date_string(some_date, now)

    some_date = now + timedelta(days=7)
    assert "Sat 02" == create_date_string(some_date, now)

    some_date = now + timedelta(days=8)
    assert "Sun 03" == create_date_string(some_date, now)


class TestEventsContent(object):
    def test_create_event_info(self):
        endpoint = None
        factory = None
        events = EventsContent(endpoint, factory)
        data = [
            ['ctf', date(2017, 11, 26)],  # Tomorrow
            ['social', date(2017, 11, 29)],  # Wednesday
            ['boardgames', date(2017, 12, 2)],  # Sat 02
            ['something else', date(2017, 12, 5)],  # Tue 05 # Not to be added.
        ]
        result = [
            'Tomorrow: ctf',
            'Wednesday: social',
            'Sat 02: boardgames',
        ]
        assert result == events.create_event_info(data, now=date(2017, 11, 25))
