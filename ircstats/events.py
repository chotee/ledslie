class IrcEvent(object):
    pass


class IrcChatEvent(IrcEvent):
    def __init__(self, ts, type, nick, msg=None, target=None):
        self.ts = ts
        self.type = type
        self.nick = nick
        self.msg = msg
        self.target = target
        # if self.target:
        #     log.info("%s:%s %s→%s %s", type, ts, nick, target, msg)
        # else:
        #     log.info("%s:%s %s %s", type, ts, nick, msg)


class IrcPresenceEvent(IrcEvent):
    def __init__(self, ts, nick, type, new_nick=None):
        self.ts = ts
        self.nick = nick
        self.type = type
        self.new_nick = new_nick