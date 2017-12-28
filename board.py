# -*- coding: utf-8 -*-
import os, sys
import itertools

Default = object()

Infinity = sys.maxsize

class _Empty(object):

    def __repr__(self):
        return "<Empty>"

    def __bool__(self):
        return False

Empty = _Empty()

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
        return "<{} {}>".format(self.__class__.__name__, tuple(("Infinity" if isinstance(d, InfiniteDimension) else len(d)) for d in self.dimensions))

    def __eq__(self, other):
        return \
            self.dimensions == other.dimensions and \
            dict(self.iterdata()) == dict(other.iterdata())

    def __len__(self):
        return len(self._data)

    def __nonzero__(self):
        return bool(self._data)

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
        if len(coord) != len(self.dimensions):
            raise self.InvalidDimensionsError(
                "Coordinate {} has {} dimensions; the board has {}".format(coord, len(coord), len(self.dimensions)))

        return all(c in d for (c, d) in zip(coord, self.dimensions))

    def __contains__(self, coord):
        return self._is_in_bounds(coord)

    def __iter__(self):
        """Iterator over all combinations of coordinates. If you need
        data, use iterdata.
        """
        # If all the dimensions are finite (the simplest and most common
        # situation) just use itertools.product.

        # If any dimension is infinite, we can't use itertools.product
        # directly because it consumes its arguments in order to make
        # up the axes for its Cartesian join. Instead, we chunk through
        # any infinite dimensions, while repeating the finite ones.
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

    def iterline(self, coord1, coord2, extend=False):
        """Generate all the coordinates in a line which pass through
        coord1 and coord2, optionally extending in both directions.
        """
        if coord1 == coord2:
            raise ValueError("Distinct coordinates must be supplied for line iteration")
        for coord in coord1, coord2:
            if not self._is_in_bounds(coord):
                raise self.OutOfBoundsError("{} is out of bounds for {}".format(coord, self))

        x1, y1 = coord1
        x2, y2 = coord2
        #
        # If the line is vertical, extend it if required in both directions
        # and yield all the coordinates in between
        #
        if x1 == x2:
            if extend:
                y = min(y1, y2) - 1
                while self._is_in_bounds(x1, y):
                    yield x1, y
                    y -= 1
            for y in range(y1, y2 + 1):
                yield x1, y
            if extend:
                y = max(y1, y2) + 1
                while self._is_in_bounds(x1, y):
                    yield x1, y
                    y += 1
        #
        # ... otherwise determine the function for y = mx + c
        # and yield every coordinate
        #
        else:
            m = (y2 - y1) / (x2 - x1)
            c = y1 - (m * x1)
            y = lambda x: m * x + c
            if extend:
                x = min(x1, x2) - 1
                while self._is_in_bounds(x, y1):
                    yield x, round(y(x))
                    x -= 1
            for x in range(x1, x2 + 1):
                yield x, round(y(x))
            if extend:
                x = max(x1, x2) + 1
                while self._is_in_bounds(x, y1):
                    yield x, round(y(x))
                    x += 1

    def copy(self, with_data=True):
        """Return a new board with the same dimensionality as the present one.
        If with_data is truthy, populate with the current data.

        NB this creates a copy, not a reference. For linked copy of the board,
        use __getitem__, eg b2 = b1[:, :, :]
        """
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
            return self._data.get(coord, Empty)
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
            raise IndexError("Coordinate {} is out-of-bounds on board {!r}".format(coord, self))

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
        coords_in_use = [coord for coord, _ in self.iterdata()]
        min_coord = tuple(min(coord) for coord in zip(*coords_in_use))
        max_coord = tuple(max(coord) for coord in zip(*coords_in_use))
        return min_coord, max_coord

    def itercoords(self, coord1, coord2):
        """Iterate over the coordinates in between the two coordinates which
        exist in the local coordinate space.

        So on a 3x3 board, iterating between (0, 0) and (2, 1) would give:

          (0, 0), (1, 0), (2, 0), (1, 0), (1, 1), (2, 1)

        While iterating between (2, 1) and (3, 3) would give:

          (2, 1), (2, 2)
        """
        for coord in itertools.product(*(range(i1, 1 + i2) for (i1, i2) in zip(coord1, coord2))):
            if self._is_in_bounds(coord):
                yield coord

    def neighbours(self, coord):
        """For a given coordinate, yield each of its nearest
        neighbours along all dimensions, mapping each coordinate to
        its value.
        """
        gcoord = self._normalised_coord(coord)

        #
        # Find the bounding box for all coordinates surrounding coord.
        # Then produce every coordinate in that space, selecting only
        # those which fall onto the local board.
        #
        mins = [x - 1 for x in coord]
        maxs = [x + 1 for x in coord]
        gcoords = set(c for c in itertools.product(*zip(mins, gcoord, maxs)) if self._is_in_bounds(c))
        #
        # ... and remove the coordinate itself
        #
        gcoords.remove(coord)

        for g in gcoords:
            yield self._from_global(g), self._data.get(g, Empty)

    def populate(self, iterable):
        """Populate the entire board from an iterable

        The iterable can be shorter or longer than the board. The two
        are zipped together so the population will stop when the shorter
        is exhausted.

        This is a convenience method both to assist testing and also for,
        eg, games like Boggle or word-searches where the board must start
        filled with letters etc. If the data needs to be, eg, a random or
        weighted choice then this should be implemented in the iterator
        supplied.
        """
        for coord, value in zip(self, iter(iterable)):
            self[coord] = value

if __name__ == '__main__':
    pass
