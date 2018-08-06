#!python3
import os, sys

import board
from board import Board, Empty, draw, paint

ox_board = Board((3, 3))
ox_board.paint("ox.png")
os.startfile("ox.html")

player = "O"
while True:
