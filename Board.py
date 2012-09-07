import os, sys

class CoordBase(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __str__ (self):
        return str ((self.x, self.y))
    
    def __repr__ (self):
        return "<%s: %s>" % (self.__class__.__name__, self)
    
    def __hash__(self):
        return hash((self.x, self.y))
    
class Coord(CoordBase):
    
    @classmethod
    def from_iterable(cls, iterable):
        return cls(*iterable)
    
    @classmethod
    def from_string(cls, string):
        letter, number = string.upper()
        x = ord(letter) - ord('A')
        y = int(number) - 1
        return cls(x, y)
    
    def __eq__(self, other):
        other = coord(other)
        return self.x == other.x and self.y == other.y
        
    def __add__(self, other):
        return self.__class__(self.x + other.x, self.y + other.y)
        
    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self
    
    def as_string(self):
        return "%s%s" % (chr(self.x + ord("A")), 1 + self.y)

def CoordOffset(CoordBase):
    pass

def coord(coord):
    if isinstance(coord, Coord):
        return coord
    elif isinstance(coord, basestring):
        return Coord.from_string(coord)
    else:
        return Coord.from_iterable(coord)
        
class Board(object):
    
    class OutOfBoundsError(Exception): pass
    
    def __init__(self, width, height):
        self._board = {}
        self._width = range(width)
        self._height = range(height)

    def __getitem__(self, item_coord):
        item_coord = coord(item_coord)
        return self._board.get(item_coord)
