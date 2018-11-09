#!/usr/bin/env python3
import logging
from typing import Iterable

from ircstats.database import EventDatabase
from ircstats.events import IrcEvent
from ircstats.parsers import IrssiParser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])

log_fn = "../logs/#techinc.log"


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
