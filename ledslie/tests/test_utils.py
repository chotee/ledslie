import pytest
from ledslie.content.utils import CircularBuffer


class TestCircularBuffer(object):
    def test_usage(self):
        cb = CircularBuffer()
        cb.add("Foo")
        assert "Foo" == cb.next()
        assert "Foo" == cb.next()
        cb.add("Bar")
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