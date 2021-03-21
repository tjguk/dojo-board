#!python3
#
# The semantics of 3.x range are broadly equivalent
# to xrange in 2.7
#
try:
    range = xrange
except NameError:
    pass

import functools
import itertools
import unittest
from board import Board, Infinity, Empty, InfiniteDimension

#
# The most likely false assumptions in the code will be:
# * that boards are 2-dimensional
# * that all dimensions are finite
# * that boards are not slices of other boards
# * that all dimensions have at least two elements
#
# Therefore testing should reflect that. The base test class creates
# several boards intended to exercise the edge cases, including a
# board with only infinite dimensions.
#
# These boards will be initially fully populated along non-infinite
# dimensions.
#

class BoardTest(unittest.TestCase):

    def setUp(self):
        self.b1 = Board((1, 1))
        self.b44 = Board((4, 4))
        self.b333 = Board((3, 3, 3))
        self.b5555 = Board((5, 5, 5, 5))
        self.b33 = self.b44[1:, 1:]
        self.b22 = self.b33[1:, 1:]
        self.b3i = Board((3, Infinity))
        self.bii = Board((Infinity, Infinity))

        self.boards = [
            ("1d", self.b1),
            ("2d", self.b44),
            ("3d", self.b333),
            ("4d", self.b5555),
            ("slice33", self.b33),
            ("slice22", self.b22),
            ("3inf", self.b3i),
            ("inf", self.bii)
        ]

        #
        # The test data set must be enough to fill all of the finite boards
        #
        size_of_test_data = max(len(b) for name, b in self.boards if not b.has_infinite_dimensions)
        self.test_data = range(size_of_test_data)
        for name, board in self.boards:
            if not board.is_offset:
                board.populate(self.test_data)

class BoardCreationTest(BoardTest):

    def test_empty(self):
        """An exception is raised when a board is created with no dimensions
        """
        with self.assertRaises(Board.InvalidDimensionsError):
            Board(())

    def test_dim_0(self):
        """An exception is raised when one of the board dimensions is 0
        """
        with self.assertRaises(Board.InvalidDimensionsError):
            Board((1, 0))

    def test_dim_negative(self):
        """An exception is raised when one of the board dimensions is < 0
        """
        with self.assertRaises(Board.InvalidDimensionsError):
            Board((1, -1))

    def test_n_dim(self):
        """Create each of 1- to 10-dimensional boards
        """
        for n in range(1, 10):
            b = Board(tuple(1 for i in range(n)))
            actual = len(b.dimensions)
            expected = n
            self.assertEqual(expected, actual)

    def test_one_infinite_dim(self):
        """Create a board with one infinite dimension
        """
        b = Board((3, 3, Infinity))
        self.assertEqual(len(b.dimensions[0]), 3)
        self.assertEqual(len(b.dimensions[1]), 3)
        self.assertEqual(len(b.dimensions[2]), Infinity)

    def test_all_infinite_dims(self):
        """Create a board with every dimension infinite (a la Minecraft)
        """
        b = Board((Infinity, Infinity, Infinity))
        self.assertEqual(len(b.dimensions[0]), Infinity)
        self.assertEqual(len(b.dimensions[1]), Infinity)
        self.assertEqual(len(b.dimensions[2]), Infinity)

class BoardDump(BoardTest):

    def test_empty_dumped(self):
        #
        # An empty board will produce one header line,
        # plus the curly brackets with no content (3 rows)
        #
        for name, board in self.boards:
            board.clear()
            dumped = list(board.dumped())

            expected = 3
            actual = len(dumped)
            self.assertEqual(expected, actual, name)

    def test_dumped(self):
        #
        # A populated board will produce one header line
        # plus the curly brackets surrounding one row for
        # each item of contents
        #
        for name, board in self.boards:
            dumped = list(board.dumped())

            expected = 3 + board.lendata()
            actual = len(dumped)
            self.assertEqual(expected, actual, name)

