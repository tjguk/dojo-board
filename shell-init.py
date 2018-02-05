import os
import random
import string

import board

b2 = board.Board((3, 3))
b3 = board.Board((4, 4, 4))

for coord in b2:
    b2[coord] = random.choice(string.ascii_uppercase)
for coord in b3:
    b3[coord] = random.choice(string.ascii_uppercase)
