#!/usr/bin/env python3
import itertools
import logging
from typing import Iterable

from ircstats.database import EventDatabase
from ircstats.events import IrcEvent
from ircstats.parsers import IrssiParser, WeechatParser

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])

log_fn_irssi = "../logs/#techinc.log"
log_fn_weechat = '../logs/irc.oftc.#techinc.weechatlog'

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
    log.info("Done c = %s" % c)


def main():
    log.info("Start")
    db = EventDatabase("irc.sqlite")
    irssi_parser = IrssiParser()
    weechat_parser = WeechatParser()
    c = 1
    for irc_event in itertools.chain(
            parse_file(irssi_parser, open(log_fn_irssi, 'r', errors='replace', encoding='UTF-8')),
            parse_file(weechat_parser, open(log_fn_weechat, 'r', errors='replace', encoding='UTF-8'))
    ):
        db.add_event(irc_event)
        # log.info(irc_event)
        if c % 100 == 0:
            log.info("loaded Row #%d", c)
        c += 1
    db.done()
    log.info("End")


if __name__ == "__main__":
    main()
