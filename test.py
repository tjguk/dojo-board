#!python3
import unittest
from board import Board, Infinity, Empty

#
# The most likely false assumptions in the code are:
# * That boards are 2-dimensional
# * That all dimensions are finite
# * That boards are not slices of other boards
# * That all dimensions have at least one element [not sure if this is valid]
#
# Therefore testing should reflect that. The base test class creates
# four boards: a 4x4; a 3x3x3; a 2x2 slice of the 4x4; an 3xInf board,
# and a board with only infinite dimensions.
#
# These boards will be initially fully populated along non-infinite
# dimensions.
#

class BoardTest(unittest.TestCase):

    def setUp(self):
        self.b = Board((3, 3))
        for i in range(3):
            self.b[i, i] = i

        self.b44 = Board((4, 4))
        self.b333 = Board((3, 3, 3))
        self.b22 = self.b44[1:3, 1:3]
        self.b3i = Board((3, Infinity))
        self.binf = Board((Infinity, Infinity))

        self.b44.populate(range(100))
        self.b333.populate(range(100))
        self.b3i.populate(range(100))
        self.binf.populate(range(100))

        self.boards = [
            ("2d", self.b44),
            ("3d", self.b333),
            ("slice", self.b22),
            ("3inf", self.b3i),
            ("inf", self.binf)
        ]

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
            self.assertEqual(len(b.dimensions), n)

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
            self.assertEqual(len(dumped), 3, name)

    def test_dumped(self):
        #
        # A populated board will produce one header line
        # plus the curly brackets surrounding one row for
        # each item of contents
        #
        for name, board in self.boards:
            dumped = list(board.dumped())
            self.assertEqual(len(dumped), 3 + len(board), name)

