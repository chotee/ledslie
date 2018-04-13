# Ledslie, a community information display
# Copyright (C) 2018  Chotee@openended.eu
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

from calendar import monthrange
from datetime import datetime

import os
from twisted.internet import reactor, task
from twisted.logger import Logger

from ledslie.bitfont.font8x8 import font8x8
from ledslie.config import Config
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_PROGRAMS
from ledslie.messages import FrameSequence, Frame
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.processors.typesetter import MarkupLine


class Progress(GenericContent):
    def __init__(self, endpoint, factory):
        self.log = Logger(self.__class__.__name__)
        super().__init__(endpoint, factory)

    def onBrokerConnected(self):
        self.task = task.LoopingCall(self.publishProgress)
        self.task.start(60, now=True)  # Update content every minute

    def publishProgress(self):
        def _logFailure(failure):
            self.log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)

        # self.log.debug(" >< Starting one round of publishing >< ")
        now = datetime.now()
        seq = FrameSequence()
        image = bytearray()
        image.extend(self._create_graph_line(self._create_day_progress(now)))
        image.extend(self._create_graph_line(self._create_month_progress(now)))
        image.extend(self._create_graph_line(self._create_year_progress(now)))
        frame = Frame(image, duration=self.config['PROGRESS_DISPLAY_DURATION'])
        seq.add_frame(frame)
        seq.program = "progress"
        d = self.publish(topic=LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + seq.program, message=seq)
        d.addCallbacks(_logAll, _logFailure)
        return d

    def _create_graph_line(self, values):
        string, fraction = values
        line = bytearray()
        MarkupLine(line, string, font8x8)
        display_width = Config()['DISPLAY_WIDTH']
        line_location = int(display_width * fraction)
        for x in range(8):
            begin = x*display_width
            end = x*display_width+line_location
            c = begin
            while c < end:
                line[c] = (~(line[c]) & 0xff)
                c += 1
        return line

    def _create_day_progress(self, now):
        fraction = (now.hour*60*60 + now.minute*60 + now.second) / (24*60*60.0)
        time_string = now.strftime("%H:%M")
        line_string = "{:13s}{:5.1%}".format(time_string, fraction)
        return line_string, fraction

    def _create_month_progress(self, now):
        days_in_the_month = monthrange(now.year, now.month)[1]
        fraction = ((now.day-1)*24*60*60 + now.hour*60*60 + now.minute*60 + now.second) / (days_in_the_month * 24 * 60 * 60.0)
        time_string = now.strftime("%B %d")
        line_string = "{:13s}{:5.1%}".format(time_string, fraction)
        return line_string, fraction

    def _create_year_progress(self, now):
        seconds_since_newyear = (now - datetime(now.year, 1, 1, 0, 0, 0)).total_seconds()
        seconds_in_year = (datetime(now.year + 1, 1, 1, 0, 0, 0) - datetime(now.year, 1, 1, 0, 0, 0)).total_seconds()
        fraction = seconds_since_newyear / seconds_in_year
        year_day = now.timetuple()[7]
        time_string = "{} of {}".format(year_day, now.year)
        line_string = "{:12s}{:6.1%}".format(time_string, fraction)
        return line_string, fraction


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(Progress)
    reactor.run()
