import logging
import re
from datetime import datetime

from dateutil import parser as dateparser

from ircstats.events import IrcEvent, IrcChatEvent, IrcPresenceEvent

log = logging.getLogger(__file__.split("/")[-1])

class GenericParser(object):
    def __init__(self):
        self.line_patterns = ()
        self.target_pattern = re.compile(r"(?P<target>\S+): .*")

    def parse_line(self, line) -> IrcEvent:
        line = line.strip()
        match = None
        res = None
        for pattern, func in self.line_patterns:
            match = pattern.match(line)
            if match:
                res = func(**match.groupdict())
                break
        if match is None:
            log.warning("unmatched: %s" % line)
        return res


class WeechatParser(GenericParser):
    def __init__(self):
        super().__init__()
        self.line_patterns = (
            (re.compile(r"(?P<date>\S+ \S+)\t(?P<mode>@|)(?P<nick>(?!<--|--|-->)[^\t\*]+)\t(?P<msg>.*)"), self.chat_line),
            (re.compile(r"(?P<date>\S+ \S+)\t \*\t(?P<nick>\S+) (?P<msg>.*)"), self.action_line),
            (re.compile(r"(?P<date>\S+ \S+)\t(<--|-->)?\t(?P<nick>\S+).*has (?P<action>\S+)"), self.presence_event),
            (re.compile(r"(?P<date>\S+ \S+)\t--\t(?P<oldnick>\S+) is now known as (?P<newnick>\S+)"), self.nick_change),
        )

    def chat_line(self, date, nick, mode, msg) -> IrcChatEvent:
        ts = dateparser.parse(date)
        match = self.target_pattern.match(msg)
        if match:
            target = match.group(1)
        else:
            target = None
        return IrcChatEvent(ts, "msg", nick, msg, target)

    def action_line(self, date, nick, msg) -> IrcChatEvent:
        ts = dateparser.parse(date)
        return IrcChatEvent(ts, "action", nick, msg)

    def presence_event(self, date, nick, action) -> IrcPresenceEvent:
        ts = dateparser.parse(date)
        return IrcPresenceEvent(ts, nick, action)

    def nick_change(self, date, oldnick, newnick) -> IrcPresenceEvent:
        ts = dateparser.parse(date)
        return IrcPresenceEvent(ts, oldnick, "change", new_nick=newnick)


class IrssiParser(GenericParser):
    def __init__(self):
        super().__init__()
        self.last_ts = None
        self.line_patterns = (
            (re.compile(r"(?P<time>\d{2}:\d{2}) <(?P<mode> |@)(?P<nick>[^ ]+)> (?P<msg>.*)"), self.chat_line),
            (re.compile(r"(?P<time>\d{2}:\d{2})  \* (?P<nick>[^ ]+) (?P<msg>.*)"), self.action_line),
            (re.compile(r"--- Log opened (?P<date>.*)"), self.log_open),
            (re.compile(r"--- Day changed (?P<date>.*)"), self.day_start),
            (re.compile(r"(?P<time>\d{2}:\d{2}) -!- (?P<nick>[^ ]+) \[(?P<host>.*)\] has (?P<action>[^ ]+)"),
             self.presence_event),
            (re.compile(r"(?P<time>\d{2}:\d{2}) -!- (?P<oldnick>[^ ]+) is now known as (?P<newnick>[^ ]+)"),
             self.nick_change),
        )

    def chat_line(self, time, nick, mode, msg) -> IrcChatEvent:
        ts = self._parse_time(self.last_ts, time)
        match = self.target_pattern.match(msg)
        if match:
            target = match.group(1)
        else:
            target = None
        return IrcChatEvent(ts, "msg", nick, msg, target)

    def action_line(self, time, nick, msg) -> IrcChatEvent:
        ts = self._parse_time(self.last_ts, time)
        return IrcChatEvent(ts, "action", nick, msg)

    def log_open(self, date):
        date = dateparser.parse(date)
        self.last_ts = date

    def day_start(self, date):
        date = dateparser.parse(date)
        self.last_ts = date

    def presence_event(self, time, nick, host, action) -> IrcPresenceEvent:
        ts = self._parse_time(self.last_ts, time)
        return IrcPresenceEvent(ts, nick, action)

    def nick_change(self, time, oldnick, newnick) -> IrcPresenceEvent:
        ts = self._parse_time(self.last_ts, time)
        return IrcPresenceEvent(ts, oldnick, "change", new_nick=newnick)

    def _parse_time(self, ts: datetime, time: str) -> datetime:
        hour, minute = map(int, time.split(":"))
        tt = list(ts.timetuple())
        tt[3] = hour
        tt[4] = minute
        tt[5] = 0
        return datetime(*tt[:6])