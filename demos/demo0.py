import math
import random

from map_generator import MapGenerator



if __name__ == '__main__':
    # Use `start` to reset the map generator's state if multiple
    # maps need to be generated.
    MapGenerator.start(ar=8.0, cs=4.0, od=10.0, hp=10.0, sm=1.0, st=1)
    MapGenerator.set_meta(version='test', creator='unknown')

    # The control point data format is:
    #   [ t, x, y, c ]
    #       t = time
    #       x = x position
    #       y = y position
    #       c = split slider?
    #
    # If there is is 1 control point, then the data is treated
    # as a hitcircle. If there are multiple control points, then
    # then the data is treated as a slider.
    #
    # By default `t_delta` is `True`. This treats time value
    # as a delta. A timestamp value is internal tracked and
    # automatically added to. If specific timestamp is desired,
    # pass `t_delta=False` to `add_note`.

    # Add single notes arranged in a circle. The notes are
    # randomly placed 250 ms or 500 ms apart. `c` has no
    # function in this case.
    for i in range(50):
        MapGenerator.add_note([
            [ random.choice([250, 500]), 200 + 100*math.cos(i), 200 + 100*math.sin(i), 0 ]
        ])

    # Add a slider. Only first and last timings matter.
    # The rest are there for sake of data format consistency.
    MapGenerator.add_note([
        [50, 100, 100, 0],
        [50, 500, 100, 0],
        [50, 500, 200, 1],
        [50, 100, 200, 0],
        [50, 500, 300, 0],
    ])

    # Generates the .osu data. `map` is the .osu file text.
    map = MapGenerator.gen()

    # Saves the .osu data to a file.
    #
    # Replace this with your osu! folder path
    # In this example my osu! install is located in "C:/Games/osu!".
    # The map is put into the folder osu! Play Analyzer monitors for generated maps
    map_path = f'./data'
    MapGenerator.save(map, map_path)
