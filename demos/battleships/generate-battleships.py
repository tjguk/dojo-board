import random
import board

vessel_formats = [
  ("s", 2, 3),
  ("f", 3, 3),
  ("d", 4, 2),
  ("c", 5, 1)
]
vessels = {}

b = board.Board((16, 16))
for vessel_type, length, number in vessel_formats:
    print("\nAdding", vessel_type)
    for n in range(number):
        runs = [coords for (coords, data) in b.runs_of_n(length) if not any(data)]
        random.shuffle(runs)
        vessel = runs.pop()
        for coord in vessel:
            b[coord] = vessel_type
        vessels.setdefault(vessel_type, set()).add(vessel)

b.draw()
