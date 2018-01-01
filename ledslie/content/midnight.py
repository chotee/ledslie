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
import random
from datetime import datetime, timedelta
from dateutil.tz import gettz, tzlocal

from twisted.internet import reactor
from twisted.logger import Logger

from ledslie.config import Config
from ledslie.content.generic import GenericContent, CreateContent
from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_3LINES
from ledslie.messages import TextTripleLinesLayout

import pytz

def next_midnight(tz_str=None):
    if tz_str is None:
        tz = tzlocal()
    else:
        tz = gettz(tz_str)
    now = datetime.now(tz) + timedelta(days=1)
    midnight = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz)
    midnight_home_time = midnight.astimezone(tzlocal())
    return midnight_home_time


def all_next_midnights():
    now_home = datetime.now(tzlocal())
    midnights = []
    for tzname in pytz.all_timezones:
        tzname_parts = tzname.split('/')
        if len(tzname_parts) == 1:
            continue
        if tzname_parts[0] in ['Etc', 'US', "Brazil", 'Canada', "Chile"]:
            continue
        if tzname_parts[-1].isupper():
            continue
        midnight_diff_seconds = midnight_seconds(tzname)
        midnights.append((tzname, midnight_diff_seconds))
    return midnights


def midnight_seconds(tzname):
    midnight_tzname = next_midnight(tzname)
    midnight_home = next_midnight()
    seconds_till_midnight = (midnight_tzname - midnight_home).total_seconds()
    return seconds_till_midnight


def create_city_name(tzname):
    tzname_parts = tzname.split('/')
    city_name = tzname_parts[-1].replace("_", " ")
    return city_name


def create_midnight_groups():
    midnight_groups = {}
    for tz_name, midnight in all_next_midnights():
        group = midnight_groups.setdefault(midnight, [])
        group.append(tz_name)
    return midnight_groups


class MidnightContent(GenericContent):
    def __init__(self, endpoint, factory):
        self.log = Logger(self.__class__.__name__)
        super().__init__(endpoint, factory)
        self.tz_groups = create_midnight_groups()
        self.is_empty = True

    def onBrokerConnected(self):
        now = datetime.now(tzlocal())
        if self.is_empty:
            for offset in self.tz_groups.keys():
                self.call_on_midnight_offset(now, offset)
        self.is_empty = False

    def call_on_midnight_offset(self, now, offset):
        moment = next_midnight() + timedelta(seconds=offset)
        if moment < now:
            moment = moment + timedelta(days=1)
        seconds_to_wait = (moment - now).total_seconds()
        self.reactor.callLater(seconds_to_wait, self.publishMidnight, offset)

    def publishMidnight(self, midnight_offset):
        self.call_on_midnight_offset(datetime.now(tzlocal()), midnight_offset)  # setup the new trigger for tomorrow.
        tz_names = self.tz_groups[midnight_offset]
        tz_name = random.choice(tz_names)
        city = create_city_name(tz_name)
        self.tz_groups = create_midnight_groups()  # Catch changes due to Daylight saving.

        def _logFailure(failure):
            self.log.debug("reported {message}", message=failure.getErrorMessage())
            return failure

        def _logAll(*args):
            self.log.debug("all publishing complete args={args!r}", args=args)

        msg = TextTripleLinesLayout()
        msg.duration = self.config['MIDNIGHT_DISPLAY_DURATION']
        msg.program = 'midnight'
        msg.lines = ['Midnight in', city, ""]
        msg.valid_time = self.config["MIDNIGHT_SHOW_VALIDITY"]
        d = self.publish(topic=LEDSLIE_TOPIC_TYPESETTER_3LINES, message=msg, qos=1)
        d.addCallbacks(_logAll, _logFailure)
        return d


if __name__ == '__main__':
    ns = __file__.split(os.sep)[-1]
    Config(envvar_silent=False)
    CreateContent(MidnightContent)
    reactor.run()
