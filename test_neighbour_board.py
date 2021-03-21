from unittest import TestCase
import board

class TestBoard(TestCase):
    def test_neighbours_original(self):
        b1 = board.Board((3, 3, 3))
        neighbours = list(b1.neighbours((0, 0, 0), include_diagonals=False))

        for coord in neighbours:
            print(coord)
        self.assertEqual(3, len(neighbours))


        neighbours = list(b1.neighbours((0,0,0), include_diagonals=True))
        self.assertEqual(7, len(neighbours))

    def test_two_by_two_board_neighbours(self):
        b = board.Board((2, 2))
        target_coord = (0, 0)
        neighbour_coord = list(b.neighbours(target_coord, include_diagonals=True))
        self.assertEqual(3, len(neighbour_coord))
        self.assertSetEqual({(0, 1), (1, 0), (1, 1)}, set(neighbour_coord))

        neighbour_coord = list(b.neighbours(target_coord, include_diagonals=False))
        self.assertEqual(2, len(neighbour_coord))
        self.assertSetEqual({(0, 1), (1, 0)}, set(neighbour_coord))

    def test_three_by_three_board_neighbours(self):
        b = board.Board((3,3))

        target_coord = (1,1)
        neighbour_coord = list(b.neighbours(target_coord, include_diagonals=True))
        self.assertEqual(8, len(neighbour_coord))
        neighbour_coord = list(b.neighbours(target_coord, include_diagonals=False))
        self.assertEqual(4, len(neighbour_coord))

        target_coord = (0,0)
        neighbour_coord = list(b.neighbours(target_coord, include_diagonals=True))
        self.assertEqual(3, len(neighbour_coord))
        neighbour_coord = list(b.neighbours(target_coord, include_diagonals=False))
        self.assertEqual(2, len(neighbour_coord))
