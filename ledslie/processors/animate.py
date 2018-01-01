#!/usr/bin/env python
#     Ledslie, a community information display
#     Copyright (C) 2017-18  Chotee@openended.eu
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as published
#     by the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ===========
#
# Animation routines.

from ledslie.config import Config
from ledslie.messages import FrameSequence, Frame


def AnimateStill(still: Frame):
    """
    I take a frame and create a sequence where the duration of the frame is visible.
    :param still: The image to animate.
    :type still: Frame
    :return: The sequence of frames with the time animation.
    :rtype: FrameSequence
    """
    seq = FrameSequence()
    width, height = Config().get('DISPLAY_WIDTH'), Config().get('DISPLAY_HEIGHT')
    seq_duration = still.duration
    steps_ms = int(seq_duration / height)
    still_img = still.raw()
    still.duration = steps_ms
    for nr in range(height):
        frame = bytearray(still_img)
        frame[width*nr-1] = 0xff
        seq.add_frame(Frame(bytes(frame), steps_ms))
    seq[-1].duration += seq_duration - seq.duration  # Add the steps_ms missing because of the division.
    return seq


def AnimateVerticalScroll(image: bytearray, line_duration: int) -> list:
    """
    I let the content of a longer image scroll vertically up.
    :param image: The image that there is to scroll.
    :type image: bytearray
    :param line_duration: The duration in ms that each line should be shown.
    :type line_duration: int
    :return: List of frames that make up the scrolling motion.
    :rtype: list
    """
    config = Config()
    display_width = config['DISPLAY_WIDTH']
    animate_duration = config['TYPESETTER_ANIMATE_VERTICAL_SCROLL_DELAY']
    nr_of_lines = len(image) / display_width  # nr of lines does the whole image has.
    nr_of_scroll = int(nr_of_lines - config['DISPLAY_HEIGHT'])  # number of lines there are to scroll
    f_start = 0
    f_end = config['DISPLAY_SIZE']
    frames = []
    for nr in range(nr_of_scroll):
        if nr % 8 == 0:  # On a full line, show for longer.
            duration = line_duration
        else:
            duration = animate_duration
        frames.append(Frame(image[f_start:f_end], duration=duration))
        f_start += display_width
        f_end += display_width
    frames.append(Frame(image[-config['DISPLAY_SIZE']:], duration=line_duration))
    return frames
