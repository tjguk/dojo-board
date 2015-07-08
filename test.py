import unittest
from board import Board, Infinity

class BoardTest(unittest.TestCase):
    
    def setUp(self):
        self.b = Board((3, 3))
        for i in range(3):
            self.b[i, i] = i

class BoardCreationTest(BoardTest):
    
    def test_0_dim(self):
        """An exception is raised when a board is created with no dimensions
        """
        with self.assertRaises(Board.InvalidDimensionsError):
            Board(())
            
    def test_n_dim(self):
        """Create each of 1- to 10-dimensional boards
        """
        for n in range(1, 10):
            b = Board(tuple(1 for i in range(n)))
            self.assertEqual(len(b.dimensions), n)
    
    def test_one_infinite_dim(self):
        """Create a board with one infinite dimension
        """
        inf = float("inf")
        b = Board((3, 3, Infinity))
        self.assertEqual(len(b.dimensions[0]), 3)
        self.assertEqual(len(b.dimensions[1]), 3)
        self.assertEqual(len(b.dimensions[2]), Infinity)

    def test_all_infinite_dims(self):
        """Create a board with every dimension infinite (a la Minecraft)
        """
        inf = float("inf")
        b = Board((Infinity, Infinity, Infinity))
        self.assertEqual(len(b.dimensions[0]), Infinity)
        self.assertEqual(len(b.dimensions[1]), Infinity)
        self.assertEqual(len(b.dimensions[2]), Infinity)

class BoardDump(BoardTest):
    
    def test_finite_empty_dumped(self):
        b = Board((3, 3))
        dumped = list(b.dumped())
        #
        # For an empty board, should produce one header line,
        # plus the curly brackets with no content (3 rows)
        #
        self.assertEqual(len(dumped), 3)
    
    def test_infinite_empty_dumped(self):
        b = Board((3, Infinity))
        dumped = list(b.dumped())
        #
        # For an empty board, should produce one header line,
        # plus the curly brackets with no content (3 rows)
        #
        self.assertEqual(len(dumped), 3)

    def test_finite_dumped(self):
        b = Board((3, 3))
        for x, y in b:
            b[x, y] = x * y
        dumped = list(b.dumped())
        self.assertEqual(len(dumped), 3 + 9)
    
    def test_infinite_dumped(self):
        b = Board((3, Infinity))
        for x in range(3):
            for y in range(3):
                b[x, y] = x * y
        dumped = list(b.dumped())
        self.assertEqual(len(dumped), 3 + 9)

class BoardContains(BoardTest):
    
    def setUp(self):
        self.board = Board((3, 3))
    
    def test_contains(self):
        self.assertTrue((0, 0) in self.board)
    
    def test_does_not_contain(self):
        self.assertFalse((3, 3) in self.board)
    
    def test_contains_infinite(self):
        self.assertTrue((0, 10) in Board((3, Infinity)))

    def test_does_not_contain_infinite(self):
        self.assertFalse((3, 10) in Board((3, Infinity)))

class BoardIteration(BoardTest):
    
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
    
class BoardCopy(BoardTest):

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
    
    def test_setitem_value(self):
        self.b[0, 1] = "Value"
        self.assertEqual(self.b[0, 1], "Value")
    
    def test_delitem_value(self):
        del self.b[0, 0]
        self.assertEqual(self.b[0, 0], None)
    
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

if __name__ == '__main__':
    unittest.main()
