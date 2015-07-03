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
    """
    
    def __init__(self, dimension_sizes, _global_board=None, _from_global_function=None, _to_global_function=None):
        """Set up a n-dimensional board
        """
        self.dimensions = [list(range(size or 0)) for size in dimension_sizes]

        #
        # This can be a sub-board of another board: a slice.
        # If that's the case, the boards share a common data structure
        # and this one is offset from the other, possibly with fewer dimensions. 
        # NB this means that if a slice is taken of a slice, the offset must itself be offset!
        #
        self._data = _global_board or {}
        self._to_global_function = _to_global_function or lambda coord: coord
        self._from_global_function = _from_global_function or lambda coord: coord

    def _is_in_bounds(self, coord):
        return all(d is None or c in d for (c, d) in zip(coord, self.dimensions))
    
    def _local_to_global(self, coord):
        return tuple(c + o for (c, o) in zip(coord, self._offset))

    def _global_to_local(self, coord):
        return tuple(c - o for (c, o) in zip(coord, self._offset))
    
    def _iterate_global(self, only_used=True):
        """Generate the list of global coordinates, optionally limiting
        to those which have some data attached.
        """
        if only_used:
            for coord in self._data:
                local_coord = self._global_to_local(coord)
                if _is_in_bounds(local_coord):
                    yield coord
        else:
            for coord in itertools.product(itertools.count(len(dimension)) for dimension in self.dimensions)
                

    def clear(self):
        """Clear the data which belongs to this board, possible a sub-board
        of a larger board
        """
        self._data.clear()

    def __getitem__(self, loc):
        loc = self._bounds_check(loc)

        try:
            return self._data[loc]
        except KeyError:
            return None

    def __setitem__(self, loc, val):
        loc = self._bounds_check(loc)

        self._data[loc] = val

    def __delitem__(self, coord):
        loc = self._normalise_coordinate(loc)

        try:
            del self._data[loc]
        except KeyError:
            pass

    def _normalise_coordinate(self, coord):
        """Given a coordinate, check whether it's the right dimensionality
        for this board and whether it's within bounds. Return the underlying
        coordinate, allowing for offset.
        
        This is expected to be overridden by a Wrapping subclass.
        
        Return a coordinate
        """
        if len(coord) != len(self.dimensions):
            raise IndexError("Coordinate %s has %d dimensions; the board has %d" % (coord, len(coord), len(self.dimensions)))

        for (c, d) in zip(coord, self.dimensions):
            if not d:
                #
                # This dimension is infinite
                #
                continue
            if c not in d:
                raise IndexError("Coordinate %s is out-of-bounds" % coord)
        
        return tuple(c + o for (c, o) in zip(coord, self._offset))
    
    def nearest(self, coord, offset):
        coord = self._bounds_check(coord)
        coord1 = self._bounds_check(tuple(c + o for c, o in zip(coord, offset)))
        
    def is_in_bounds(self, loc):
        if len(loc) != self.num_dimensions:
            raise IndexError("Wrong number of dimensions for given key")
        
        if loc not in self._in_bounds:
            
            if self.wrap and not self.infinite:
                loc = [x % self.dimensions[i] for i, x in enumerate(loc)]

            if not self.infinite:
                for i, dim in enumerate(loc):
                    if not (0 <= dim < self.dimensions[i]):
                        self._in_bounds[loc] = False
                        break
            
            if loc not in self._in_bounds:
                self._in_bounds[loc] = True
        
        return self._in_bounds[loc]

    def _bounds_check(self, loc):
        if self.is_in_bounds(loc):
            return loc
        else:
            raise IndexError("Location out of bounds")

    def occupied(self):
        minmax = [[float('inf'), float('-inf')]] * self.num_dimensions

        for key in self._data.iterkeys():
            for i, dim in enumerate(key):
                if dim < minmax[i][0]:
                    minmax[i][0] = dim

                if dim > minmax[i][1]:
                    minmax[i][1] = dim

        return minmax

    def get_viewport(self):
        return self

    def neighbours(self, loc):
        """For a given coordinate, return a dictionary of its nearest
        neighbours along all coordinates, mapping each coordinate to
        its value.
        """
        loc = self._bounds_check(loc)

        mins = [x - 1 for x in loc]
        maxs = [x + 1 for x in loc]

        coords = set(c for c in itertools.product(*zip(mins, loc, maxs)) if self.is_in_bounds(c))
        coords.remove(loc)

        return dict((c, self[c]) for c in coords)

if __name__ == '__main__':
    pass
