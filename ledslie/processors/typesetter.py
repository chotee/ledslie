#!/usr/bin/env python
"""
    Ledslie, a community information display
    Copyright (C) 2017  Chotee@openended.eu

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

===========

I take a message with text data and generate a frame representing that data.

TOPIC: ledslie.definitions.LEDSLIE_TOPIC_TYPESETTER:
MESSAGE STRUCTURE: MessagePack message.
  type = "1line" and content is on "text" variable.
OR
  type = "3lines" and content is in "lines" variable.

"""

# Start without arguments it's the typesetter
# Start with arguments "show 'hello world'" and it will show you how 'hello world' will be rendered.
import os

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from twisted.internet import reactor
from twisted.logger import Logger

from ledslie.config import Config
from ledslie.defaults import DISPLAY_DEFAULT_DELAY
from ledslie.definitions import LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, LEDSLIE_TOPIC_SEQUENCES_UNNAMED, \
    LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT, LEDSLIE_TOPIC_TYPESETTER_1LINE, LEDSLIE_TOPIC_TYPESETTER_3LINES, \
    LEDSLIE_TOPIC_ALERT
from ledslie.messages import TextSingleLineLayout, TextTripleLinesLayout, FrameSequence, TextAlertLayout, Frame
from ledslie.processors.font8x8 import font8x8
from ledslie.processors.service import GenericProcessor, CreateService

SCRIPT_DIR = os.path.split(__file__)[0]
os.chdir(SCRIPT_DIR)

class Typesetter(GenericProcessor):
    subscriptions = (
        (LEDSLIE_TOPIC_TYPESETTER_1LINE, 1),
        (LEDSLIE_TOPIC_TYPESETTER_3LINES, 1),
        (LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT, 1),
        (LEDSLIE_TOPIC_ALERT + "+", 1),
    )

    def __init__(self, endpoint, factory):
        self.log = Logger(__class__.__name__)
        super().__init__(endpoint, factory)
        self.sequencer = None

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        self.log.debug("onPublish topic={topic};q={qos}, msg={payload}", payload=payload, qos=qos, topic=topic)
        program = None
        if topic == LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT:
            font_size = self.config['TYPESETTER_1LINE_DEFAULT_FONT_SIZE']
            image_bytes = self.typeset_1line(payload[:30], font_size)
        elif topic == LEDSLIE_TOPIC_TYPESETTER_1LINE:
            msg = TextSingleLineLayout().load(payload)
            font_size = msg.font_size if msg.font_size is not None else self.config['TYPESETTER_1LINE_DEFAULT_FONT_SIZE']
            text = msg.text
            image_bytes = self.typeset_1line(text, font_size)
        elif topic == LEDSLIE_TOPIC_TYPESETTER_3LINES:
            msg = TextTripleLinesLayout().load(payload)
            image_bytes = self.typeset_3lines(msg.lines)
        elif topic.startswith(LEDSLIE_TOPIC_ALERT):
            msg = TextAlertLayout().load(payload)
            frame_seq = self.typeset_alert(topic, msg)
            frame_seq.program = "alert"
            return self.send_frame_sequence(frame_seq)
        else:
            raise NotImplementedError("topic '%s' (%s) is not known" % (topic, type(topic)))
        if image_bytes is None or "":
            return
        seq_msg = FrameSequence()
        seq_msg.program = msg.program
        seq_msg.valid_time = msg.valid_time
        seq_msg.frames.append((image_bytes, {'duration': msg.duration}))
        self.send_image(seq_msg)

    def send_image(self, image_data):
        if image_data.program is None:
            topic = LEDSLIE_TOPIC_SEQUENCES_UNNAMED
        else:
            topic = LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + image_data.program
        self.publish(topic, image_data)

    def send_frame_sequence(self, seq: FrameSequence):
        topic = LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + seq.program
        message = seq.serialize()
        return self.protocol.publish(topic, message, 1, retain=False)

    def typeset_1line(self, text: str, font_size: float):
        image = Image.new("L", (self.config.get("DISPLAY_WIDTH"),
                                self.config.get("DISPLAY_HEIGHT")))
        draw = ImageDraw.Draw(image)
        fontFileName = "DroidSansMono.ttf"
        font_path = self._get_font_filepath(fontFileName)
        try:
            font = ImageFont.truetype(font_path, font_size)
        except OSError as exc:
            print("Can't find the font file '%s': %s" % (font_path, exc))
            return None
        draw.text((0, 0), text, 255, font=font)
        return image.tobytes()

    def typeset_3lines(self, lines):
        display_width = self.config['DISPLAY_WIDTH']
        maxchars = self._char_display_width()
        image = bytearray()
        display_width_bytes = display_width * 8
        for line in lines:  # off all the lines
            line_image = bytearray(display_width_bytes)
            for j, c in enumerate(line[:maxchars]):  # Look at each character of a line
                try:
                    glyph = font8x8[ord(c)]
                except KeyError:
                    glyph = font8x8[ord("?")]
                xpos = j*8  # Horizontal Position in the line.
                for n, glyph_line in enumerate(glyph):  # Look at each row of the glyph (is just a byte)
                    for x in range(8):  # Look at the bits
                        if testBit(glyph_line, x) != 0:
                            line_image[xpos + n * display_width + x] = 0xff
            image.extend(line_image)
        return bytes(image)

    def _char_display_width(self):
        display_width = self.config['DISPLAY_WIDTH']
        return int(display_width / 8)

    def _get_font_filepath(self, fontFileName):
        return os.path.realpath(os.path.join(self.config["FONT_DIRECTORY"], fontFileName))

    def typeset_alert(self, topic: str, msg: TextAlertLayout) -> FrameSequence:
        assert topic.split('/')[-1] == "spacealert"
        display_size = self.config['DISPLAY_SIZE']
        text = msg.text
        who = msg.who
        fs = FrameSequence()
        char_width = self._char_display_width()
        fs.program = msg.program
        alert = self.typeset_1line("Space Alert!", 20)
        alert_neg = bytes([(~x & 0xff) for x in alert])
        fs.add_frame(Frame(alert, duration=200))
        fs.add_frame(Frame(alert_neg, duration=200))
        fs.add_frame(Frame(alert, duration=200))
        fs.add_frame(Frame(alert_neg, duration=200))
        lines = ["From %s" % who, text[:char_width], text[char_width:]]
        fs.add_frame(Frame(self.typeset_3lines(lines), duration=2000))
        fs.prio = "alert"
        return fs


def testBit(int_type, offset):
    mask = 1 << offset
    return (int_type & mask)


if __name__ == '__main__':
    Config(envvar_silent=False)
    CreateService(Typesetter)
    reactor.run()