class BoardContains(BoardTest):
    """A coordinate is considered to be "in" a board if
    it's within the bounds of the *local* coordinates. It
    doesn't matter whether it contains data or not.
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
        board = self.binf
        #
        # Construct a coordinate beyond each of the dimensions
        #
        coord = tuple(2 + len(d) for d in board.dimensions)
        self.assertTrue(coord in board)

    def test_contain_with_wrong_dimensionality(self):
        for name, board in self.boards:
            with self.assertRaises(Board.InvalidDimensionsError, msg=name):
                coord = tuple(1 for _ in board.dimensions) + (1,)
                coord in board

class BoardIteration(BoardTest):
    """A board iterates coordinates across all its dimensions in
    an underspecified order. Particularly, any infinite dimension
    results in chunks of 10 coordinates, each time restarting any
    non-infinite dimensions.

    The .iterdata method yield the coordinate and its value for each
    coordinate in the local space which has a value.
    """

    def test_iteration(self):
        b = Board((2, 2))
        self.assertEqual(list(b), [(0, 0), (0, 1), (1, 0), (1, 1)])

    def test_iteration_one_infinite(self):
        """Iterate over a board with one finite and one infinite dimension

        The infinite dimensions iterate in chunks of 10
        """
        b = Board((2, Infinity))
        i = iter(b)
        for x in range(2):
            for y in range(10):
                self.assertEqual((x, y), next(i))

    def test_iteration_all_infinite(self):
        """Iterate over a board with all dimensions infinite

        The infinite dimensions iterate in chunks of 10
        """
        b = Board((Infinity, Infinity))
        i = iter(b)
        for x in range(2):
            for y in range(10):
                self.assertEqual((x, y), next(i))

    def test_iterdata(self):
        "Iterate over data contained"
        b = Board((3, 3))
        results = []
        for x, y in b:
            b[x, y] = x * y
            results.append(((x, y), x * y))

        self.assertEqual(set(b.iterdata()), set(results))

    def test_itercoords_all_on_board(self):
        """Iterate over the coords between a pair of coords where
        all are on this board
        """
        b = Board((3, 3))
        coords = set(b.itercoords((0, 0), (1, 1)))
        self.assertEqual(coords, {(0, 0), (0, 1), (1, 0), (1, 1)})

    def test_itercoords_none_on_board(self):
        """Iterate over the coords between a pair of coords where
        none are on this board
        """
        b = Board((1, 1))
        coords = set(b.itercoords((2, 2), (2, 2)))
        self.assertEqual(coords, set())

    def test_itercoords_some_on_board(self):
        """Iterate over the coords between a pair of coords where
        some are on this board
        """
        b = Board((1, 1))
        coords = set(b.itercoords((0, 0), (2, 2)))
        self.assertEqual(coords, {(0, 0)})

class BoardCopy(BoardTest):
    """Copying a board can result in a new board, or a subboard
    linked to the original. The former is achieved by the .copy
    command, the latter by slicing the original (similar to pulling
    out the data at a specific coordinate, but using a slice notation
    instead).
    """

    def test_copy_without_data(self):
        b2 = self.b.copy(with_data=False)
        self.assertEqual(list(b2), list(self.b))
        self.assertEqual(list(b2.iterdata()), list())
        obj = object()
        b2[0, 0] = obj
        self.assertIsNot(self.b[0, 0], obj)

    def test_copy_with_data(self):
        b2 = self.b.copy(with_data=True)
        self.assertEqual(list(b2), list(self.b))
        self.assertEqual(list(b2.iterdata()), list(self.b.iterdata()))
        obj = object()
        b2[0, 0] = obj
        self.assertIsNot(self.b[0, 0], obj)

    def test_slice(self):
        b2 = self.b[:, :]
        self.assertEqual(b2.dimensions, self.b.dimensions)
        self.assertEqual(list(b2), list(self.b))
        self.assertEqual(list(b2.iterdata()), list(self.b.iterdata()))
        obj = object()
        b2[0, 0] = obj
        self.assertIs(self.b[0, 0], obj)

    def test_subslice(self):
        b2 = self.b[:2, :2]
        self.assertEqual(b2.dimensions, [range(2), range(2)])
        self.assertEqual(list(b2), [(0, 0), (0, 1), (1, 0), (1, 1)])
        self.assertEqual(list(b2.iterdata()), [(c, v) for (c, v) in self.b.iterdata() if c in b2])
        obj = object()
        b2[0, 0] = obj
        self.assertIs(self.b[0, 0], obj)

class BoardClear(BoardTest):
    """Clearing the board removes all the data visible to the local board.
    That is, if this is a subboard of some larger board, only those items
    which fall within the local coordinate space are removed;
    """

    def test_clear(self):
        self.b.clear()
        self.assertFalse(list(self.b.iterdata()))

    def test_clear_subboard(self):
        "Test that a subboard clears its own values only"
        self.assertEqual(set(v for c, v in self.b.iterdata()), set([0, 1, 2]))
        b2 = self.b[:2, :2]
        self.assertEqual(set(v for c, v in b2.iterdata()), set([0, 1]))
        b2.clear()
        self.assertEqual(set(v for c, v in self.b.iterdata()), set([2]))
        self.assertEqual(set(v for c, v in b2.iterdata()), set())

class BoardItemAccess(BoardTest):
    """Test access via __getitem__, __setitem__ and __delitem__

    Board objects offer __getitem__ access to values or to sub-boards via the
    slice protocol. They offer __setitem__ to write values and __delitem__ to
    delete values.
    """

    def test_getitem_value(self):
        self.assertEqual(self.b[0, 0], 0)

    def test_getitem_no_value(self):
        self.assertIs(self.b[0, 1], Empty)

    def test_setitem_value(self):
        self.b[0, 1] = "Value"
        self.assertEqual(self.b[0, 1], "Value")

    def test_delitem_value(self):
        del self.b[0, 0]
        self.assertIs(self.b[0, 0], Empty)

    def test_out_of_bounds(self):
        with self.assertRaises(IndexError):
            self.b[5, 5]

    def test_all_slices(self):
        b2 = self.b[:2, :2]
        self.assertEqual(b2.dimensions, [d[:2] for d in self.b.dimensions])
        #
        # Check that a change to b2 changes b
        #
        obj = object()
        b2[0, 0] = obj
        self.assertIs(self.b[0, 0], obj)

    def test_all_slices_with_infinite(self):
        b = Board((2, Infinity))
        b2 = self.b[:2, :2]
        self.assertEqual(b2.dimensions, [d[:2] for d in self.b.dimensions])
        #
        # Check that a change to b2 changes b
        #
        obj = object()
        b2[0, 0] = obj
        self.assertIs(self.b[0, 0], obj)

class BoardOffset(BoardTest):
    """A board slice can result in a subboard offset from the main board
    at one or both ends of each dimension.
    """

    def test_simple_copy(self):
        b = self.b
        b2 = b[:, :]
        self.assertEqual(b.dimensions, b2.dimensions)
        #
        # Check that a change to b2 changes b
        #
        obj = object()
        b2[0, 0] = obj
        self.assertIs(self.b[0, 0], obj)

    def test_short_from_origin(self):
        b = self.b
        b2 = b[:-1, :-1]
        self.assertEqual([d[:-1] for d in b.dimensions], b2.dimensions)
        #
        # Check that a change to b2 changes b
        #
        obj = object()
        b2[0, 0] = obj
        self.assertIs(b[0, 0], obj)

    def test_from_offset(self):
        b = self.b
        b2 = b[1:, 1:]
        self.assertEqual([len(d[1:]) for d in b.dimensions], [len(d) for d in b2.dimensions])
        #
        # Check that a change to b2 changes b
        #
        obj = object()
        b2[0, 0] = obj
        self.assertIs(b[1, 1], obj)

    def test_from_offset_infinite(self):
        b = Board((3, Infinity))
        b2 = b[1:, 1:]
        self.assertEqual(len(b2.dimensions[0]), len(b.dimensions[0]) - 1)
        self.assertEqual(len(b2.dimensions[1]), Infinity)
        #
        # Check that a change to b2 changes b
        #
        obj = object()
        b2[0, 0] = obj
        self.assertIs(b[1, 1], obj)

class BoardDunders(BoardTest):
    """Sundry dunder methods such as __eq__, __len__ and so on
    """

    def test_eq(self):
        b1 = Board((1, 1))
        b1.populate(range(100))
        b2 = b1.copy()
        self.assertTrue(b2 == b1)

    def test_eq_different_dimensions(self):
        b1 = Board((1, 1))
        b2 = Board((2, 2))
        self.assertFalse(b2 == b1)

    def test_eq_different_dimensionality(self):
        b1 = Board((1, 1, 1))
        b2 = Board((2, 2))
        self.assertFalse(b2 == b1)

    def test_eq_different_data(self):
        b1 = Board((1, 1))
        b1.populate(range(100))
        b2 = b1.copy()
        del b2[0, 0]
        self.assertFalse(b2 == b1)

    def test_len_empty(self):
        b = Board((1, 1))
        self.assertEqual(len(b), 0)

    def test_len_1(self):
        b = Board((1, 1))
        b.populate(range(100))
        self.assertEqual(len(b), 1)

    def test_len_full(self):
        b = Board((3, 3))
        b.populate(range(100))
        self.assertEqual(len(b), 9)

    def test_len_infinite(self):
        """Check that len still works when at least one of the dimensions
        is infinite
        """
        b = Board((3, Infinity))
        b.populate(range(100))
        self.assertEqual(len(b), 100)

    def test_bool_empty(self):
        b = Board((1, 1))
        self.assertFalse(b)

    def test_bool_nonempty(self):
        b = Board((1, 1))
        b.populate(range(100))
        self.assertTrue(b)

    def test_bool_infinite(self):
        """Check that bool still works when at least one of the dimensions
        is infinite
        """
        b = Board((3, Infinity))
        b.populate(range(100))
        self.assertTrue(b)

class BoardOccupied(BoardTest):
    """Check the determination of the bounding box of occupied positions
    """
    def test_empty(self):
        """If the board is empty, a pair of empty tuples will be returned
        """
        b = Board((1, 1))
        self.assertEqual(b.occupied(), ((), ()))

    def test_single_position(self):
        b = Board((3, 3))
        min_coord = max_coord = (1, 1)
        expected = min_coord, max_coord
        b[min_coord] = "*"
        self.assertEqual(b.occupied(), expected)

    def test_square(self):
        b = Board((3, 3))
        min_coord = (0, 0)
        max_coord = (1, 1)

        expected = min_coord, max_coord
        b[min_coord] = "*"
        b[max_coord] = "*"
        self.assertEqual(b.occupied(), expected)

if __name__ == '__main__':
    unittest.main()
