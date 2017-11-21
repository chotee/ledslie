from collections import deque

import msgpack

from twisted.logger import Logger
log = Logger()


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
    def __init__(self, config):
        self.config = config
        self.program = None
        self.sequence = deque()

    def load(self, payload):
        seq_images, seq_info = msgpack.unpackb(payload)
        self.program = seq_info.get(b'program', None)
        for image_data, image_info in seq_images:
            if len(image_data) != self.config.get('DISPLAY_SIZE'):
                log.error("Images are of the wrong size. Ignoring.")
                return
            try:
                image_duration = image_info.get(b'duration', self.config['DISPLAY_DEFAULT_DELAY'])
            except KeyError:
                break
            self.sequence.append(Image(image_data, duration=image_duration))
        return self

    def __bytes__(self):
        fields = ['program']
        seq_info = dict([(k, v) for k, v in self.__dict__.items() if k in fields and v is not None])
        images = [(idata, iinfo) for idata, iinfo in self.sequence]
        return msgpack.packb((images, seq_info))

    @property
    def duration(self):
        return sum([i.duration for i in self.sequence])

    def next_frame(self):
        return self.sequence.popleft()


class GenericTextLayout(GenericMessage):
    def __init__(self):
        self.program = None
        self.duration = None

    def load(self, payload):
        obj_data = msgpack.unpackb(payload)
        self.duration = obj_data.get(b'duration', None)
        self.program = obj_data.get(b'program', None)
        return obj_data


class TextSingleLineLayout(GenericTextLayout):
    def __init__(self):
        super().__init__()
        self.text = ""

    def load(self, payload):
        obj_data = super(TextSingleLineLayout, self).load(payload)
        self.text = obj_data.get(b'text', b"").decode()
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
