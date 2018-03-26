import pytest
from ledslie.content.utils import CircularBuffer


class TestCircularBuffer(object):
    def test_usage(self):
        cb = CircularBuffer()
        assert 0 == len(cb)
        cb.add("Foo")
        assert 1 == len(cb)
        assert "Foo" == next(cb)
        assert "Foo" == next(cb)
        cb.add("Bar")
        assert 2 == len(cb)
        assert "Bar" == next(cb)
        assert "Foo" == next(cb)
        cb.add("Quux")
        assert "Quux" == next(cb)
        assert "Bar" == next(cb)
        assert "Foo" == next(cb)
        assert "Quux" == next(cb)

    def test_empty(self):
        cb = CircularBuffer()
        try: next(cb)
        except IndexError: pass
        else: pytest.fail("Should have raised IndexError")

    def test_init_load(self):
        cb = CircularBuffer(['One', 'Two', 'Three'])
        assert "One" == next(cb)
        assert "Two" == next(cb)
        assert "Three" == next(cb)
        assert "One" == next(cb)

    def test_remove(self):
        cb = CircularBuffer(['One', 'Two', 'Three', 'Four'])
        assert 4 == len(cb)
        assert "One" == next(cb)
        cb.remove('Two')
        assert 3 == len(cb)
        assert 'Three' == next(cb)
        cb.remove('Three')
        assert 2 == len(cb)
        assert 'Four' == next(cb)
        try:
            cb.remove('Missing')
            pytest.fail("Should have raised ValueError")
        except ValueError: pass

    def test_update(self):
        cb = CircularBuffer(['One'])
        assert 1 == len(cb)
        two_id = cb.add("Two")
        assert two_id is not None
        assert 2 == len(cb)
        assert "Two" == next(cb)
        cb.update(two_id, "Twee")
        assert 2 == len(cb)
        assert "One" == next(cb)
        assert "Twee" == next(cb)
        try:
            cb.update(666, "something")
            pytest.fail("Should have raised KeyError")
        except KeyError:
            pass