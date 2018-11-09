class IrcEvent(object):
    pass


class IrcChatEvent(IrcEvent):
    def __init__(self, ts, type, nick, msg=None, target=None, id=None):
        self.ts = ts
        self.type = type
        self.nick = nick
        self.msg = msg
        self.target = target
        self.id = id


class IrcPresenceEvent(IrcEvent):
    def __init__(self, ts, nick, type, new_nick=None, id=None):
        self.ts = ts
        self.nick = nick
        self.type = type
        self.new_nick = new_nick
        self.id = id