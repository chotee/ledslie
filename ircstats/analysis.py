import logging

# guess_language-spirit package.
import re
from typing import List

from guess_language import guess_language
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from ircstats.database import EventDatabase

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__file__.split("/")[-1])

normal_chars = re.compile(r'[^a-zA-Z ]+')
sentiment_analyser = SentimentIntensityAnalyzer()


def main():
    db = EventDatabase("irc.sqlite")
    c = 0
    for chat in db.iter_chat_entries():
        if chat.target:
            msg = chat.msg.split(":", 1)[1]
        else:
            msg = chat.msg
        lang = detect_language(msg)
        sentiment = None
        if lang == 'en':
            sentiment = detect_sentiment(msg)
            nouns = detect_nouns(msg)
            db.add_nouns(chat.id, nouns)
        db.add_analysis(chat.id, lang, sentiment)
        c += 1
        if c % 100 == 0:
            log.info("#%s" % c)
            # break
    db.done()


def detect_sentiment(msg: str) -> float:
    return sentiment_analyser.polarity_scores(msg)['compound']


def detect_nouns(msg) -> List[str]:
    if "https://" in msg or "http://" in msg:
        return []
    clean_msg = normal_chars.sub('', msg)
    tokens = nltk.word_tokenize(clean_msg)
    token_tags = nltk.pos_tag(tokens)
    return set([word for word, token in token_tags if token == 'NN'])


def detect_language(msg):
    lang = guess_language(msg)
    if lang == "UNKNOWN":
        lang = None
    return lang


if __name__ == "__main__":
    main()