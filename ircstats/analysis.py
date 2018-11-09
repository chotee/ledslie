import logging

from guess_language import guess_language

from ircstats.database import EventDatabase

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])


def main():
    db = EventDatabase("irc.sqlite")
    c = 0
    for chat in db.iter_chat_entries():
        lang = guess_language(chat.msg)
        if lang == "UNKNOWN":
            lang = None
        db.add_analysis(chat.id, lang)
        if c % 100 == 0:
            log.info("#%s" % c)
        c += 1
    db.done()


if __name__ == "__main__":
    main()