class BoardContains(BoardTest):
    """A coordinate is considered to be "in" a board if
    it's within the bounds of the *local* coordinates. It
    doesn't matter whether that position contains data or not.
    """

    def test_contains(self):
        for name, board in self.boards:
            #
            # Each board will have at least an upper left position
            #
            coord = tuple(0 for d in board.dimensions)
            self.assertTrue(coord in board, name)

    def test_does_not_contain(self):
        for name, board in self.boards:
            #
            # The entirely infinite board contains every coordinate
            #
            if name == "inf":
                continue
            #
            # Construct a coordinate beyond each of the dimensions
            #
            coord = tuple(2 + len(d) for d in board.dimensions)
            self.assertFalse(coord in board, name)

    def test_inf_contains_everything(self):
        board = self.bii
        #
        # Construct a coordinate beyond each of the dimensions.
        # This will nonetheless be contained in the board
        #
        coord = tuple(2 + len(d) for d in board.dimensions)
        self.assertTrue(coord in board)

    def test_contain_with_wrong_dimensionality(self):
        for name, board in self.boards:
            coord = tuple(1 for _ in board.dimensions) + (1,)
            with self.assertRaises(Board.InvalidDimensionsError, msg=name):
                coord in board

class BoardIteration(BoardTest):
    """A board iterates coordinates across all its dimensions in
    an underspecified order. Particularly, any infinite dimension
    results in chunks of 10 coordinates, each time restarting any
    non-infinite dimensions.

    The .iterdata method yield the coordinate and its value for each
    coordinate in the local space which has a value. NB iterdata is
    actually iterating over a dictionary and so the order of coordinates
    is arbitrary
    """

    def test_finite_iteration(self):
        for name, board in self.boards:
            #
            # Skip any boards with an infinite dimension; these are tested
            # separately
            #
            if any(len(d) == Infinity for d in board.dimensions):
                continue
            expected = set(itertools.product(*board.dimensions))
            actual = set(board)
            self.assertSetEqual(expected, actual, name)

    def test_infinite_iteration(self):
        #
        # Any infinite dimensions are iterated over in a chunk. We attempt
        # to match one chunk for each of the infinite dimensions.
        #
        for name, board in self.boards:
            if all(len(d) != Infinity for d in board.dimensions):
                continue
            ranges = [(range(d.chunk_size) if d is InfiniteDimension else d) for d in board.dimensions]
            expected = itertools.product(*ranges)
            self.assertTrue(all(a == b for a, b in zip(expected, board)), name)

    def test_iterdata(self):
        #
        # Non-sliced test contain however much of the test data which
        # fit within their size (ie a subset for finite boards, the whole set for
        # boards with at least one infinite dimension)
        #
        for name, board in self.boards:
            #
            # FIXME: for now, skip offset boards
            #
            if board.is_offset:
                continue
            if board.has_infinite_dimensions:
                data_length = Infinity
            else:
                data_length = functools.reduce(lambda a, b: a * b, (len(d) for d in board.dimensions))
            expected = set(data for data, _ in zip(self.test_data, range(data_length)))
            actual = set(data for coord, data in board.iterdata())
            self.assertSetEqual(expected, actual, name)

    def test_itercoords(self):
        #
        # itercoords generates all the coordinates between two corners
        #
        for name, board in self.boards:
            coord1 = tuple(0 for d in board.dimensions)
            coord2 = tuple(3 if d.is_infinite else len(d) - 1 for d in board.dimensions)

            ranges = [range(c1, 1 + c2) for (c1, c2) in zip(coord1, coord2)]
            expected_results = itertools.product(*ranges)
            actual = board.itercoords(coord1, coord2)
            self.assertEqual(list(expected_results), list(actual), name)

    def test_itercoords_off_board(self):
        #
        # Attempting to iterate between coordinates where at least
        # one endpoint is outside the local coordinate space will
        # raise an exception
        #
        for name, board in self.boards:
            #
            # Skip entirely infinite boards and nothing is off-board for them!
            #
            if board.has_infinite_dimensions and not board.has_finite_dimensions:
                continue
            coord1 = tuple(2 + len(d) for d in board.dimensions)
            coord2 = tuple(0 for d in board.dimensions)
            with self.assertRaises(Board.OutOfBoundsError, msg=name):
                next(board.itercoords(coord1, coord2))

