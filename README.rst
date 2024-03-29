Board Game for Python Dojos
===========================

Introduction
------------

Often, when running a Python Dojo, we've ended up with a challenge
based around some kind of board or tile-based landscape. In these
situations it's not uncommon to spend a lot of the time building up
your basic board functionality in order to support the more interesting
gameplay algorithm.

This module implements a general-purpose board structure which
has the functionality needed for a range of purposes, and lends itself
to being subclassed for those particular needs.

Dependencies
------------

None - stdlib only

Tests
-----

Fairly decent coverage (not actually checked with coverage.py): test.py

Getting Started
---------------

Install with pip::

    pip install board

Absolutely basic usage::

    import board
    #
    # Produce a 3x3 board
    #
    b = board.Board((3, 3))

    b[0, 0] = "X"
    b[1, 0] = "O"

Usage
-----

Board is an n-dimensional board, any of which dimensions can be of
infinite size. (So if you have, say, 3 infinite dimensions, you have
the basis for a Minecraft layout). Dimensions are zero-based and
negative indexes operate as they usually do in Python: working from
the end of the dimension backwards.

Cells on the board are accessed by item access, eg board[1, 2] or
landscape[1, 1, 10].

A board can be copied, optionally along with its data by means of the
.copy method. Or a section of a board can be linked to the original
board by slicing the original board::

    b1 = board.Board((9, 9))
    b1[1, 1] = 1
    b2 = b1.copy()
    b3 = b1[:3, :3]

Note that the slice must include all the dimensions of the original
board, but any of those subdimensions can be of length 1::

    b1 = board.Board((9, 9, 9))
    b2 = b1[:3, :3, :1]

A sentinel value of Empty indicates a position which is not populated
because it has never had a value, or because its value has been deleted::

    b1 = board.Board((3, 3))
    assert b1[1, 1] is board.Empty
    b1.populate("abcdefghi")
    assert b1[1, 1] == "e"
    del b1[1, 1]
    assert b1[1, 1] is board.Empty

Iterating over the board yields its coordinates::

    b1 = board.Board((2, 2))
    for coord in b1:
        print(coord)
    #
    # => (0, 0), (0, 1) etc.
    #

Iteration over a board with one or more infinite dimensions will work
by iterating in chunks::

    b1 = board.Board((3, 3, board.Infinity))
    for coord in b1:
        print(b1)

To see coordinates with their data items, use iterdata::

    b1 = board.Board((2, 2))
    b1.populate("abcd")
    for coord, data in b1.iterdata():
        print(coord, "=>", data)

To read, write and empty the data at a board position, use indexing::

    b1 = board.Board((3, 3))
    b1.populate("abcdef")
    print(b1[0, 0]) # "a"

    b1[0, 0] = "*"
    print(b1[0, 0]) # "*"

    b1[-1, -1] = "*"
    print(b1[2, 2]) # "*"

    del b1[0, 0]
    print(b1[0, 0]) # <Empty>

To test whether a coordinate is contained with the local coordinate space, use in::

    b1 = board.Board((3, 3))
    (1, 1) in b1 # True
    (4, 4) in b1 # False
    (1, 1, 1) in b1 # InvalidDimensionsError

One board is equal to another if it has the same dimensionality and
each data item is equal::

    b1 = board.Board((3, 3))
    b1.populate("abcdef")
    b2 = b1.copy()
    b1 == b2 # True
    b2[0, 0] = "*"
    b1 == b2 # False

    b2 = board.Board((2, 2))
    b2.populate("abcdef")
    b1 == b2 # False

To populate the board from an arbitrary iterator, use .populate::

    def random_letters():
        import random, string
        while True:
            yield random.choice(string.ascii_uppercase)

    b1 = board.Board((4, 4))
    b1.populate(random_letters())

To clear the board, use .clear::

    b1 = board.Board((3, 3))
    b1.populate(range(10))
    b1.clear()
    list(b1.iterdata()) # []

A board is True if it has any data, False if it has none::

    b1 = board.Board((2, 2))
    b1.populate("abcd")
    bool(b1) # True
    b1.clear()
    bool(b1) # False

The length of the board is the product of its dimension lengths. If any
dimension is infinite, the board length is infinite. NB to find the
amount of data on the board, use lendata::

    b1 = board.Board((4, 4))
    len(b1) # 16
    b1.populate("abcd")
    len(b1) # 16
    b1.lendata() # 4
    b2 = board.Board((2, board.Infinity))
    len(b2) # Infinity

To determine the bounding box of the board which contains data, use .occupied::

    b1 = board.Board((3, 3))
    b1.populate("abcd")
    list(c for (c, d) in b1.iterdata()) # [(0, 0), (0, 1), (0, 2), (1, 0)]
    b1.occupied() # ((0, 0), (1, 2))

For the common case of slicing a board around its occupied space,
use .occupied_board::

    b1 = board.Board((3, 3))
    b1.populate("abcd")
    b1.draw()
    b2 = b1.occupied_board()
    b2.draw()

To test whether a position is on any edge of the board, use .is_edge::

    b1 = board.Board((3, 3))
    b1.is_edge((0, 0)) # True
    b1.is_edge((1, 1)) # False
    b1.is_edge((2, 0)) # True

To find the immediate on-board neighbours to a position along all dimensions::

    b1 = board.Board((3, 3, 3))
    list(b1.neighbours((0, 0, 0)))
    # [(0, 1, 1), (1, 1, 0), ..., (1, 0, 1), (0, 1, 0)]

To iterate over all the coords in the rectangular space between
two corners, use .itercoords::

    b1 = board.Board((3, 3))
    list(b1.itercoords((0, 0), (1, 1))) # [(0, 0), (0, 1), (1, 0), (1, 1)]

To iterate over all the on-board positions from one point in a
particular direction, use .iterline::

    b1 = board.Board((4, 4))
    start_from = 1, 1
    direction = 1, 1
    list(b1.iterline(start_from, direction)) # [(1, 1), (2, 2), (3, 3)]
    direction = 0, 2
    list(b1.iterline(start_from, direction)) # [(1, 1), (1, 3)]

or .iterlinedata to generate the data at each point::

    b1 = board.Board((3, 3))
    b1.populate("ABCDEFGHJ")
    start_from = 1, 1
    direction = 1, 0
    list(b1.iterlinedata(start_from, direction)) # ['A', 'D', 'G']

Both iterline and iterdata can take a maximum number of steps, eg for
games like Connect 4 or Battleships::

    b1 = board.Board((8, 8))
    #
    # Draw a Battleship
    #
    b1.populate("BBBB", b1.iterline((2, 2), (1, 0)))

As a convenience for games which need to look for a run of so many
things, the .run_of_n method combines iterline with data to yield
every possible line on the board which is of a certain length along
with its data::

    b1 = board.Board((3, 3))
    b1[0, 0] = 'X'
    b1[1, 1] = 'O'
    b1[0, 1] = 'X'
    for line, data in b1.runs_of_n(3):
        if all(d == "O" for d in data):
            print("O wins")
            break
        elif all(d == "X" for d in data):
            print("X wins")
            break

To iterate over the corners of the board, use .corners::

    b1 = board.Board((3, 3))
    corners() # [(0, 0), (0, 2), (2, 0), (2, 2)]

Properties
----------

To determine whether a board is offset from another (ie the result of a slice)::

    b1 = board.Board((3, 3))
    b1.is_offset # False
    b2 = b1[:1, :1]
    b2.is_offset # True

To determine whether a board has any infinite or finite dimensions::

    b1 = board.Board((3, board.Infinity))
    b1.has_finite_dimensions # True
    b1.has_infinite_dimensions # True
    b2 = board.Board((3, 3))
    b1.has_infinite_dimensions # False
    b3 = board.Board((board.Infinity, board.Infinity))
    b3.has_finite_dimensions # False

Display the Board
-----------------

To get a crude view of the contents of the board, use .dump::

    b1 = board.Board((3, 3))
    b1.populate("abcdef")
    b1.dump()

To get a grid view of a 2-dimensional board, use .draw::

    b1 = board.Board((3, 3))
    b1.populate("OX  XXOO ")
    b1.draw()

If you don't want the borders drawn, eg because you're using the board
to render ASCII art, pass use_borders=False::

    b1 = board.Board((8, 8))
    for coord in b1.iterline((0, 0), (1, 1)):
        b1[coord] = "*"
    for coord in b1.iterline((7, 0), (-1, 1)):
        b1[coord] = "*"
    b1.draw(use_borders=False)

To render to an image using Pillow (which isn't a hard dependency) use paint.
The default renderer treats the data items as text and renders then, scaled
to fit, into each cell. This works, obviously, for things like Noughts & Crosses
assuming that you store something like "O" and "X". But it also works for
word searches and even simple battleships where the data items are objects
whose __str__ returns blank (for undiscovered), "+" for a single hit, and "*"
for a destroyed vessel::

    b1 = board.Board((3, 3))
    b1[0, 0] = "X"
    b1[1, 1] = "O"
    b1[0, 2] = "X"
    b1.paint("board.png")
    # ... and now look at board.png

The text painting is achieved internally by means of a callback called
text_sprite. An alternative ready-cooked callback for paint() is
imagefile_sprite. This looks for a .png file in the current directory
(or another; you can specify).

Local and Global coordinates
----------------------------

Since one board can represent a slice of another, there are two levels
of coordinates: local and global. Coordinates passed to or returned from
any of the public API methods are always local for that board. They
represent the natural coordinate space for the board. Internally, the
module will use global coordinates, translating as necessary.

Say you're managing a viewport of a tile-based dungeon game where the
master dungeon board is 100 x 100 but the visible board is 10 x 10.
Your viewport board is currently representing the slice of the master
board from (5, 5) to (14, 14). Changing the item at position (2, 2) on
the viewport board will change the item at position (7, 7) on the master
board (and vice versa).

As a user of the API you don't need to know this, except to understand
that a board slice is essentially a view on its parent. If you wish
to subclass or otherwise extend the board, you'll need to note where
coordinate translations are necessary.

# TESTING - PLEASE IGNORE