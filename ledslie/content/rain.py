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
from pprint import pprint

from twisted.internet import _sslverify
_sslverify.platformTrust = lambda: None
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.web.client import Agent, readBody, BrowserLikePolicyForHTTPS
from twisted.web.http_headers import Headers
import treq

from ledslie.config import Config
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_1LINE
from ledslie.messages import TextSingleLineLayout


class RainContent(GenericContent):
    @inlineCallbacks
    def connectToBroker(self, protocol, name):
        '''
        Connect to MQTT broker
        '''
        self.protocol = protocol
        self.protocol.onDisconnection = self.onDisconnection
        self.protocol.setWindowSize(3)
        self.task = task.LoopingCall(self.createForecast)
        self.task.start(self.config['RAIN_UPDATE_FREQ'], now=False)
        # self.reactor.callLater(0, self.createForecast)
        try:
            yield self.protocol.connect(self.__class__.__name__, keepalive=60)
        except Exception as e:
            self.log.error("Connecting to {broker} raised {excp!s}",
                           broker=self.config.get('MQTT_BROKER_CONN_STRING'), excp=e)
        else:
            self.log.info("Connected to {broker}", broker=self.config.get('MQTT_BROKER_CONN_STRING'))

    def _logFailure(self, failure):
        self.log.debug("reported failure: {message}", message=failure.getErrorMessage())
        return failure

    def createForecast(self):
        d = treq.get(self.config["RAIN_DATA_SOURCE"])
        d.addCallbacks(self.grab_http_response, self._logFailure)
        d.addCallbacks(self.parse_forecast_results, self._logFailure)
        d.addCallbacks(self.create_forcast, self._logFailure)
        d.addCallbacks(self.publish_forcast, self._logFailure)

    def create_forcast(self, data):
        if data[0][0] == 0:  # It's currently dry
            for rain, t in data:
                if rain > 0:
                    return "Rain at %s" % t
            return "Dry until %s" % data[-1][1]
        else:  # It's raining.
            for rain, t in data:
                if rain == 0:
                    return "Rain stops: %s" % t
            return "Rain Rain Rain"

    def grab_http_response(self, response):
        if response.code != 200:
            raise RuntimeError("Status is not 200 but '%s'" % response.code)
        return readBody(response)

    def parse_forecast_results(self, content):
        raw_str = content.decode()
        raw_arr = []
        for raw in raw_str.split("\r\n"):
            if not raw:
                continue
            rain_value, hour = raw.split("|")
            raw_arr.append([int(rain_value, 10), hour])
        return raw_arr

    def publish_forcast(self, forcast_string):
        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)

        # d = self._rain_request()
        #

        # self.log.debug(" >< Starting one round of publishing >< ")
        msg = TextSingleLineLayout()
        msg.duration = self.config["RAIN_DISPLAY_DURATION"]
        msg.program = 'rain'
        d = self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_1LINE, message=bytes(msg), qos=1)
        d.addCallbacks(_logAll, self._logFailure)
        return d


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(RainContent)
    reactor.run()
