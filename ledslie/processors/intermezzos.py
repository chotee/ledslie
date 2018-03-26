from ledslie.config import Config
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
    sep = bytearray([0x00, 0xff, 0x80, 0xff, 0x00])
    sep_len = len(sep)
    for step in range(wipe_frame_step_size, width, wipe_frame_step_size):
        img_data = bytearray()
        for row in range(0, height):
            start = width*row
            img_data.extend(nxt[start:start+step] + sep + prv[start+step+sep_len:start+width])
        seq.add_frame(Frame(img_data, wipe_frame_delay))
    return seq