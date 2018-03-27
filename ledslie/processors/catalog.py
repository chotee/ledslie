import time
from typing import Iterable

from ledslie.config import Config
from ledslie.content.utils import CircularBuffer
from ledslie.messages import FrameSequence


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
        self.programs.remove_by_id(program_id)
        del self.program_name_ids[program_name]

    def __contains__(self, program_name: str) -> bool:
        """
        Return true if the catalog contains a program of program_name
        :param program_name: The name of the program
        :type program_name: str
        :return: True if the program was found. False otherwise.
        :rtype: bool
        """
        return program_name in self.program_name_ids
