from ledslie.messages import Frame
from ledslie.processors.intermezzos import IntermezzoInvaders

def test_IntermezzoInvaders():
    prev_frame = Frame(bytearray([0x66]*144*24), 100)
    next_frame = Frame(bytearray([0x66]*144*24), 100)
    seq = IntermezzoInvaders(prev_frame, next_frame)
