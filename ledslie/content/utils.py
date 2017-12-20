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
