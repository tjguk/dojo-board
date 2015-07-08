import unittest
import board

class BoardTest(unittest.TestCase):
    pass

class BoardCreationTest(BoardTest):
    
    def test_0_dim(self):
        """An exception is raised when a board is created with no dimensions
        """
        with self.assertRaises(board.Board.InvalidDimensionsError):
            board.Board(())
            
    def test_n_dim(self):
        """Create each of 1- to 10-dimensional boards
        """
        for n in range(1, 10):
            b = board.Board(tuple(1 for i in range(n)))
            self.assertEqual(len(b.dimensions), n)
    
    def test_one_infinite_dim(self):
        """Create a board with one infinite dimension
        """
        inf = float("inf")
        b = board.Board((3, 3, None))
        self.assertEqual(len(b.dimensions[0]), 3)
        self.assertEqual(len(b.dimensions[1]), 3)
        self.assertEqual(len(b.dimensions[2]), board.INFINITY)

    def test_all_infinite_dimd(self):
        """Create a board with every dimension infinite (a la Minecraft)
        """
        inf = float("inf")
        b = board.Board((None, None, None))
        self.assertEqual(len(b.dimensions[0]), board.INFINITY)
        self.assertEqual(len(b.dimensions[1]), board.INFINITY)
        self.assertEqual(len(b.dimensions[2]), board.INFINITY)

class BoardDump(BoardTest):
    
    def test_finite_empty_dumped(self):
        b = board.Board((3, 3))
        dumped = list(b.dumped())
        #
        # For an empty board, should produce one header line,
        # plus the curly brackets with no content (3 rows)
        #
        self.assertEquals(len(dumped), 3)
    
    def test_infinite_empty_dumped(self):
        b = board.Board((3, None))
        dumped = list(b.dumped())
        #
        # For an empty board, should produce one header line,
        # plus the curly brackets with no content (3 rows)
        #
        self.assertEquals(len(dumped), 3)

    def test_finite_dumped(self):
        b = board.Board((3, 3))
        for x, y in b:
            b[x, y] = x * y
        dumped = list(b.dumped())
        self.assertEquals(len(dumped), 3 + 9)
    
    def test_infinite_dumped(self):
        b = board.Board((3, None))
        for x in range(3):
            for y in range(3):
                b[x, y] = x * y
        dumped = list(b.dumped())
        self.assertEquals(len(dumped), 3 + 9)

class BoardContains(BoardTest):
    
    def setUp(self):
        self.board = board.Board((3, 3))
    
    def test_contains(self):
        self.assertTrue((0, 0) in self.board)
    
    def test_does_not_contain(self):
        self.assertFalse((3, 3) in self.board)
    
    def test_contains_infinite(self):
        self.assertTrue((0, 10) in board.Board((3, None)))

    def test_does_not_contain_infinite(self):
        self.assertFalse((3, 10) in board.Board((3, None)))

class BoardIteration(BoardTest):
    
    def test_iteration(self):
        b = board.Board((2, 2))
        self.assertEquals(list(b), [(0, 0), (0, 1), (1, 0), (1, 1)])

    def test_iteration_one_infinite(self):
        """Iterate over a board with one finite and one infinite dimension
        
        The infinite dimensions iterate in chunks of 10
        """
        b = board.Board((2, None))
        i = iter(b)
        for x in range(2):
            for y in range(10):
                self.assertEquals((x, y), next(i))

    def test_iteration_all_infinite(self):
        """Iterate over a board with all dimensions infinite
        
        The infinite dimensions iterate in chunks of 10
        """
        b = board.Board((None, None))
        i = iter(b)
        for x in range(2):
            for y in range(10):
                self.assertEquals((x, y), next(i))

if __name__ == '__main__':
    unittest.main()
