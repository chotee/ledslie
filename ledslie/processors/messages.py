from collections import deque

import msgpack

from twisted.logger import Logger
log = Logger()


class GenericMessage(object):
    def load(self):
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
        self.sequence = deque()

    def load(self, payload):
        seq_data = msgpack.unpackb(payload)
        for image_data, image_info in seq_data:
            if len(image_data) != self.config.get('DISPLAY_SIZE'):
                log.error("Images are of the wrong size. Ignoring.")
                return
            try:
                image_duration = image_info.get(b'duration', self.config['DISPLAY_DEFAULT_DELAY'])
            except KeyError:
                break
            self.sequence.append(Image(image_data, duration=image_duration))
        return self

    @property
    def duration(self):
        return sum([i.duration for i in self.sequence])

    def next_frame(self):
        return self.sequence.popleft()


class GenericTextLayout(GenericMessage):
    def __init__(self):
        self.program = None


class TextSingleLineLayout(GenericTextLayout):
    def __init__(self):
        super().__init__()
        self.text = ""