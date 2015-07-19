# -*- coding: utf-8 -*-
import os, sys
import itertools

Infinity = sys.maxsize

class InfiniteDimension(object):
    
    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)
    
    def __iter__(self):
        return itertools.count()
    
    def __contains__(self, item):
        return True
    
    def __len__(self):
        return Infinity
    
    def __bool__(self):
        return False
    
    def __getitem__(self, item):
        if isinstance(item, int):
            if item == 0:
                return 0
            elif item == -1:
                return Infinity
            else:
                raise IndexError("Infinite dimensions can only return first & last items")
        elif isinstance(item, slice):
            #
            # If the request is for an open-ended slice,
            # just return the same infinite dimension.
            #
            if item.stop is None:
                return self
            else:
                return range(*item.indices(item.stop))
        else:
            raise TypeError("{} can only be indexed by int or slice".format(self.__class__.__name__))
            
class Board(object):
    """Board - represent a board of stated dimensions, possibly infinite.
    
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
    
    INFINITE_CHUNK_SIZE = 10
    
    def __init__(self, dimension_sizes, _global_board=None, _offset_from_global=None):
        """Set up a n-dimensional board
        """
        if not dimension_sizes:
            raise self.InvalidDimensionsError("The board must have at least one dimension")
        self.dimensions = [InfiniteDimension() if size == Infinity else range(size) for size in dimension_sizes]

        #
        # This can be a sub-board of another board: a slice.
        # If that's the case, the boards share a common data structure
        # and this one is offset from the other. 
        # NB this means that if a slice is taken of a slice, the offset must itself be offset!
        #
        self._data = {} if _global_board is None else _global_board
        self._offset_from_global = _offset_from_global

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, tuple(len(d) for d in self.dimensions))

    def dumped(self):
        if self._offset_from_global:
            offset = " offset by {}".format(self._offset_from_global)
        else:
            offset = ""
        yield repr(self) + offset
        yield "{"
        for coord, value in self.iterdata():
            if self._offset_from_global:
                global_coord = " => {}".format(self._to_global(coord))
            else:
                global_coord = ""
            data = " [{}]".format(self[coord] if self[coord] is not None else "")
            yield "  {}{}{}".format(coord, global_coord, data)
        yield "}"
    
    def dump(self, outf=sys.stdout):
        for line in self.dumped():
            outf.write(line + "\n")
        
    def _is_in_bounds(self, coord):
        return all(c in d for (c, d) in zip(coord, self.dimensions))
    
    def __contains__(self, coord):
        return self._is_in_bounds(coord)

    def __iter__(self):
        """Iterator over all combinations of coordinates.
        
        If all the dimensions are finite (the simplest and most common
        situation) just use itertools.product.
        
        If any dimension is infinite, we can't use itertools.product
        directly because it consumes its arguments in order to make
        up the axes for its Cartesian join. Instead, we chunk through
        any infinite dimensions, while repeating the finite ones.
        """
        if any(d[-1] == Infinity for d in self.dimensions):        
            start, chunk = 0, self.INFINITE_CHUNK_SIZE
            while True:
                iterators = [d[start:start+chunk] if d[-1] == Infinity else iter(d) for d in self.dimensions]
                for coord in itertools.product(*iterators):
                    yield coord
                start += chunk
        else:
            for coord in itertools.product(*self.dimensions):
                yield coord

    def _to_global(self, coord):
        if not self._offset_from_global:
            return tuple(coord)
        else:
            return tuple(c + o for (c, o) in zip(coord, self._offset_from_global))

    def _from_global(self, coord):
        if not self._offset_from_global:
            return tuple(coord)
        else:
            return tuple(c - o for (c, o) in zip(coord, self._offset_from_global))

    def iterdata(self):
        """Generate the list of data in local coordinate terms.
        """
        for gcoord, value in self._data.items():
            lcoord = self._from_global(gcoord)
            if self._is_in_bounds(lcoord):
                yield lcoord, value

    def copy(self, with_data=True):
        board = self.__class__(tuple(len(d) for d in self.dimensions))
        if with_data:
            for coord, value in self.iterdata():
                board._data[coord] = value
        return board

    def clear(self):
        """Clear the data which belongs to this board, possibly a sub-board
        of a larger board.
        """
        for lcoord, value in list(self.iterdata()):
            del self._data[self._to_global(lcoord)]

    def __getitem__(self, item):
        """The item is either a tuple of numbers, representing a single
        coordinate on the board, or a tuple of slices representing a copy 
        of some or all of the board.
        """
        if all(isinstance(i, int) for i in item):
            coord = self._normalised_coord(item)
            return self._data.get(coord)
        elif all(isinstance(i, (int, slice)) for i in item):
            return self._slice(item)
        else:
            raise TypeError("{} can only be indexed by int or slice".format(self.__class__.__name))
    
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
            raise IndexError("Coordinate {} has {} dimensions; the board has {}".format(coord, len(coord), len(self.dimensions)))

        #
        # Account for negative indices in the usual way, allowing
        # for the fact that you can't use negative indices if the
        # dimension is infinite
        #
        normalised_coord = []
        for c, d in zip(coord, self.dimensions):
            if c < 0 and not d:
                raise IndexError("Cannot use negative index {} on an infinite dimension".format(c))
            else:
                normalised_coord.append(len(d) + c if c < 0 else c)
        
        if not self._is_in_bounds(coord):
            raise IndexError("Coordinate {} is out-of-bounds".format(coord))

        return self._to_global(coord)

    def _slice(self, slices):
        """Produce a subset of this board, possibly of fewer dimensions,
        linked to the same underlying data.
        """
        if len(slices) != len(self.dimensions):
            raise IndexError("Slices {} have {} dimensions; the board has {}".format(slices, len(slices), len(self.dimensions)))

        #
        # Determine the start/stop/step for all the slices
        #
        slice_indices = [slice.indices(len(dimension)) for (slice, dimension) in zip(slices, self.dimensions)]
        if any(abs(step) != 1 for start, stop, step in slice_indices):
            raise IndexError("At least one of slices {} has a stride other than 1".format(slices))
        
        _sizes = []
        for (start, stop, step), dimension in zip(slice_indices, self.dimensions):
            if len(dimension) == Infinity:
                _sizes.append(Infinity)
            else:
                _sizes.append(stop - start)
        sizes = tuple(_sizes)
        #~ sizes = tuple(Infinity if len(d) is Infinity else (stop - start) for (start, stop, step), d in zip(slice_indices, self.dimensions))
        #
        # Need to take into account the offset of this board, which might
        # itself be offset from the parent board.
        #
        _offset_from_global = self._offset_from_global or tuple(0 for _ in self.dimensions)
        offset = tuple(o + start for (o, (start, stop, step)) in zip(_offset_from_global, slice_indices))
        return self.__class__(sizes, self._data, offset)

    def _occupied_dimension(self, n_dimension):
        """Return the min/max along a particular dimension.
        (Intended for internal use, eg when displaying an infinite dimension)
        """
        data_in_use = [coord for coord in self._data if coord in self]
        if not data_in_use:
            return (None, None)
        else:
            return (
                min(c[n_dimension] for c in data_in_use),
                max(c[n_dimension] for c in data_in_use)
            )
            
    def occupied(self):
        """Return the bounding box of space occupied
        """
        min_coord = tuple(min(coord) for coord, value in zip(*self.iterdata()))
        max_coord = tuple(max(coord) for coord, value in zip(*self.iterdata()))
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
