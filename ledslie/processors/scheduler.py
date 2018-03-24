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
from typing import Iterable

from ledslie.config import Config
from ledslie.content.utils import CircularBuffer
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, LEDSLIE_TOPIC_SEQUENCES_UNNAMED, \
    LEDSLIE_TOPIC_SERIALIZER, ALERT_PRIO_STRING
from ledslie.messages import FrameSequence, Frame
from ledslie.processors.animate import AnimateStill
from ledslie.processors.service import CreateService, GenericProcessor

# ----------------
# Global variables
# ----------------

log = Logger()


def IntermezzoWipe(previous_frame: Frame, next_frame: Frame):
    config = Config()
    prv = previous_frame.raw()
    nxt = next_frame.raw()
    seq = FrameSequence()
    height = config['DISPLAY_HEIGHT']
    width = config['DISPLAY_WIDTH']
    sep = bytearray([0x00, 0xff, 0x80, 0xff, 0x00])
    sep_len = len(sep)
    for step in range(2, width, 2):
        img_data = bytearray()
        for row in range(0, height):
            start = width*row
            img_data.extend(nxt[start:start+step] + sep + prv[start+step+sep_len:start+width])
        seq.add_frame(Frame(img_data, 20))
    return seq


class Catalog(object):
    def __init__(self):
        self.config = Config()
        self.programs = CircularBuffer()
        self.program_name_ids = {}  # Dict with names and Ids.
        self.program_retirement = {}
        self.alert_program = None
        self.intermezzo_func = None

    def add_intermezzo(self, intermezzo_func):
        self.intermezzo_func = intermezzo_func

    def now(self) -> float:
        return time.time()

    def has_content(self) -> bool:
        return len(self.programs) > 0

    def is_empty(self) -> bool:
        return not self.has_content()

    def frames_iter(self) -> Iterable:
        """
        I return the next frame.

        :return: The frame to display
        :rtype: Frame
        """
        prev_program = None
        while True:
            current_program = next(self.programs)
            if prev_program and self.intermezzo_func:
                intermezzo = self.intermezzo_func(prev_program.last(), current_program.first())
                if intermezzo:
                    yield from intermezzo
            if self.now() > self.program_retirement[current_program.program_id]:
                self.programs.remove(current_program)
            yield from current_program.frames
            prev_program = current_program


    def add_program(self, program_name: str, seq: FrameSequence):
        """
        I add a program to the catalog.
        :param program_id: The id of the program
        :type program_id: str
        :param seq: The sequence to add to the catalog
        :type seq: FrameSequence
        """
        assert isinstance(seq, FrameSequence), "Program is not a ImageSequence but: %s" % seq

        if program_name not in self.program_name_ids:
            program_id = self.programs.add(seq)
            self.program_name_ids[program_name] = program_id
        else:
            program_id = self.program_name_ids[program_name]
            self.programs.update(program_id, seq)
        seq.program_id = program_id
        self.program_retirement[program_id] = seq.retirement_age + self.now()

    def remove_program(self, program_name: str) -> None:
        program_id = self.program_name_ids[program_name]
        del self.program_name_ids[program_name]
        self.programs.remove_by_id(program_id)


class Scheduler(GenericProcessor):
    subscriptions = (
        (LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, 1),
        (LEDSLIE_TOPIC_SEQUENCES_UNNAMED, 1),
    )

    def __init__(self, endpoint, factory):
        super().__init__(endpoint, factory)
        self.catalog = Catalog()
        self.sequencer = None
        self.frame_iterator = None

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("onPublish topic={topic}, msg={payload}", payload=payload, topic=topic)
        program_name = self.get_program_id(topic)
        seq = FrameSequence().load(payload)
        if seq is None:
            return
        if len(seq) == 1:
            seq = AnimateStill(seq[0])
        self.catalog.add_program(program_name, seq)
        if self.sequencer is None:
            self.sequencer = self.reactor.callLater(0, self.send_next_frame)

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
