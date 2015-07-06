import os, sys
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
    
    class BoardError(BaseException): pass
    class InvalidDimensionsError(BoardError): pass
    class OutOfBoundsError(BoardError): pass
    
    def __init__(self, dimension_sizes, _global_board=None, _offset_from_global=None):
        """Set up a n-dimensional board
        """
        if not dimension_sizes:
            raise self.InvalidDimensionsError("The board must have at least one dimension")
        self.dimensions = [list(range(size or 0)) for size in dimension_sizes]

        #
        # This can be a sub-board of another board: a slice.
        # If that's the case, the boards share a common data structure
        # and this one is offset from the other. 
        # NB this means that if a slice is taken of a slice, the offset must itself be offset!
        #
        self._data = {} if _global_board is None else _global_board
        self._offset_from_global = _offset_from_global or tuple(0 for _ in self.dimensions)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, tuple(len(d) for d in self.dimensions))

    def dumped(self, only_used=True):
        is_offset = any(c for c in self._offset_from_global)
        yield repr(self)
        yield "{"
        for coord in self._iterate(only_used=only_used):
            if is_offset:
                global_coord = " => %s" % (self._to_global(coord),)
            else:
                global_coord = ""
            yield "  %s%s [%s]" % (coord, global_coord, self[coord])
        yield "}"
    
    def dump(self, outf=sys.stdout):
        for line in self.dumped():
            outf.write(line + "\n")
        
    def _is_in_bounds(self, coord):
        return all(not d or c in d for (c, d) in zip(coord, self.dimensions))
    
    def __contains__(self, coord):
        return self._is_in_bounds(coord)

    def __iter__(self):
        return itertools.product(*(d if d else itertools.count() for d in self.dimensions))

    def _to_global(self, coord):
        return tuple(c + o for (c, o) in zip(coord, self._offset_from_global))

    def _from_global(self, coord):
        return tuple(c - o for (c, o) in zip(coord, self._offset_from_global))

    def _iterate(self, only_used=True):
        """Generate the list of local coordinates. If one or more dimensions
        is infinite, only the bounding box of used coordinates will be 
        produced.
        """
        #
        # Because we don't want to iterate infinitely over our infinite dimension,
        # treat an infinite dimension as the bounding box of its data or, if there is
        # not data on the board, a single [None] dimension.
        #
        dimensions = []
        for n_dimension, dimension in enumerate(self.dimensions):
            if not dimension:
                dmin, dmax = self._occupied_dimension(n_dimension)
                if dmin is None: # no data on the board
                    dimension.append([None])
                else:
                    dimensions.append(range(dmin, 1 + dmax))

        for lcoord in itertools.product(*(d if d else itertools.count() for d in dimensions)):
            if only_used:
                if self._is_in_bounds(lcoord):
                    yield lcoord
            else:
                yield lcoord

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
        of a larger board.
        """
        for coord in list(self._iterate_g(only_used=True)):
            del self._data[coord]

    def __getitem__(self, item):
        """The item is either a tuple of numbers, representing a single
        coordinate on the board, or a tuple of slices representing a copy 
        of some or all of the board.
        """
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
        slice_indices = [slice.indices(len(dimension)) for (slice, dimension) in zip(slices, self.dimensions)]
        if any(abs(step) != 1 for start, stop, step in slice_indices):
            raise IndexError("At least one of slices %s has a stride other than 1" % slices)
        sizes = tuple(stop - start for start, stop, step in slice_indices)
        #
        # Need to take into account the offset of this board, which might
        # itself be offset from the parent board.
        #
        offset = tuple(o + start for (o, (start, stop, step)) in zip(self._offset_from_global, slice_indices))
        return self.__class__(sizes, self._data, offset)

    def _occupied_dimension(self, n_dimension):
        """Return the min/max along a particular dimension.
        (Intended for internal use, eg when displaying an infinite dimension)
        """
        data_in_use = list(self._iterate())
        if not data_in_use:
            return (None, None)
        else:
            return (
                min(c[n_dimension] for c in self._iterate()),
                max(c[n_dimension] for c in self._iterate())
            )
            
    def occupied(self):
        """Return the bounding box of space occupied
        """
        min_coord = tuple(min(c) for c in zip(*self._iterate()))
        max_coord = tuple(max(c) for c in zip(*self._iterate()))
        return min_coord, max_coord
    #
    # These were inherited from the previous implementation. They presumably
    # do useful things but I'm leaving them out for now.
    #
    if 0:

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
