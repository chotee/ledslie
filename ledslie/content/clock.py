# Ledslie, a community information display
# Copyright (C) 2017  Chotee@openended.eu
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

from datetime import datetime

import os
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.logger import Logger

from ledslie.config import Config
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_1LINE
from ledslie.messages import TextSingleLineLayout
from ledslie.content.generic import GenericContent, CreateContent

class ClockContent(GenericContent):
    def __init__(self, endpoint, factory):
        self.log = Logger(self.__class__.__name__)
        super().__init__(endpoint, factory)

    def onBrokerConnected(self):
        self.task = task.LoopingCall(self.publishClock)
        self.task.start(1, now=True)

    def publishClock(self):
        def _logFailure(failure):
            self.log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)

        self.log.debug(" >< Starting one round of publishing >< ")
        date_str = str(datetime.now().strftime("%a %H:%M:%S"))
        msg = TextSingleLineLayout()
        msg.text = date_str
        msg.duration = 1000
        msg.program = 'clock'
        d = self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_1LINE, qos=0, message=msg)
        d.addCallbacks(_logAll, _logFailure)
        return d


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(ClockContent)
    reactor.run()
