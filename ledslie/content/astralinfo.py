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
from datetime import datetime, timedelta

from twisted.internet import reactor, task
from twisted.internet.defer import DeferredList
from twisted.logger import Logger

import pytz
from astral import Astral

from ledslie.config import Config
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_1LINE
from ledslie.messages import TextSingleLineLayout, TextTripleLinesLayout


class AstralContent(GenericContent):
    def __init__(self, endpoint, factory):
        self.log = Logger(self.__class__.__name__)
        super().__init__(endpoint, factory)
        self.astral = Astral()
        self.astral.solar_depression = 'civil'
        self.city = self.astral['Amsterdam']
        self.publish_task = None

    def onBrokerConnected(self):
        self.publish_task = task.LoopingCall(self.publish_astral)
        self.publish_task.start(60, now=True)

    def publish_astral(self, now=None):
        """I am called every minute."""
        self.log.info("Checking astral events.")
        def _logFailure(failure):
            self.log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)

        deferreds = []

        now = self._now(now)

        moon_msg = self.moon_message(now)
        if moon_msg:
            deferreds.append(self._create_single_msg('moon', moon_msg))

        solar_msg = self.sun_message(now)
        if solar_msg:
            deferreds.append(self._create_multi_msg('solar', [solar_msg, self.light_time(), self.dark_time()]))

        if deferreds:
            dl = DeferredList(deferreds)
            dl.addCallbacks(_logAll, _logFailure)
            return dl
        else:
            return None

    def light_time(self, now=None) -> str:
        now = self._now(now)
        start, end = self.city.daylight(now.date())
        return "Day:  % 8s" % str(end-start)

    def dark_time(self, now=None) -> str:
        now = self._now(now)
        start, end = self.city.daylight(now.date())
        return "Night:% 8s" % str(timedelta(days=1)- (end-start))

    def _create_single_msg(self, prog_name, solar_msg):
        msg = TextSingleLineLayout()
        msg.text = solar_msg
        msg.program = prog_name
        msg.valid_time = 60
        msg.font_size = 15
        return self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_1LINE, message=msg)

    def _create_multi_msg(self, prog_name, solar_msg):
        msg = TextTripleLinesLayout()
        msg.lines = solar_msg
        msg.program = prog_name
        self.size = '7x6'
        msg.valid_time = 60
        return self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_1LINE, message=msg)


    def _now(self, dt=None):
        dt = datetime.now() if dt is None else dt
        dt = pytz.timezone(self.config['TIMEZONE']).localize(dt)
        return dt

    def moon_message(self, now: datetime):
        moon_phase = self.city.moon_phase(now)
        if moon_phase == 21:
            return "Full moon"
        if moon_phase == 0:
            return "New moon"
        return None

    def sun_message(self, now: datetime):
        pretime = 30*60

        time_to_sunrise = (self.city.sunrise(now) - now).total_seconds()
        if time_to_sunrise > 0:
            if time_to_sunrise < 60:
                return "Sunrise now"
            elif time_to_sunrise < pretime:
                return "Sunrise in %sm" % int(time_to_sunrise / 60)

        time_to_highnoon = (self.city.solar_noon(now) - now).total_seconds()
        if time_to_highnoon > 0:
            if time_to_highnoon < 60:
                return "Solar noon now"
            elif time_to_highnoon < pretime:
                return "Solar noon in %sm" % int(time_to_highnoon / 60)

        time_to_sunset = (self.city.sunset(now) - now).total_seconds()
        if time_to_sunset > 0:
            if time_to_sunset < 60:
                return "Sunset now"
            if time_to_sunset < pretime:
                return "Sunset in %sm" % int(time_to_sunset / 60)

        time_to_midnight = (self.city.solar_midnight(now) - now).total_seconds()
        if time_to_midnight > 0:
            if time_to_midnight < 60:
                return "Solar midnight now"
            if time_to_midnight < pretime:
                return "S. Midnight in %sm" % int(time_to_midnight / 60)

        return None


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(AstralContent)
    reactor.run()
