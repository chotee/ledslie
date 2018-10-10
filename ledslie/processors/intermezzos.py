from ledslie.config import Config
from ledslie.gfx.invaders import invader3, invader2, invader1
from ledslie.gfx.pacman import Pacman1, Pacman2
from ledslie.messages import Frame, FrameSequence


def IntermezzoWipe(previous_frame: Frame, next_frame: Frame):
    config = Config()
    wipe_frame_delay = config['INTERMEZZO_WIPE_FRAME_DELAY']
    wipe_frame_step_size = config['INTERMEZZO_WIPE_FRAME_STEP_SIZE']
    prv = previous_frame.raw()
    nxt = next_frame.raw()
    seq = FrameSequence()
    height = config['DISPLAY_HEIGHT']
    width = config['DISPLAY_WIDTH']
    sep = bytearray([0x00, 0x00, 0x40, 0x60, 0x80, 0x80, 0xff, 0x00])
    sep_len = len(sep)
    for step in range(wipe_frame_step_size, width-wipe_frame_step_size-sep_len, wipe_frame_step_size):
        img_data = bytearray()
        for row in range(0, height):
            start = width*row
            img_data.extend(nxt[start:start+step] + sep + prv[start+step+sep_len:start+width])
        seq.add_frame(Frame(img_data, wipe_frame_delay))
    return seq


def IntermezzoPacman(previous_frame: Frame, next_frame: Frame):
    config = Config()
    frame_move  = config['PACMAN_MOVE']
    frame_delay = config['PACMAN_DELAY']
    prv = previous_frame.raw()
    nxt = next_frame.raw()
    seq = FrameSequence()
    height = config['DISPLAY_HEIGHT']
    width = config['DISPLAY_WIDTH']
    pacmans = [Pacman1, Pacman2]
    i = 0
    for step in range(width, 0, -1*frame_move):
        i += 1
        img_data = bytearray()
        for row_nr in range(height):
            prv_row = prv[row_nr*width:(row_nr+1)*width]
            nxt_row = nxt[row_nr*width:(row_nr+1)*width]
            try:
                img_data.extend((prv_row[:step] + pacmans[i%2][row_nr] + nxt_row)[:width])
            except IndexError:
                0/0
        seq.add_frame(Frame(img_data, frame_delay))
    return seq


def _invaders(step):
    i = step % 8
    reverse = int(step/8) % 2
    phase = step % 2
    if not reverse:
        vert = i
    else:
        vert = 8 - i
    ba = bytearray()
    for row in range(8):
        ba.extend([0x00]*(vert+4))
        for invader in [invader1, invader2, invader3, invader2, invader2, invader3, invader2, invader1]:
            ba.extend(invader[phase][row] + bytearray([0x00]*8))
        ba.extend([0x00]*(8-vert+4))
        assert len(ba) % 144 == 0, len(ba)
    return ba


def IntermezzoInvaders(previous_frame: Frame, next_frame: Frame):
    """
    Show Invaders from the top to the bottom switching programs.
    """
    config = Config()
    prv = previous_frame.raw()
    nxt = next_frame.raw()
    seq = FrameSequence()
    frame_delay = config['INVADERS_FRAME_DELAY']
    height = config['DISPLAY_HEIGHT']
    width = config['DISPLAY_WIDTH']
    size = height*width
    invader_height = int(len(_invaders(0)) / width)
    for step in range(height+invader_height+4):  # lets go from top to bottom
        img = bytearray().join([
            nxt,
            bytearray(width),  # Empty.
            bytearray(width),  # Empty.
            _invaders(step),
            bytearray(width),  # Empty.
            bytearray(width),  # Empty.
            prv
        ])
        if step == 0:
            frame_data = img[-1*size - (step*width):]
        else:
            frame_data = img[-1*size - (step*width):-(step*width)]
        seq.add_frame(Frame(frame_data, frame_delay))
    return seq
