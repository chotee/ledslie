#!/usr/bin/env python3

#     Ledslie, a community information display
#     Copyright (C) 2017-18  Chotee@openended.eu
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as published
#     by the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ============
#
# I decide what information is to be shown on the screen. I do this by keeping track of animations and messages are
# available for displaying.
#
# Messages are send to topic «ledslie/sequences/1/» + «name». Where «name» is the name of the sequence to display. For
# each name only the last sequence is retained. THis allows producers to provide updated information.
#
# An image is simply a sequence of one frame

import time

from twisted.internet import reactor
from twisted.logger import Logger

from ledslie.config import Config
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, LEDSLIE_TOPIC_SEQUENCES_UNNAMED, \
    LEDSLIE_TOPIC_SERIALIZER, ALERT_PRIO_STRING
from ledslie.messages import FrameSequence
from ledslie.processors.animate import AnimateStill
from ledslie.processors.service import CreateService, GenericProcessor

# ----------------
# Global variables
# ----------------

log = Logger()


class Catalog(object):
    def __init__(self):
        self.config = Config()
        self.programs = {}
        self.active_program = None
        self.program_name_list = []  # list of keys that indicate the sequence of programs.
        self.active_program_name = None
        self.program_retirement = {}
        self.alert_program = None

    def now(self):
        return time.time()

    def has_content(self):
        return bool(self.programs)

    def is_empty(self):
        return not self.has_content()

    def select_next_program(self):
        if self.alert_program and self.alert_program.alert_count > 0:
            self.alert_program.alert_count -= 1
            self.active_program = self.alert_program
            self.active_program_name = ALERT_PRIO_STRING
        else:
            next_program_name = self._select_program()
            self.active_program = self.programs[next_program_name]
            self.active_program_name = next_program_name
        if self.now() > self.program_retirement[self.active_program_name]:
            self.remove_program(self.active_program_name)

    def _select_program(self):
        try:
            active_program_idx = self.program_name_list.index(self.active_program_name)
            next_program_name = self.program_name_list[active_program_idx + 1]
        except (ValueError, IndexError):
            next_program_name = self.program_name_list[0]
        return next_program_name

    def next_frame(self):
        if self.active_program is None:
            self.select_next_program()
        try:
            return self.active_program.next_frame()
        except IndexError:
            self.select_next_program()
            return self.next_frame()

    def add_program(self, program_id: str, seq: FrameSequence):
        assert isinstance(seq, FrameSequence), "Program is not a ImageSequence but: %s" % seq
        if program_id not in self.programs:
            self.program_name_list.append(program_id)
        self.programs[program_id] = seq
        default_retirement_age = self.config['PROGRAM_RETIREMENT_AGE']
        if seq.is_alert():
            self.alert_program = seq
            seq.alert_count = self.config['ALERT_INITIAL_REPEAT']
            seq.valid_time = self.config['ALERT_RETIREMENT_AGE']
        retirement_age = min(seq.valid_time, default_retirement_age) if seq.valid_time else default_retirement_age
        self.program_retirement[program_id] = self.now() + retirement_age

    def remove_program(self, program_id):
        del self.programs[program_id]
        del self.program_retirement[program_id]
        self.program_name_list.remove(program_id)


class Scheduler(GenericProcessor):
    subscriptions = (
        (LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, 1),
        (LEDSLIE_TOPIC_SEQUENCES_UNNAMED, 1),
    )

    def __init__(self, endpoint, factory):
        super().__init__(endpoint, factory)
        self.catalog = Catalog()
        self.sequencer = None

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("onPublish topic={topic}, msg={payload}", payload=payload, topic=topic)
        program_id = self.get_program_id(topic)
        seq = FrameSequence().load(payload)
        if seq is None:
            return
        if len(seq) == 1:
            seq = AnimateStill(seq[0])
        self.catalog.add_program(program_id, seq)
        if self.sequencer is None:
            self.sequencer = self.reactor.callLater(0, self.send_next_frame)

    def get_program_id(self, topic):
        if topic == LEDSLIE_TOPIC_SEQUENCES_UNNAMED:
            program_id = None
        else:
            program_id = topic.split('/')[-1]
        return program_id

    def send_next_frame(self):
        try:
            frame = self.catalog.next_frame()
        except KeyError:
            return
        self.publish_frame(frame)
        duration = min(10, frame.duration/1000)
        self.sequencer = self.reactor.callLater(duration, self.send_next_frame)

    def publish_frame(self, frame):
        # d = self.publish(topic=LEDSLIE_TOPIC_SERIALIZER, message=SerializeFrame(frame.raw()))
        d = self.publish(topic=LEDSLIE_TOPIC_SERIALIZER, message=frame.raw())
        d.addErrback(self._logPublishFailure)
        return d


if __name__ == '__main__':
    log = Logger(__file__)
    Config(envvar_silent=False)
    CreateService(Scheduler)
    reactor.run()
