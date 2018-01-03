# Ledslie, a community information display
# Copyright (C) 2017-18  Chotee@openended.eu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

import bs4
from dateutil.parser import parser as date_parser
from datetime import date, datetime

from twisted.internet.defer import Deferred
from twisted.logger import Logger

from twisted.internet import reactor, task
from twisted.web.client import readBody
import treq

from ledslie.config import Config
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_3LINES
from ledslie.messages import TextTripleLinesLayout


def create_date_string(event_date, now=None):
    now = datetime.now().date() if now is None else now
    day_diff = (event_date - now).days
    if day_diff == 0:
        return "Today"
    elif day_diff == 1:
        return "Tomorrow"
    elif day_diff <= 5:
        return event_date.strftime("%a")
    else:
        return event_date.strftime("%a%d")


class EventsContent(GenericContent):
    def __init__(self, endpoint, factory):
        self.log = Logger(self.__class__.__name__)
        super().__init__(endpoint, factory)
        self.task = None

    def onBrokerConnected(self):
        self.task = task.LoopingCall(self.createEventsInfo)
        self.task.start(self.config['EVENTS_UPDATE_FREQ'], now=True)

    def _logFailure(self, failure):
        self.log.debug("reported failure: {message}", message=failure.getErrorMessage())
        return failure

    def createEventsInfo(self):
        d = treq.get(self.config["EVENTS_DATA_SOURCE"])
        d.addCallbacks(self.grab_http_response, self._logFailure)
        d.addCallbacks(self.parse_page, self._logFailure)
        d.addCallbacks(self.create_event_info, self._logFailure)
        d.addCallbacks(self.publish_events, self._logFailure)

    def create_event_info(self, event_data, now=None):
        lines = []
        for event_name, event_date in event_data[:5]:
            date_str = create_date_string(event_date, now)
            lines.append("%s: %s" % (date_str, event_name))
        return lines

    def grab_http_response(self, response):
        if response.code != 200:
            raise RuntimeError("Status is not 200 but '%s'" % response.code)
        return readBody(response)

    def parse_page(self, content):
        html = bs4.BeautifulSoup(content, "html.parser")
        events = []
        table = html.find('table', {"class": "wikitable"})
        for tr in table.findAll('tr')[1:]:  # Iter over the table rows
            e_name, e_date = tr.findAll('td')[:2]
            name = e_name.getText().strip()
            date = date_parser().parse(e_date.getText().strip()).date()
            events.append([name, date])
        return events

    def publish_events(self, event_lines: list) -> Deferred:
        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)
        msg = TextTripleLinesLayout()
        msg.lines = event_lines
        msg.line_duration = self.config["EVENTS_LINE_DURATION"]
        msg.program = 'events'
        msg.size = '6x7'
        d = self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_3LINES, message=msg, qos=1)
        d.addCallbacks(_logAll, self._logFailure)
        return d


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(EventsContent)
    reactor.run()
