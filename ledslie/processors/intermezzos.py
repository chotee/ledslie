from ledslie.config import Config
from ledslie.gfx.invaders import invader3, invader2, invader1
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
            ba.extend(invader[phase][i] + bytearray([0x00]*8))
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
    frame_delay = 12
    height = config['DISPLAY_HEIGHT']
    width = config['DISPLAY_WIDTH']
    size = height*width
    invader_height = int(len(_invaders(0)) / width)
    for step in range(height+invader_height+2):  # lets go from top to bottom
        img = bytearray().join([
            nxt,
            bytearray(width),  # Empty.
            _invaders(step),
            bytearray(width),  # Empty.
            prv
        ])
        if step == 0:
            frame_data = img[-1*size - (step*width):]
        else:
            frame_data = img[-1*size - (step*width):-(step*width)]
        seq.add_frame(Frame(frame_data, frame_delay))
    return seq
