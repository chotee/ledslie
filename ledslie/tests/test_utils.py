import pytest
from ledslie.content.utils import CircularBuffer


class TestCircularBuffer(object):
    def test_usage(self):
        cb = CircularBuffer()
        assert 0 == len(cb)
        cb.add("Foo")
        assert 1 == len(cb)
        assert "Foo" == cb.next()
        assert "Foo" == cb.next()
        cb.add("Bar")
        assert 2 == len(cb)
        assert "Bar" == cb.next()
        assert "Foo" == cb.next()
        cb.add("Quux")
        assert "Quux" == cb.next()
        assert "Bar" == cb.next()
        assert "Foo" == cb.next()
        assert "Quux" == cb.next()

    def test_empty(self):
        cb = CircularBuffer()
        try: cb.next()
        except IndexError: pass
        else: pytest.fail("Should have raised IndexError")

    def test_init_load(self):
        cb = CircularBuffer(['One', 'Two', 'Three'])
        assert "One" == cb.next()
        assert "Two" == cb.next()
        assert "Three" == cb.next()
        assert "One" == cb.next()

    def test_remove(self):
        cb = CircularBuffer(['One', 'Two', 'Three', 'Four'])
        assert 4 == len(cb)
        assert "One" == cb.next()
        cb.remove('Two')
        assert 3 == len(cb)
        assert 'Three' == cb.next()
        cb.remove('Three')
        assert 2 == len(cb)
        assert 'Four' == cb.next()
        try:
            cb.remove('Missing')
            pytest.fail("Should have raised ValueError")
        except ValueError: pass
