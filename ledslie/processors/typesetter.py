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
    LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT, LEDSLIE_TOPIC_TYPESETTER_1LINE, LEDSLIE_TOPIC_TYPESETTER_3LINES
from ledslie.messages import TextSingleLineLayout, TextTripleLinesLayout, ImageSequence
from ledslie.processors.service import GenericMQTTPubSubService, CreateService

log = Logger(__file__)

SCRIPT_DIR = os.path.split(__file__)[0]
os.chdir(SCRIPT_DIR)

class Typesetter(GenericMQTTPubSubService):
    subscriptions = (
        (LEDSLIE_TOPIC_TYPESETTER_1LINE, 1),
        (LEDSLIE_TOPIC_TYPESETTER_3LINES, 1),
        (LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT, 1),
    )

    def __init__(self, endpoint, factory):
        super().__init__(endpoint, factory)
        self.sequencer = None

    def onPublish(self, topic, payload, qos, dup, retain, msgId):
        '''
        Callback Receiving messages from publisher
        '''
        log.debug("onPublish topic={topic};q={qos}, msg={payload}", payload=payload, qos=qos, topic=topic)
        program = None
        if topic == LEDSLIE_TOPIC_TYPESETTER_SIMPLE_TEXT:
            image_bytes = self.typeset_1line(payload[:30]).tobytes()
            duration = DISPLAY_DEFAULT_DELAY
        else:
            if topic == LEDSLIE_TOPIC_TYPESETTER_1LINE:
                msg = TextSingleLineLayout().load(payload)
                image_bytes = self.typeset_1line(msg.text).tobytes()
            elif topic == LEDSLIE_TOPIC_TYPESETTER_3LINES:
                msg = TextTripleLinesLayout().load(payload)
                image_bytes = self.typeset_3lines(msg.lines).tobytes()
            else:
                raise NotImplementedError("topic '%s' (%s) is not known" % (topic, type(topic)))
            duration = msg.duration
            program = msg.program
        if image_bytes is None:
            return
        seq_msg = ImageSequence()
        seq_msg.program = program
        seq_msg.sequence.append((image_bytes, {'duration': duration}))
        self.send_image(seq_msg)

    def send_image(self, image_data):
        data = bytes(image_data)
        if image_data.program is None:
            topic = LEDSLIE_TOPIC_SEQUENCES_UNNAMED
        else:
            topic = LEDSLIE_TOPIC_SEQUENCES_PROGRAMS[:-1] + image_data.program
        self.publish(topic, data)

    def typeset_1line(self, msg):
        image = Image.new("L", (self.config.get("DISPLAY_WIDTH"),
                                self.config.get("DISPLAY_HEIGHT")))
        draw = ImageDraw.Draw(image)
        fontFileName = "DroidSansMono.ttf"
        font_path = self._get_font_filepath(fontFileName)
        try:
            font = ImageFont.truetype(font_path, 20)
        except OSError as exc:
            print("Can't find the font file '%s': %s" % (font_path, exc))
            return None
        draw.text((0, 0), msg, 255, font=font)
        return image

    def typeset_3lines(self, lines):
        image = Image.new("L", (144, 24))
        draw = ImageDraw.Draw(image)
        fontFileName = "DroidSansMono.ttf"
        font_path = self._get_font_filepath(fontFileName)
        try:
            font = ImageFont.truetype(font_path, 9)
        except OSError as exc:
            print("Can't find the font file '%s': %s" % (font_path, exc))
            return None
        for i, msg in enumerate(lines):
            draw.text((0, (i*8)-2), msg, (255), font=font)
        return image

    def _get_font_filepath(self, fontFileName):
        return os.path.realpath(os.path.join(self.config["FONT_DIRECTORY"], fontFileName))


# if __name__ == '__main__':
#     if len(sys.argv) == 3 and sys.argv[1] == 'show':
#         show_text = sys.argv[2].split(',')
#         img = typeset_3lines(show_text)
#         if img:
#             img.show()
#         else:
#             print("No image was generated.")
#     else:
#         main()

if __name__ == '__main__':
    log = Logger(__file__)
    Config(envvar_silent=False)
    CreateService(Typesetter)
    reactor.run()
