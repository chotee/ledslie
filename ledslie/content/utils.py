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
        self._elems = []
        self._table = {}
        self._curr = -1
        self._id_counter = -1
        if elements:
            for element in reversed(elements):
                self.add(element)

    def add(self, element: object):
        """
        I add an element to the buffer. I also make sure that the next call of next() will return the last element
        added.
        :param element: The object to add to the buffer
        :type element: object
        """
        self._id_counter += 1
        e_obj = [element]  # Create a list object, so that we can update just the content of the first element.
        self._table[self._id_counter] = e_obj
        self._elems.insert(self._curr+1, e_obj)
        return self._id_counter

    def remove(self, value: object):
        """
        Remove value from the buffer.
        :param value: The value to remove
        :type value: object
        """
        # Remove from the list
        i = self._elems.index([value])
        if self._curr >= i:
            self._curr -= 1
        self._elems.pop(i)
        found = None

        # Remove from the Table
        for k, v in self._table.items():
            if v == value:
                found = k
                break
        if found:
            del self._table[k]

    def update(self, elem_id, new_value):
        self._table[elem_id][0] = new_value

    def next(self):
        """
        I return a single entry in the buffer.
        :return: An entry in the buffer.
        :rtype: object
        """
        self._curr += 1
        try:
            return self._elems[self._curr][0]
        except IndexError:
            self._curr = 0
            return self._elems[self._curr][0]

    def __len__(self):
        return len(self._elems)
