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

class GenericFont(dict):
    def __init__(self, width, height, characters):
        """
        I'm a generic representation of a Bit Font for led display.

        :param width: Number of bits/LEDs that the font is wide
        :type width: int
        :param height: Number of bits/LEDs that the font is tall
        :type height: int
        :param characters: Dict with the font characters. THe key is the Unicode number and value a list with one entry
        per row.
        :type characters: dict
        """
        super().__init__(characters)
        self.width = width
        self.height = height
