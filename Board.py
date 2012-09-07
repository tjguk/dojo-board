import os, sys
from collections import namedtuple

class Coord(object):

    def __init__(self, x, y):
        self._coord = x, y

    def __str__ (self):
        return str (self._coord)

    def __repr__ (self):
        return "<%s: %s>" % (self.__class__.__name__, self)

    def __hash__(self):
        return hash(self._coord)

    @classmethod
    def from_iterable(cls, iterable):
        return cls(*iterable)

    @classmethod
    def from_string(cls, string):
        letter, number = string.upper()
        x = ord(letter) - ord('A')
        y = int(number) - 1
        return cls(x, y)

    @classmethod
    def factory(cls, coord):
        if isinstance(coord, cls):
            return coord
        elif isinstance(coord, basestring):
            return cls.from_string(coord)
        else:
            return cls.from_iterable(coord)

    def __eq__(self, other):
        other = self.__class__.factory(other)
        return self._coord == other._coord

    def __add__(self, other):
        other = self.__class__.factory(other)
        x, y = self._coord
        dx, dy = other._coord
        return self.__class__(x + dx, y + dy)

    def __iadd__(self, other):
        x, y = self._coord
        dx, dy = other._coord
        self._coord[0] += other._coord[0]
        self._coord[1] += other._coord[1]
        return self

    def _get_x(self):
        return self._coord[0]
    def _set_x(self):
        self._coord[0] = x
    x = property(_get_x, _set_x)

    def _get_y(self):
        return self._coord[1]
    def _set_y(self):
        self._coord[1] = y
    y = property(_get_y, _set_y)

    def as_string(self):
        return "%s%s" % (chr(self.x + ord("A")), 1 + self.y)

    def neighbours(self):
        x, y = self._coord
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (dx, dy) != (0, 0):
                    yield self.__class__(x + dx, y + dy)

class Board(object):

    class OutOfBoundsError(Exception): pass
    class OverlapError(Exception): pass

    def __init__(self, width, height):
        #
        # _board tracks which coordinates have something at them
        #
        self._board = {}
        #
        # _items tracks items with their coordinates
        #
        self._items = {}

        self._width = set(range(width))
        self._height = set(range(height))

    def __repr__(self):
        return "<%s: %s x %s>" % (self.__class__.__name__, len(self._width), len(self._height))

    def __getitem__(self, item_coord):
        item_coord = Coord.factory(item_coord)
        return self._board.get(item_coord)

    def __contains__(self, coord):
        return Coord.factory(coord) in self._board

    def _validate_coord(self, coord):
        x, y = coord
        if not (x in self._width and y in self._height):
            raise self.OutOfBoundsError("Coord %s falls outside %r" % (coord, self))

    def place_item(self, item, item_coords):
        for coord in item_coords:
            self._validate_coord(coord)
            if coord in self._board:
                raise self.OverlapError("Coord %s is already occupied by %s" % (coord, self._board[coord]))
            self._board[coord] = item
        self._items[item] = item_coords

    def neighbours(self, coord):
        return set(Coord.factory(coord).neighbours()) & set(itertools.product(self._width, self._height))
