import os, sys
import glob
import random
import time

import board

farm = board.Board((4, 4))
animals = ["sheep", "cow", "pig", "horse"]

def random_population(data):
    while True:
        yield random.choice(data)

os.startfile("farmyard.html")
while True:
    farm.populate(random_population(animals))
    farm.paint("farmyard.png", board.imagefile_sprite(".", ".png"), use_borders=False)
    time.sleep(2)
