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
import json

from twisted.internet import reactor
from twisted.logger import Logger

from ledslie.config import Config
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, LEDSLIE_TOPIC_SEQUENCES_UNNAMED, \
    LEDSLIE_TOPIC_SERIALIZER, LEDSLIE_TOPIC_SCHEDULER_PROGRAMS
from ledslie.messages import FrameSequence
from ledslie.processors.animate import AnimateStill
from ledslie.processors.catalog import Catalog
from ledslie.processors.intermezzos import IntermezzoWipe
from ledslie.processors.service import CreateService, GenericProcessor

# ----------------
# Global variables
# ----------------

log = Logger()


class Scheduler(GenericProcessor):
    subscriptions = (
        (LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, 1),
        (LEDSLIE_TOPIC_SEQUENCES_UNNAMED, 1),
    )

    def __init__(self, endpoint, factory):
        super().__init__(endpoint, factory)
        self.catalog = Catalog()
        self.catalog.add_intermezzo(IntermezzoWipe)
        self.sequencer = None
        self.frame_iterator = None

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("onPublish topic={topic}, msg={payload}", payload=payload, topic=topic)
        program_name = self.get_program_id(topic)
        if not payload:  # remove programs when the payload is empty.
            if program_name in self.catalog:
                self.catalog.remove_program(program_name)
            return
        seq = FrameSequence().load(payload)
        if seq is None:
            return
        if len(seq) == 1:
            seq = AnimateStill(seq[0])
        self.catalog.add_program(program_name, seq)
        if self.sequencer is None:
            self.sequencer = self.reactor.callLater(0, self.send_next_frame)
        content = json.dumps(self.catalog.list_current_programs()).encode()
        self.protocol.publish(LEDSLIE_TOPIC_SCHEDULER_PROGRAMS, content, 0, retain=False)

    def get_program_id(self, topic):
        if topic == LEDSLIE_TOPIC_SEQUENCES_UNNAMED:
            program_id = None
        else:
            program_id = topic.split('/')[-1]
        return program_id

    def send_next_frame(self):
        if self.frame_iterator is None:
            self.frame_iterator = self.catalog.frames_iter()
        try:
            frame = next(self.frame_iterator)
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
