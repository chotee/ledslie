#!/usr/bin/env python3

import logging
import re

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])

log_fn = "../logs/#techinc.log"


class IrssiParser(object):
    def __init__(self):
        self.date = None
        self.line_patterns = (
            (re.compile(r"(?P<time>\d{2}:\d{2}) <(?P<mode> |@)(?P<nick>[^ ]+)> (?P<msg>.*)"), self.chat_line),
            (re.compile(r"(?P<time>\d{2}:\d{2})  * (?P<nick>[^ ]+) (?P<msg>.*)"), self.action_line),
            (re.compile(r"--- Log opened (?P<date>.*)"), self.log_open),
            (re.compile(r"--- Day changed (?P<date>.*)"), self.day_start),
            (re.compile(r"(?P<time>\d{2}:\d{2}) -!- (?P<nick>[^ ]+) \[(?P<host>.*)\] has (?P<action>[^ ]+)"),
             self.presence_event),
            (re.compile(r"(?P<time>\d{2}:\d{2}) -!- (?P<oldnick>[^ ]+) is now known as (?P<newnick>[^ ]+)"),
             self.nick_change),
        )

    def parse_line(self, line):
        line = line.strip()
        match = None
        for pattern, func in self.line_patterns:
            match = pattern.match(line)
            if match:
                func(**match.groupdict())
                break
        if match is None:
            log.warning("unmatched: %s" % line)

    def chat_line(self, time, nick, mode, msg):
        # log.info("Chat line: " + ", ".join([time, nick, msg]))
        pass

    def action_line(self, time, nick, msg):
        # log.info("Chat line: " + ", ".join([time, nick, msg]))
        pass

    def log_open(self, date):
        # log.info("Log open: " + date)
        pass

    def day_start(self, date):
        pass

    def presence_event(self, time, nick, host, action):
        pass

    def nick_change(self, time, oldnick, newnick):
        pass


def parse_file(parser, fd):
    c = 0
    line = fd.readline()
    while line != "":
        c += 1
        parser.parse_line(line)
        line = fd.readline()
        if c > 5000:
            break
    log.info("c = %s" % c)


def main():
    log.info("Start")
    parser = IrssiParser()
    parse_file(parser, open(log_fn, 'r', errors='replace', encoding='UTF-8'))
    log.info("End")

if __name__ == "__main__":
    main()