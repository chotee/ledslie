#!/usr/bin/env python3

import logging
import re

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])

log_fn = "../logs/#techinc.log"

def chat_line(time, nick, mode, msg):
    # log.info("Chat line: " + ", ".join([time, nick, msg]))
    pass

def action_line(time, nick, msg):
    # log.info("Chat line: " + ", ".join([time, nick, msg]))
    pass


def log_open(date):
    # log.info("Log open: " + date)
    pass


def day_start(date):
    pass


def presence_event(time, nick, host, action):
    pass

def nick_change(time, oldnick, newnick):
    pass


line_selector = (
    (re.compile(r"(?P<time>\d{2}:\d{2}) <(?P<mode> |@)(?P<nick>[^ ]+)> (?P<msg>.*)"), chat_line),
    (re.compile(r"(?P<time>\d{2}:\d{2})  * (?P<nick>[^ ]+) (?P<msg>.*)"), action_line),
    (re.compile(r"--- Log opened (?P<date>.*)"), log_open),
    (re.compile(r"--- Day changed (?P<date>.*)"), day_start),
    (re.compile(r"(?P<time>\d{2}:\d{2}) -!- (?P<nick>[^ ]+) \[(?P<host>.*)\] has (?P<action>[^ ]+)"), presence_event),
    (re.compile(r"(?P<time>\d{2}:\d{2}) -!- (?P<oldnick>[^ ]+) is now known as (?P<newnick>[^ ]+)"), nick_change),

)


def parse_irssi(fd):
    c = 0
    line = fd.readline()
    while line != "":
        # if line.startswith("--- "):
        #     handle_metadata(line)
        c += 1
        line = line.strip()
        match = None
        for pattern, func in line_selector:
            match = pattern.match(line)
            if match:
                func(**match.groupdict())
                break
        if match is None:
            log.warning("unmatched: %s" % line)
        line = fd.readline()
        if c > 5000:
            break
    log.info("c = %s" % c)


def main():
    log.info("Start")
    parse_irssi(open(log_fn, 'r', errors='replace', encoding='UTF-8'))
    log.info("End")

if __name__ == "__main__":
    main()