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

from twisted.internet.defer import CancelledError
from twisted.logger import Logger

from twisted.internet import reactor, task
from twisted.web.client import readBody
import treq

from ledslie.config import Config
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_1LINE
from ledslie.messages import TextSingleLineLayout


class RainContent(GenericContent):
    def __init__(self, endpoint, factory):
        self.log = Logger(self.__class__.__name__)
        super().__init__(endpoint, factory)
        self.task = None

    def onBrokerConnected(self):
        self.task = task.LoopingCall(self.createForecast)
        self.task.start(self.config['RAIN_UPDATE_FREQ'], now=True)

    def _logTimeout(self, failure):
        failure.trap(CancelledError)
        self.log.error("Timeout of request to %s" % self.config["RAIN_DATA_SOURCE"])

    def _logFailure(self, failure):
        self.log.error("reported failure: {message}", message=failure.getErrorMessage())
        return failure

    def _logSuccess(self, success, url):
        self.log.info("Success requesting {url}", url=url)
        return success

    def createForecast(self):
        url = self.config["RAIN_DATA_SOURCE"]
        self.log.debug("Grabbing rain forecast URL '%s'" % url)
        d = treq.get(url, timeout=5)
        d.addCallbacks(self.grab_http_response, self._logTimeout)
        d.addCallbacks(self.parse_forecast_results)
        d.addCallbacks(self.create_forcast)
        d.addCallbacks(self.publish_forcast)
        d.addCallback(self._logSuccess, url)
        d.addErrback(self._logFailure, url)

    def create_forcast(self, data):
        if data[0][0] == 0:  # It's currently dry
            for rain, t in data:
                if rain > 0:
                    return "Rain at %s" % t
            return None
        else:  # It's raining.
            for rain, t in data:
                if rain == 0:
                    return "Rain stop %s" % t
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
        if len(raw_arr) == 0:
            raise RuntimeWarning("API results where not in the expected format. They were: {}".format(raw_str))
        return raw_arr

    def publish_forcast(self, forcast_string: str):
        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)
        if forcast_string is None:  # There's no Rain information to show.
            return
        msg = TextSingleLineLayout()
        msg.text = forcast_string
        msg.duration = self.config["RAIN_DISPLAY_DURATION"]
        msg.program = 'rain'
        msg.font_size = 15
        d = self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_1LINE, message=msg, qos=1)
        d.addCallbacks(_logAll, self._logFailure)
        return d


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(RainContent)
    reactor.run()