class BoardCopy(BoardTest):
    """Copying a board results in a new board, optionally containing
    the original data. The boards are not linked once the copy is made:
    changing the data in one will affect the other
    """

    def test_copy_without_data_dimensions(self):
        #
        # Copying a board without data results in a second board
        # with the same dimensionality
        #
        for name, board in self.boards:
            board2 = board.copy(with_data=False)
            expected = board.dimensions
            actual = board2.dimensions
            self.assertEqual(expected, actual, name)

    def test_copy_without_data_empty(self):
        #
        # Copying a board without data results in a second empty board
        #
        for name, board in self.boards:
            board2 = board.copy(with_data=False)
            self.assertFalse(board2, name)

    def test_copy_without_data_unlinked(self):
        #
        # Copying a board without data results in a second board
        # not linked to the first
        #
        for name, board in self.boards:
            board2 = board.copy(with_data=False)
            obj = object()
            coord = tuple(0 for _ in board2.dimensions)
            board2[coord] = obj
            expected = obj
            actual = board[coord]
            self.assertIsNot(expected, actual, name)

    def test_copy_with_data_dimensions(self):
        #
        # Copying a board with data results in a second board
        # with the same dimensionality
        #
        for name, board in self.boards:
            board2 = board.copy(with_data=True)
            expected = board.dimensions
            actual = board2.dimensions
            self.assertEqual(expected, actual, name)

    def test_copy_with_data_same_data(self):
        #
        # Copying a board with data results in a second board
        # with the same data
        #
        for name, board in self.boards:
            board2 = board.copy(with_data=True)
            expected = set(board.iterdata())
            actual = set(board2.iterdata())
            self.assertSetEqual(expected, actual, name)

    def test_copy_with_data_unlinked(self):
        #
        # Copying a board without data results in a second board
        # not linked to the first
        #
        for name, board in self.boards:
            board2 = board.copy(with_data=True)
            obj = object()
            coord = tuple(0 for _ in board2.dimensions)
            board2[coord] = obj
            expected = obj
            actual = board[coord]
            self.assertIsNot(expected, actual, name)

class BoardClear(BoardTest):
    """Clearing the board removes all the data visible to the local board.
    That is, if this is a subboard of some larger board, only those items
    which fall within the local coordinate space are removed;
    """

    def test_clear(self):
        for name, board in self.boards:
            board.populate(self.test_data)
            self.assertNotEqual(list(board.iterdata()), [], name)
            board.clear()
            expected = []
            actual = list(board.iterdata())
            self.assertEqual(expected, actual, name)

    def test_clear_offset_board(self):
        """Test that an offset board clears its own values only"""
        for name, board in self.boards:
            if any(len(d) == 1 for d in board.dimensions):
                continue # Won't try to slice a 1-element dimension
            board.populate(self.test_data)
            offset = tuple(1 for _ in board.dimensions)
            coord_slices = tuple(slice(o, None) for o in offset)
            board2 = board[coord_slices]

            #
            # Check that both boards are non-empty
            #
            self.assertNotEqual(list(board.iterdata()), [], name)
            self.assertNotEqual(list(board2.iterdata()), [], name)
            board2.clear()
            #
            # Now check that the second board is empty while its
            # parent is still (part-) populated
            #
            self.assertNotEqual(list(board.iterdata()), [], name)
            self.assertEqual(list(board2.iterdata()), [], name)

