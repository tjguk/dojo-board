Board Game for Python Dojos
===========================

Introduction
------------

Often, when running a Python Dojo, we've ended up with a challenge
based around some kind of board or tile-based landscape. In these
situations it's not uncommon to spend a lot of the time building up
your basic board functionality in order to support the more interesting
gameplay algorithm.

This module attempts to produce a general-purpose board structure which
has the functionality needed for a range of purposes, and lends itself
to being subclassed for those particular needs.

Getting Started
---------------

Absolutely basic usage::

    import board
    #
    # Produce a 3x3 board
    #
    b = board.Board((3, 3))
    
    b[0, 0] = "X"
    b[1, 0] = "O"

Essentials
----------

Board is an n-dimensional board, any of which dimensions can be of
infinite size. (So if you have, say, 3 infinite dimensions, you have
the basis for a Minecraft layout). Dimensions are zero-based.

Cells on the board are accessed by item access, eg board[1, 2] or
landscape[1, 1, 10].

A board can be copied, optionally along with its data by means of the
.copy method. Or a section of a board can be linked to the original
board by means of slicing the original board::

    b1 = board.Board((9, 9))
    b1[1, 1] = 1
    b2 = b1.copy()
    b3 = b1[:3, :3]
    
Note that the slice must include all the dimensions of the original
board, but any of those subdimensions can be of length 1::

    b1 = board.Board((9, 9, 9))
    b2 = b1[:3, :3, 1:1]
