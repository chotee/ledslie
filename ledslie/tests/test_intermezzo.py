from ledslie.config import Config
from ledslie.messages import Frame
from ledslie.processors.intermezzos import IntermezzoWipe


class TestIntermezzo(object):
    def test_IntermezzoWipe(self):
        config = Config()
        image_size = config.get('DISPLAY_SIZE')
        prev_frame = Frame(bytearray(b'0' * image_size), 1)
        next_frame = Frame(bytearray(b'1' * image_size), 1)
        seq = IntermezzoWipe(prev_frame, next_frame)
        for frame in seq:
            assert image_size == len(frame.raw()), "Frame length relative to expected: %s" % (len(frame.raw())-image_size)