class BoardItemAccess(BoardTest):
    """Test access via __getitem__, __setitem__ and __delitem__

    Board objects offer __getitem__ access to values or to sub-boards via the
    slice protocol. They offer __setitem__ to write values and __delitem__ to
    delete values.
    """

    def test_getitem_value(self):
        for name, board in self.boards:
            board.populate(self.test_data)
            coord = tuple(0 for _ in board.dimensions)

            expected = self.test_data[0]
            actual = board[coord]
            self.assertEqual(expected, actual, name)

    def test_getitem_no_value(self):
        for name, board in self.boards:
            board.clear()
            coord = tuple(0 for _ in board.dimensions)

            expected = Empty
            actual = board[coord]
            self.assertIs(expected, actual, name)

    def test_setitem_value(self):
        for name, board in self.boards:
            coord = tuple(0 for _ in board.dimensions)
            obj = object()
            board[coord] = obj

            expected = obj
            actual = board[coord]
            self.assertIs(expected, actual, name)

    def test_delitem_value(self):
        for name, board in self.boards:
            board.populate(self.test_data)
            coord = tuple(0 for _ in board.dimensions)
            del board[coord]

            expected = Empty
            actual = board[coord]
            self.assertIs(expected, actual, name)

    def test_out_of_bounds(self):
        """Check that an OutOfBoundsError is raised when the coordinate is outside
        the local coordinate space
        """
        for name, board in self.boards:
            if board.has_infinite_dimensions and not board.has_finite_dimensions:
                continue # Won't try to check out-of-bounds on an entirely infinite board!
            coord = tuple(2 + len(d) for d in board.dimensions)
            with self.assertRaises(Board.OutOfBoundsError, msg=name):
                board[coord]

    def test_negative_getitem(self):
        """Check that a -1 index refers to the value at the last point on each
        non-infinite dimension.
        """

        #
        # Negative indexes have no meaning on an infinite dimension.
        # For this test, where the board also has finite dimensions,
        # perform the test but fake in a coordinate of zero for the
        # infinite dimensions. Skip the test where there are no
        # finite dimensions.
        #

        for name, board in self.boards:
            if board.has_infinite_dimensions and not board.has_finite_dimensions:
                continue # Won't try to check for negative index an entirely infinite board
            coord = tuple(0 if d[-1] == Infinity else -1 for d in board.dimensions)
            real_coord = tuple(0 if d[-1] == Infinity else len(d) -1 for d in board.dimensions)
            obj = object()
            board[real_coord] = obj

            expected = obj
            actual = board[real_coord]
            self.assertIs(expected, actual, name)

