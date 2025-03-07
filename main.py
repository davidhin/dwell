import sys
import os
import math

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from dwell import Dwell


design = Dwell()

design.create_floor([(0, 0), (13, 0), (10, 6), (6, 6), (6, 10), (0, 12)])
design.create_walls(3, 0.2)
design.add_window(edge_index=4, window_width=2, window_height=1.5, sill=1, offset=0)
design.add_window(edge_index=0, window_width=2, window_height=1.5, sill=1, offset=0)
design.add_window(edge_index=0, window_width=2, window_height=1.5, sill=1, offset=3)
design.add_opening(edge_index=1, opening_width=2, opening_height=2, sill=0, offset=1)

design.add_glb_model(
    filepath="./brimnes.glb",
    scale=(3, 3, 3),
    floor=True,
    snap_line=True,
    wall_edge_index=0,
)

design.add_glb_model(
    filepath="./kmart_blake1.glb",
    scale=(0.5, 0.5, 0.5),
    floor=True,
    snap_line=True,
    wall_edge_index=4,
)

design.build("output.blend")
