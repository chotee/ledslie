import pytest

from ledslie.tests.fakes import FakeClient


@pytest.fixture
def client():
    return FakeClient()