class BoardSliced(BoardTest):

    def test_slice_whole_dimensions(self):
        #
        # Slicing an entire board results in a second board linked to the first
        # with the same dimensionality
        #
        for name, board in self.boards:
            coord_slices = tuple(slice(0, None) for _ in board.dimensions)
            board2 = board[coord_slices]

            expected = board.dimensions
            actual = board2.dimensions
            self.assertEqual(expected, actual, name)

    def test_slice_whole_same_data(self):
        #
        # Slicing a board results in a second board linked to the first
        # with the same data
        #
        for name, board in self.boards:
            coord_slices = tuple(slice(0, None) for _ in board.dimensions)
            board2 = board[coord_slices]
            self.assertTrue(all(d1 == d2 for (d1, d2) in zip(board.iterdata(), board2.iterdata())), name)

    def test_slice_whole_linked(self):
        #
        # Slicing a board results in a second board linked to the first
        # such that a change to the data in one affects the other
        #
        for name, board in self.boards:
            coord_slices = tuple(slice(0, None) for _ in board.dimensions)
            board2 = board[coord_slices]

            #
            # Update the second board at (0, ...) and confirm that
            # the first board has the same data at the same position
            #
            obj = object()
            coord = tuple(0 for _ in board2.dimensions)
            board2[coord] = obj

            expected = obj
            actual = board[coord]
            self.assertIs(expected, actual, name)

    #
    # Test a slice which has a start point but is open-ended
    # eg [1:, 1:, 1:]
    # (NB for infinite dimensions this will result in a new
    # infinite dimension offset against the original one).
    #

    def test_slice_part_open_dimensions(self):
        for name, board in self.boards:
            if any(len(d) == 1 for d in board.dimensions):
                continue # Won't try to slice a 1-element dimension
            #
            # Slice to exclude the 0th element
            #
            offset = tuple(1 for _ in board.dimensions)
            coord_slices = tuple(slice(o, None) for o in offset)
            board2 = board[coord_slices]

            #
            # (Infinite dimensions remain infinite)
            #
            expected = [len(d) if d is InfiniteDimension else len(d) -1 for d in board.dimensions]
            actual = [len(d) for d in board2.dimensions]
            self.assertEqual(expected, actual, name)

    def test_slice_part_open_linked(self):
        for name, board in self.boards:
            if any(len(d) == 1 for d in board.dimensions):
                continue # Won't try to slice a 1-element dimension
            #
            # Slice to exclude the 0th element
            #
            offset = tuple(1 for _ in board.dimensions)
            coord_slices = tuple(slice(o, None) for o in offset)
            board2 = board[coord_slices]

            #
            # Data at (0, ...) in the second board should match (1, ...) in the first
            #
            coord2 = tuple(0 for _ in board2.dimensions)
            coord1 = tuple(i + o for (i, o) in zip(coord2, offset))
            obj = object()
            board2[coord2] = obj

            expected = board[coord1]
            actual = board2[coord2]
            self.assertIs(expected, actual, name)

    #
    # Test a slice which has a start and an end point
    # eg [1:2, 1:2, 1:2]
    # (NB for infinite dimensions this will result in a new
    # *finite* dimension offset against the original one).
    #

    def test_slice_part_closed_dimensions(self):
        for name, board in self.boards:
            if any(len(d) == 1 for d in board.dimensions):
                continue # Won't try to slice a 1-element dimension
            #
            # Slice to include the 0th element
            #
            offset_start = tuple(0 for _ in board.dimensions)
            offset_stop = tuple(1 for _ in board.dimensions)
            coord_slices = tuple(slice(o0, o1) for (o0, o1) in zip(offset_start, offset_stop))
            board2 = board[coord_slices]

            #
            # (Infinite dimensions become finite)
            #
            expected = [o1 - o0 for (o0, o1) in zip(offset_start, offset_stop)]
            actual = [len(d) for d in board2.dimensions]
            self.assertEqual(expected, actual, name)

    def test_slice_part_closed_linked(self):
        for name, board in self.boards:
            if any(len(d) == 1 for d in board.dimensions):
                continue # Won't try to slice a 1-element dimension
            #
            # Slice to include the 0th element
            #
            offset_start = tuple(0 for _ in board.dimensions)
            offset_stop = tuple(1 for _ in board.dimensions)
            coord_slices = tuple(slice(o0, o1) for (o0, o1) in zip(offset_start, offset_stop))
            board2 = board[coord_slices]

            #
            # Data at (0, ...) in the second board should match (1, ...) in the first
            #
            coord2 = tuple(0 for _ in board2.dimensions)
            coord1 = tuple(i + o for (i, o) in zip(coord2, offset_start))
            obj = object()
            board2[coord2] = obj

            expected = board[coord1]
            actual = board2[coord2]
            self.assertIs(expected, actual, name)

