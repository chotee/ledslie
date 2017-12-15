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
import json
import os

from datetime import datetime

from twisted.internet.defer import Deferred
from twisted.logger import Logger

from twisted.internet import reactor, task
from twisted.web.client import readBody
import treq

from ledslie.config import Config
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_3LINES
from ledslie.messages import TextTripleLinesLayout

# Info https://github.com/skywave/KV78Turbo-OVAPI/wiki

# http://v0.ovapi.nl/stopareacode
# Louwesweg: "asdlww" and "04088"
# Aletta Jacobslaan "04094"
# Henk Sneevlietweg "04006"

# GVB_2_1  # TRAM to CS
# GVB_18_1  # BUS to CS

 


class OVInfoContent(GenericContent):
    def __init__(self, endpoint, factory):
        self.log = Logger(self.__class__.__name__)
        super().__init__(endpoint, factory)
        self.task = None

    def onBrokerConnected(self):
        self.task = task.LoopingCall(self.createCoinsInfo)
        self.task.start(self.config['COINS_UPDATE_FREQ'], now=True)

    def _logFailure(self, failure):
        self.log.debug("reported failure: {message}", message=failure.getErrorMessage())
        return failure

    def createCoinsInfo(self):
        d = treq.get(self.config["COINS_PRICE_SOURCE"])
        d.addCallbacks(self.grab_http_response, self._logFailure)
        d.addCallbacks(self.parse_page, self._logFailure)
        d.addCallbacks(self.create_coins_info, self._logFailure)
        d.addCallbacks(self.publish_prices, self._logFailure)

    def create_coins_info(self, coins_data: dict, now=None):
        lines = []
        lines.append("Bitcoin: €{:8.2f}".format(coins_data['BTC']['EUR']))
        lines.append("BTCcash: €{:8.2f}".format(coins_data['BCH']['EUR']))
        lines.append("Ether  : €{:8.2f}".format(coins_data['ETH']['EUR']))
        return lines

    def grab_http_response(self, response):
        if response.code != 200:
            raise RuntimeError("Status is not 200 but '%s'" % response.code)
        return readBody(response)

    def parse_page(self, content):
        prices = json.loads(content.decode())
        return prices

    def publish_prices(self, coin_lines: list) -> Deferred:
        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)
        msg = TextTripleLinesLayout()
        msg.lines = coin_lines
        msg.duration = self.config["COINS_DISPLAY_DURATION"]
        msg.program = 'coins'
        d = self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_3LINES, message=msg, qos=1)
        d.addCallbacks(_logAll, self._logFailure)
        return d


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(CoinsContent)
    reactor.run()
