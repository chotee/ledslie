import sqlite3
from typing import Iterator, List

from ircstats.events import IrcEvent, IrcPresenceEvent, IrcChatEvent

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

    def iter_chat_entries(self) -> Iterator[IrcChatEvent]:
        cursor = self._db.cursor()
        cursor.execute("select ts, nick, type, msg, target, id from chat order by id")
        while True:
            res = cursor.fetchone()
            if res is None:
                raise StopIteration
            yield IrcChatEvent(*res)

    def add_analysis(self, id, language, sentiment):
        self._db.execute("""insert into analysis (id, lang, sentiment) values (?, ?, ?)""", (id, language, sentiment))

    def add_nouns(self, id: int, nouns: List[str]):
        for noun in nouns:
            self._db.execute("""insert into noun (id, word) values (?, ?)""", (id, noun.lower()))

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
        self._db.execute("""CREATE TABLE analysis (
            id integer references chat(id),
            lang varchar,
            sentiment float);""")
        self._db.execute("""CREATE TABLE noun (
  
            id integer references chat(id),
            word varchar not null);""")
        self._db.execute("""insert into db_version (version, ts)  values (1, current_timestamp)""")
        self._db.commit()