class BoardDunders(BoardTest):
    """Sundry dunder methods such as __eq__, __len__ and so on
    """

    #
    # Boards are considered equal if they have the same number
    # of dimensions of the same size and the data where populated is
    # the same.

    def test_eq(self):
        for name, board in self.boards:
            board.populate(self.test_data)
            board2 = board.copy(with_data=True)
            self.assertEqual(board, board2, name)

    def test_eq_empty(self):
        for name, board in self.boards:
            board.clear()
            board2 = board.copy(with_data=True)
            self.assertEqual(board, board2, name)

    def test_eq_different_dimensionality(self):
        for name, board in self.boards:
            dimension_sizes2 = tuple([len(d) for d in board.dimensions] + [1])
            board2 = Board(dimension_sizes2)
            self.assertNotEqual(board, board2, name)

    def test_eq_different_dimensions(self):
        for name, board in self.boards:
            dimension_sizes2 = tuple(1 if len(d) == Infinity else len(d) + 1 for d in board.dimensions)
            board2 = Board(dimension_sizes2)
            self.assertNotEqual(board, board2, name)

    def test_eq_different_data(self):
        for name, board in self.boards:
            board.populate(self.test_data)
            board2 = board.copy(with_data=True)
            board2.populate(reversed(self.test_data))
            self.assertNotEqual(board, board2, name)

    #
    # The length of a board is the product of its dimension lengths,
    # except if any of the dimensions is infinite, in which case
    # the length is Infinity
    #

    def test_len_finite(self):
        for name, board in self.boards:
            if board.has_infinite_dimensions:
                continue

            expected = 1
            for d in board.dimensions:
                expected *= len(d)
            actual = len(board)
            self.assertEqual(expected, actual, name)

    def test_len_infinite(self):
        for name, board in self.boards:
            if not board.has_infinite_dimensions:
                continue

            expected = Infinity
            actual = len(board)
            self.assertEqual(expected, actual, name)

    #
    # Not really a dunder method, but masquerading as one
    # lendata returns the number of positions occupied by data
    #

    def test_lendata_empty(self):
        for name, board in self.boards:
            board.clear()

            expected = 0
            actual = board.lendata()
            self.assertEqual(expected, actual, name)

    def test_lendata_1(self):
        for name, board in self.boards:
            board.clear()
            board[tuple(0 for _ in board.dimensions)] = object()

            expected = 1
            actual = board.lendata()
            self.assertEqual(expected, actual, name)

    def test_lendata_full(self):
        for name, board in self.boards:
            board.clear()
            board.populate(self.test_data)
            #
            # Population will stop when it runs out of data or when it
            # runs out of board to populate. The resulting data will
            # be the smaller of the board size and data length
            #

            expected = min(len(board), len(self.test_data))
            actual = board.lendata()
            self.assertEqual(expected, actual, name)

    #
    # A board is considered true if it has at least one position
    # populated with data
    #

    def test_bool_empty(self):
        for name, board in self.boards:
            board.clear()
            self.assertFalse(board, name)

    def test_bool_nonempty(self):
        for name, board in self.boards:
            board.populate([object()])
            self.assertTrue(board, name)

class BoardOccupied(BoardTest):
    """Check the determination of the bounding box of occupied positions
    """
    def test_empty(self):
        """If the board is empty, a pair of empty tuples will be returned
        """
        for name, board in self.boards:
            board.clear()

            expected = (), ()
            actual = board.occupied()
            self.assertEqual(expected, actual, name)

    def test_single_position(self):
        for name, board in self.boards:
            board.clear()
            min_coord = max_coord = tuple(0 for _ in board.dimensions)
            board[min_coord] = object()

            expected = min_coord, max_coord
            actual = board.occupied()
            self.assertEqual(expected, actual, name)

    def test_square(self):
        for name, board in self.boards:
            board.clear()
            min_coord = tuple(0 for _ in board.dimensions)
            max_coord = tuple(0 if d.is_infinite else len(d) - 1 for d in board.dimensions)
            board[min_coord] = object()
            board[max_coord] = object()

            expected = min_coord, max_coord
            actual = board.occupied()
            self.assertEqual(expected, actual, name)

class BoardEdges(BoardTest):
    """Check the detection and generation of edges

    Positions are considered on the edge if any of their coordinate elements
    are at position 0 or if they are at the extreme range of the corresponding
    finite dimension.
    """
    def test_is_edge(self):
        for name, board in self.boards:
            if all(d.is_finite for d in board.dimensions):
                length = len(board)
            elif any(d.is_finite for d in board.dimensions):
                max_finite_length = max(len(d) for d in board.dimensions if d.is_finite)
                length = functools.reduce(lambda a, b: a * b, (len(d) if d.is_finite else max_finite_length for d in board.dimensions))
            else:
                length = 100

            n = 0
            for coord in board:
                if 0 in coord:
                    self.assertTrue(board.is_edge(coord), name)
                elif any(c == len(d) - 1 for c, d in zip(coord, board.dimensions)):
                    self.assertTrue(board.is_edge(coord), name)
                else:
                    self.assertFalse(board.is_edge(coord), name)

                n += 1
                if n > length: break


