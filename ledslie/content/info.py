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
import os

from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks

from ledslie.config import Config
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_3LINES
from ledslie.messages import TextTripleLinesLayout


class InfoContent(GenericContent):
    @inlineCallbacks
    def connectToBroker(self, protocol):
        '''
        Connect to MQTT broker
        '''
        self.protocol = protocol
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3)
        self.task = task.LoopingCall(self.publishInfo)
        self.task.start(5, now=False)
        try:
            yield self.protocol.connect(self.__class__.__name__, keepalive=60)
        except Exception as e:
            self.log.error("Connecting to {broker} raised {excp!s}",
                           broker=self.config.get('MQTT_BROKER_CONN_STRING'), excp=e)
        else:
            self.log.info("Connected to {broker}", broker=self.config.get('MQTT_BROKER_CONN_STRING'))

    def publishInfo(self):
        def _logFailure(failure):
            self.log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)

        self.log.debug(" >< Starting one round of publishing >< ")
        msg = TextTripleLinesLayout()
        msg.lines = [
            "Ledslie © GNU-AGPL3 ~ ;-)",
            "https://wiki.techinc.nl/index.php/Ledslie",
            "https://github.com/techinc/ledslie",
        ]
        msg.duration = 5000
        msg.program = 'info'
        d = self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_3LINES, message=bytes(msg), qos=1)
        d.addCallbacks(_logAll, _logFailure)
        return d


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(InfoContent)
    reactor.run()
