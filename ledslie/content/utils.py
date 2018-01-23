# Ledslie, a community information display
# Copyright (C) 2017-18  Chotee@openended.eu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class CircularBuffer(object):
    """
    I am a buffer with entries that you can always call next() for a new entry. Once the entries are exhausted, the
    first will returned again.
    """
    def __init__(self, elements=None):
        self._elems = [x for x in elements] if elements else []
        self._curr = -1

    def add(self, element: object):
        """
        I add an element to the buffer. I also make sure that the next call of next() will return the last element
        added.
        :param element: The object to add to the buffer
        :type element: object
        """
        self._elems.insert(self._curr+1, element)

    def remove(self, value: object):
        """
        Remove value from the buffer.
        :param value: The value to remove
        :type value: object
        """
        i = self._elems.index(value)
        if self._curr >= i:
            self._curr -= 1
        self._elems.pop(i)

    def next(self):
        """
        I return a single entry in the buffer.
        :return: An entry in the buffer.
        :rtype: object
        """
        self._curr += 1
        try:
            return self._elems[self._curr]
        except IndexError:
            self._curr = 0
            return self._elems[self._curr]

    def __len__(self):
        return len(self._elems)