class BoardNeighbours(BoardTest):
    """Check that neighbours work correctly

    Neighbours should show all immediately adjacent coordinates which are on the board
    """
    def test_neighbours_1d_center(self):
        """
        Really small 1 dimension board still has neighbours.
        """
        b = Board(dimension_sizes=(3,))
        coord = (1,)
        expected = {(0,), (2,)}
        actual = set(b.neighbours(coord))
        self.assertEqual(expected, actual)

    def test_neighbours_1d_center_no_diagonals(self):
        b = Board(dimension_sizes=(3,))
        coord = (1,)
        expected = {(0,), (2,)}
        actual = set(b.neighbours(coord, include_diagonals=False))
        self.assertEqual(expected, actual)

    def test_neighbours_2d_corner(self):
        """Find neighbours when the anchor is at the corner of a 2d board
        """
        b = self.b44

        coord = (0, 0)
        expected = {(1, 0), (0, 1), (1, 1)}
        actual = set(b.neighbours(coord))
        self.assertEqual(expected, actual)

    def test_neighbours_2d_corner_exclude_diagonals(self):
        """Find neighbours when the anchor is at the corner of a 2d board
        """
        b = self.b44

        coord = (0, 0)
        expected = {(1, 0), (0, 1)}
        actual = set(b.neighbours(coord, include_diagonals=False))
        self.assertEqual(expected, actual)

    def test_neighbours_2d_centre(self):
        """Find neighbours when the anchor is not at the corner of a 2d board
        """
        b = self.b44

        coord = (1, 1)
        expected = {
            (0, 0), (1, 0), (2, 0),
            (0, 1), (2, 1),
            (0, 2), (1, 2), (2, 2)
        }
        actual = set(b.neighbours((1, 1)))
        self.assertEqual(expected, actual)

    def test_neighbours_2d_centre_exclude_diagonals(self):
        """Find neighbours when the anchor is not at the corner of a 2d board
        """
        b = self.b44

        coord = (1, 1)
        expected = {
                    (1, 0),
            (0, 1),         (2, 1),
                    (1, 2)
        }
        actual = set(b.neighbours((1, 1), include_diagonals=False))
        self.assertEqual(expected, actual)

    def test_neighbours_3d_corner(self):
        """Find neighbours when the anchor is at the corner of a 3d board
        """
        b = self.b333

        coord = (0, 0, 0)
        expected = {
            (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)
        }
        actual = set(b.neighbours(coord))
        self.assertEqual(expected, actual)

    def test_neighbours_3d_corner_exclude_diagonals(self):
        """Find neighbours when the anchor is at the corner of a 3d board
        """
        b = self.b333

        coord = (0, 0, 0)
        expected = {
            (0, 0, 1), (0, 1, 0), (1, 0, 0)
        }
        actual = set(b.neighbours(coord, include_diagonals=False))
        self.assertEqual(expected, actual)

    def test_neighbours_3d_centre(self):
        """Find neighbours when the anchor is not at the corner of a 3d board
        """
        b = self.b333

        x, y, z = (1, 1, 1)
        expected = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    expected.add((x + dx, y + dy, z + dz))
        expected.remove((x, y, z))

        actual = set(b.neighbours((1, 1, 1)))
        self.assertEqual(expected, actual)

    def test_neighbours_3d_centre_exclude_diagonals(self):
        """Find neighbours when the anchor is not at the corner of a 3d board
        """
        b = self.b333

        x, y, z = (1, 1, 1)
        expected = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    offset = (dx, dy, dz)
                    # exclude the origin offset (0,0,0).
                    # exclude any offset where more than one dimension changes (diagonal)
                    if offset != (0, 0, 0) and sum(abs(o) for o in offset) == 1:
                        expected.add((x + dx, y + dy, z + dz))

        actual = set(b.neighbours((1, 1, 1), include_diagonals=False))
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()
