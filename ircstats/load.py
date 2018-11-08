#!/usr/bin/env python3
from datetime import datetime
import logging
import re
from typing import Iterable

import sqlite3

from dateutil import parser as dateparser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])

log_fn = "../logs/#techinc.log"


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


class IrssiParser(object):
    def __init__(self):
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
        self.target_pattern = re.compile(r"(?P<target>\S+):.*")

    def parse_line(self, line) -> IrcEvent:
        line = line.strip()
        match = None
        res = None
        for pattern, func in self.line_patterns:
            match = pattern.match(line)
            if match:
                res = func(**match.groupdict())
                break
        # if match is None:
        #     log.warning("unmatched: %s" % line)
        return res

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


def parse_file(parser, fd) -> Iterable[IrcEvent]:
    c = 0
    line = fd.readline()
    while line != "":
        c += 1
        res = parser.parse_line(line)
        if res:
            yield res
        line = fd.readline()
        # if c > 5000:
        #     break
    log.info("c = %s" % c)


class EventDatabase(object):
    def __init__(self, filename: str):
        self._db = sqlite3.connect(filename)
        try:
            self._db.execute("select * from db_version order by id desc limit 1")
        except sqlite3.OperationalError as exc:
            if exc.args[0] == "no such table: db_version":
                self._create_db()
            else:
                raise

    def add_event(self, event: IrcEvent):
        if isinstance(event, IrcPresenceEvent):
            self.add_presence_event(event)
        elif isinstance(event, IrcChatEvent):
            self.add_chat_event(event)
        else:
            raise RuntimeError("Cannot handle event of type %s", type(event))

    def add_presence_event(self, event: IrcPresenceEvent):
        if event.new_nick:
            self._db.execute("""insert into presence (ts, nick, type, new_nick) values (?, ?, ?, ?)""",
                             (event.ts, event.nick, event.type, event.new_nick))
        else:
            self._db.execute("""insert into presence (ts, nick, type) values (?, ?, ?)""",
                             (event.ts, event.nick, event.type))

    def add_chat_event(self, event: IrcChatEvent):
        if event.target:
            self._db.execute("""insert into chat (ts, nick, type, msg, target) values (?, ?, ?, ?, ?)""",
                             (event.ts, event.nick, event.type, event.msg, event.target))
        else:
            self._db.execute("""insert into chat (ts, nick, type, msg) values (?, ?, ?, ?)""",
                             (event.ts, event.nick, event.type, event.msg))

    def done(self):
        self._db.commit()

    def _create_db(self):
        self._db.execute("""create table db_version (
            id integer primary key autoincrement,	
            version varchar NOT NULL, 
            ts timestamp)""")
        self._db.execute("""CREATE TABLE chat (
            id integer PRIMARY KEY AUTOINCREMENT,
            ts timestamp NOT NULL,
            nick varchar NOT NULL,
            type varchar NOT NULL,
            msg varchar,
            target varchar );""")
        self._db.execute("""CREATE TABLE presence (
            id integer PRIMARY KEY AUTOINCREMENT,
            ts timestamp NOT NULL,
            nick varchar NOT NULL,
            type varchar NOT NULL,
            new_nick varchar );""")
        self._db.execute("""insert into db_version (version, ts)  values (1, current_timestamp)""")
        self._db.commit()


def main():
    log.info("Start")
    db = EventDatabase("irc.sqlite")
    parser = IrssiParser()
    c = 1
    for irc_event in parse_file(parser, open(log_fn, 'r', errors='replace', encoding='UTF-8')):
        db.add_event(irc_event)
        if c % 100 == 0:
            log.info("loaded Row #%d", c)
        c += 1
    db.done()
    log.info("End")


if __name__ == "__main__":
    main()
