import itertools

class Board(object):
    """Board - represent a board of stated dimensions,
    possibly infinite, possibly wrapping, but not both
    
    A location on the board is represented as an n-dimensional
    coordinate, matching the dimensionality originally specified.
    
    The board is addressed by index with a coordinate:
    
    b = Board((4, 4))
    b[2, 2] = "*"
    print(b[2, 2])
    
    NB All public methods take a local coordinate, including the implicit
    dunder methods; all other methods are assumed local unless suffixed with _g
    """
    
    def __init__(self, dimension_sizes, _global_board=None, _offset_from_global=None):
        """Set up a n-dimensional board
        """
        self.dimensions = [list(range(size or 0)) for size in dimension_sizes]

        #
        # This can be a sub-board of another board: a slice.
        # If that's the case, the boards share a common data structure
        # and this one is offset from the other. 
        # NB this means that if a slice is taken of a slice, the offset must itself be offset!
        #
        self._data = _global_board or {}
        self._offset_from_global = _offset_from_global or tuple(0 for _ in self.dimensions)
        self._gdimensions = [[self._to_global(c) for c in dimension] for dimension in self.dimensions]

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, tuple(len(d) for d in self.dimensions))
        
    def _is_in_bounds(self, coord):
        return all(not d or c in d for (c, d) in zip(coord, self.dimensions))
    
    def _is_in_bounds_g(self, coord):
        return all(not d or c in d for (c, d) in zip(coord, self._gdimensions))
    
    def __contains__(self, coord):
        return self._is_in_bounds(coord)

    def __iter__(self):
        return itertools.product(*(d if d else itertools.count() for d in self.dimensions))

    def _to_global(self, coord):
        return tuple(c - o for (c, o) in zip(coord, self._offset_from_global))

    def _from_global(self, coord):
        return tuple(c + o for (c, o) in zip(coord, self._offset_from_global))

    def _iterate(self, only_used=True):
        """Generate the list of local coordinates
        """
        if only_used:
            for coord in self._data:
                if self._is_in_bounds_g(coord):
                    yield coord
        else:
            for coord in self:
                yield coord

    def _iterate_g(self, only_used=True):
        """Generate the list of global coordinates which fit inside our space, 
        optionally limiting to those which have some data attached.
        """
        for coord in self._iterate(only_used=only_used):
            yield self._to_global(coord)

    def copy(self, with_data=True):
        board = self.__class__(tuple(len(d) for d in self.dimensions))
        if with_data:
            for coord in self._iterate():
                board._data[coord] = self._data[coord]
        return board

    def clear(self):
        """Clear the data which belongs to this board, possibly a sub-board
        of a larger board
        """
        for coord in list(self._iterate_global(only_used=True)):
            del self._data[coord]

    def __getitem__(self, item):
        """The item is either a tuple of numbers, representing a single
        coordinate on the board, or a tuple of slices representing a copy 
        of some or all of the board.
        """
        print("coord:", item)
        if all(isinstance(i, int) for i in item):
            coord = self._normalised_coord(item)
            return self._data.get(coord)
        else:
            return self._slice(item)
    
    def __setitem__(self, coord, value):
        coord = self._normalised_coord(coord)
        self._data[coord] = value

    def __delitem__(self, coord):
        coord = self._normalised_coord(coord)
        try:
            del self._data[coord]
        except KeyError:
            pass

    def _normalised_coord(self, coord):
        """Given a coordinate, check whether it's the right dimensionality
        for this board and whether it's within bounds. Return the underlying
        global coordinate.
        """
        if len(coord) != len(self.dimensions):
            raise IndexError("Coordinate %s has %d dimensions; the board has %d" % (coord, len(coord), len(self.dimensions)))

        #
        # Account for negative indices in the usual way
        #
        coord = [len(d) + c if c < 0 else c for c, d in zip(coord, self.dimensions)]

        if not self._is_in_bounds(coord):
            raise IndexError("Coordinate %s is out-of-bounds" % (coord,))

        return self._to_global(coord)

    def _slice(self, slices):
        """Produce a subset of this board, possibly of fewer dimensions,
        linked to the same underlying data.
        """
        if len(slices) != len(self.dimensions):
            raise IndexError("Slices %s have %d dimensions; the board has %d" % (slices, len(slices), len(self.dimensions)))
        
        #
        # Determine the start/stop/step for all the slices
        #
        slices = [slice.indices(len(dimension)) for (slice, dimension) in zip(slices, self.dimensions)]
        if any(abs(step) != 1 for start, stop, step in slices):
            raise IndexError("At least one of slices %s has a stride other than 1" % slices)
        
        sizes = tuple(stop - start + 1 for start, stop, step in slices)
        offset = tuple(start for start, stop, step in slices)
        return self.__class__(sizes, self._data, offset)
            
    def occupied(self):
        """(Apparently) return the bounding box of space occupied
        """
        minmax = [[float('inf'), float('-inf')]] * self.num_dimensions

        for key in self._data.iterkeys():
            for i, dim in enumerate(key):
                if dim < minmax[i][0]:
                    minmax[i][0] = dim

                if dim > minmax[i][1]:
                    minmax[i][1] = dim

        return minmax

    def neighbours(self, coord):
        """For a given coordinate, return a dictionary of its nearest
        neighbours along all coordinates, mapping each coordinate to
        its value.
        """
        coord = self._normalised_coord(coord)

        mins = [x - 1 for x in coord]
        maxs = [x + 1 for x in coord]

        coords = set(c for c in itertools.product(*zip(mins, coord, maxs)) if self._is_in_bounds(c))
        coords.remove(coord)

        return dict((c, self[c]) for c in coords)

if __name__ == '__main__':
    pass
