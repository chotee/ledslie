from collections import deque

import msgpack

from twisted.logger import Logger

from ledslie.config import Config

log = Logger()


def GetString(obj, key, default=None):
    b_value = obj.get(key, default)
    return b_value.decode() if b_value is not None else None


class GenericMessage(object):
    def load(self, obj_data):
        raise NotImplemented()

    def __bytes__(self):
        raise NotImplemented()


class Image(GenericMessage):
    def __init__(self, img_data, duration):
        self.img_data = img_data
        self.duration = duration

    def __bytes__(self):
        return self.img_data


class ImageSequence(GenericMessage):
    def __init__(self):
        self.sequence = []
        self.program = None
        self.frame_nr = -1

    def load(self, payload):
        config = Config()
        seq_images, seq_info = msgpack.unpackb(payload)
        self.program = GetString(seq_info, b'program')
        for image_data, image_info in seq_images:
            if len(image_data) != config.get('DISPLAY_SIZE'):
                log.error("Images are of the wrong size. Ignoring.")
                return
            try:
                image_duration = image_info.get(b'duration', config['DISPLAY_DEFAULT_DELAY'])
            except KeyError:
                break
            self.sequence.append(Image(image_data, duration=image_duration))
        return self

    def __bytes__(self):
        fields = []
        seq_info = dict([(k, v) for k, v in self.__dict__.items() if k in fields and v is not None])
        images = [(idata, iinfo) for idata, iinfo in self.sequence]
        return msgpack.packb((images, seq_info))

    @property
    def duration(self):
        return sum([i.duration for i in self.sequence])

    def next_frame(self):
        self.frame_nr += 1
        return self.sequence[self.frame_nr]


class GenericTextLayout(GenericMessage):
    def __init__(self):
        self.program = None
        self.duration = None

    def load(self, payload):
        obj_data = msgpack.unpackb(payload)
        self.duration = obj_data.get(b'duration', None)
        self.program = GetString(obj_data, b'program')
        return obj_data


class TextSingleLineLayout(GenericTextLayout):
    def __init__(self):
        super().__init__()
        self.text = ""

    def load(self, payload):
        obj_data = super(TextSingleLineLayout, self).load(payload)
        self.text = GetString(obj_data, b'text', "")
        return self

    def __bytes__(self):
        return msgpack.packb(self.__dict__)


class TextTripleLinesLayout(GenericTextLayout):
    def __init__(self):
        super().__init__()
        self.lines = []

    def load(self, payload):
        obj_data = super(TextTripleLinesLayout, self).load(payload)
        self.lines = [l.decode() for l in obj_data.get(b'lines', [])]
        return self

    def __bytes__(self):
        return msgpack.packb(self.__dict__)
