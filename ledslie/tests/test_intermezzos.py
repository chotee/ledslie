from ledslie.config import Config
from ledslie.messages import Frame
from ledslie.processors.intermezzos import IntermezzoWipe, IntermezzoInvaders, _invaders, IntermezzoPacman


def verify_length(seq, image_size):
    f_nr = 0
    for frame in seq:
        assert image_size == len(frame.raw()), "Frame %d/%d: length relative to expected: %s" % (
        f_nr, len(seq), len(frame.raw()) - image_size)
        f_nr += 1


class TestIntermezzo(object):
    def test_IntermezzoWipe(self):
        config = Config()
        image_size = config.get('DISPLAY_SIZE')
        prev_frame = Frame(bytearray(b'0' * image_size), 1)
        next_frame = Frame(bytearray(b'1' * image_size), 1)
        seq = IntermezzoWipe(prev_frame, next_frame)
        verify_length(seq, image_size)

class TestIntermezzoInvaders:
    def test_fram_length(self):
        config = Config()
        image_size = config.get('DISPLAY_SIZE')
        prev_frame = Frame(bytearray([0x66]*image_size), 100)
        next_frame = Frame(bytearray([0x66]*image_size), 100)
        seq = IntermezzoInvaders(prev_frame, next_frame)
        verify_length(seq, image_size)

    def test_invaders(self):
        config = Config()
        width = config['DISPLAY_WIDTH']
        height = config['DISPLAY_HEIGHT']
        for s in range(height*2+2):
            s = _invaders(0)
            assert len(s) % width == 0, "Should be a multiple of %d, but %d bytes left." % (width, len(s) % width)


class TestIntermezzoPacman:
    def test_pacman(self):
        config = Config()
        image_size = config.get('DISPLAY_SIZE')
        prev_frame = Frame(bytearray(b'0' * image_size), 1)
        next_frame = Frame(bytearray(b'1' * image_size), 1)
        seq = IntermezzoPacman(prev_frame, next_frame)
        verify_length(seq, image_size)
