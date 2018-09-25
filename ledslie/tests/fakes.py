from twisted.internet.test.test_tcp import FakeProtocol
from twisted.internet.defer import succeed

class FakeClient(object):
    def __init__(self):
        self.pubed_messages = []

    def connect(self, host, port, keepalive):
        pass

    def subscribe(self, topic):
        pass

    def publish(self, topic, data):
        self.pubed_messages.append([topic, data])

    def loop_forever(self):
        pass

    def assert_message_pubed(self, topic):
        return [msg for msg in self.pubed_messages if msg[0].startswith(topic)]


class FakeTimer(object):
    def __init__(self, delay, func, *args, **kwargs):
        pass

    def start(self):
        pass


class FakeMqttProtocol(FakeProtocol):
    def __init__(self):
        self._published_messages = []

    def setWindowSize(self, size):
        pass

    def connect(self, name, keepalive=None):
        pass

    def subscribe(self, topic, qos=0):
        return succeed("subscribed to %s" % topic)

    def publish(self, topic, message, qos, retain=False):
        assert isinstance(message, (bytearray, bytes)), "type is %s, expected bytearray or bytes" % type(message)
        self._published_messages.append((topic, message))
        return succeed(None)


class FakeLogger(object):
    def error(self, msg, **kwargs):
        raise RuntimeError(msg.format(**kwargs))
        # pass

    def info(self, msg, **kwargs):
        # raise RuntimeError(msg.format(**kwargs))
        pass

    def debug(self, msg, **kwargs):
        # raise RuntimeError(msg.format(**kwargs))
        pass

    def warn(self, msg, **kwargs):
        # raise RuntimeError(msg.format(**kwargs))
        pass


class FakeLEDScreen(object):
    def __init__(self):
        self._published_frames = []

    def publish_frame(self, data):
        self._published_frames.append(data)

# class FakeMQTTMessage(object):
#     def __init__(self, topic=None, payload=None):
#         self.topic = topic
#         self.payload = payload
#
#
# class FakeTimer(object):
#     def __init__(self, delay, func, *args, **kwargs):
#         pass
#
#     def start(self):
#         pass