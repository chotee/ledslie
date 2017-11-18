#!/usr/bin/env python3
"""
    Ledslie, a community information display
    Copyright (C) 2017  Chotee@openended.eu

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

============

I decide what information is to be shown on the screen. I do this by keeping track of animations and messages are
available for displaying.

Messages are send to topic «ledslie/sequences/1/» + «name». Where «name» is the name of the sequence to display. For
each name only the last sequence is retained. THis allows producers to provide updated information.

An image is simply a sequence of one frame
"""

from twisted.internet import reactor
from twisted.logger import Logger

# Global object to control globally namespace logging
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES, LEDSLIE_TOPIC_SERIALIZER
from ledslie.processors.messages import ImageSequence
from ledslie.processors.service import CreateService, GenericMQTTPubSubService
# ----------------
# Global variables
# ----------------

log = Logger()

class Catalog(object):
    def __init__(self):
        self.sequences = {}
        self.active_program = None

    def has_content(self):
        return bool(self.sequences)

    def is_empty(self):
        return not self.has_content()

    def select_active_program(self):
        self.active_program = self.sequences[None]

    def remove_program(self, program):
        del self.sequences[None]

    def next_frame(self):
        if self.active_program is None:
            self.select_active_program()
        try:
            return self.active_program.next_frame()
        except IndexError:
            self.remove_program(self.active_program)
            self.active_program = None
            self.select_active_program()
            self.next_frame()

    def add_sequence(self, program_id, seq):
        self.sequences[program_id] = seq


class Scheduler(GenericMQTTPubSubService):
    subscriptions = (
        (LEDSLIE_TOPIC_SEQUENCES, 1),
    )

    def __init__(self, endpoint, factory, config):
        super().__init__(endpoint, factory, config)
        self.catalog = Catalog()
        self.sequencer = None

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("onPublish topic={topic}, msg={payload}", payload=payload, topic=topic)
        program_id = self.get_program_id(topic)
        seq = ImageSequence(self.config).load(payload)
        if seq is None:
            return
        self.catalog.add_sequence(program_id, seq)
        if self.sequencer is None:
            self.sequencer = self.reactor.callLater(0, self.send_next_frame)

    def get_program_id(self, topic):
        program_id = None
        # if topic != LEDSLIE_TOPIC_SEQUENCES:
        #     program_id = topic.split('/')[-1]
        return program_id

    def send_next_frame(self):
        try:
            frame = self.catalog.next_frame()
        except KeyError:
            return
        self.publish_frame(frame)
        self.sequencer = self.reactor.callLater(frame.duration, self.send_next_frame)

    def publish_frame(self, frame):
        d1 = self.protocol.publish(topic=LEDSLIE_TOPIC_SERIALIZER, message=bytes(frame))
        d1.addErrback(self._logPublishFailure)
        return d1


if __name__ == '__main__':
    log = CreateService(Scheduler)
    reactor.run()
