import logging

# guess_language-spirit package.
from guess_language import guess_language

from ircstats.database import EventDatabase

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])


def main():
    db = EventDatabase("irc.sqlite")
    c = 0
    for chat in db.iter_chat_entries():
        if chat.target:
            msg = chat.msg.split(":", 1)[1]
        else:
            msg = chat.msg
        lang = detect_language(msg)
        db.add_analysis(chat.id, lang)
        if c % 100 == 0:
            log.info("#%s" % c)
        c += 1
    db.done()


def detect_language(msg):
    lang = guess_language(msg)
    if lang == "UNKNOWN":
        lang = None
    return lang


if __name__ == "__main__":
    main()