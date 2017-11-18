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


class FakeMQTTMessage(object):
    def __init__(self, topic=None, payload=None):
        self.topic = topic
        self.payload = payload


class FakeTimer(object):
    def __init__(self, delay, func, *args, **kwargs):
        pass

    def start(self):
        pass