import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from dwell import Dwell


design = Dwell()

design.create_floor([(0, 0), (4, 0), (4, 2.8), (0, 2.8)])
design.create_walls(1.5, 0.01)
design.add_opening(
    edge_index=3, opening_width=1.5, opening_height=1, sill=0.2, offset=0.08
)
design.add_opening(
    edge_index=2, opening_width=0.7, opening_height=1.2, sill=0, offset=-1.3
)

design.add_glb_model(
    filepath="./brimnes.glb",
    scale=(2, 2, 2),
).floor().snap_wall(wall_edge_index=0, wall_offset=-0.4)

design.add_glb_model(
    filepath="./bedside_office.glb",
    scale=(0.75, 0.75, 0.75),
).floor().snap_wall(wall_edge_index=0, wall_offset=0.8, snap_face=1)

design.add_glb_model(
    filepath="./bedside_light_round.glb",
    location=(0, 0, 0.75 + 0.1),
    scale=(0.25, 0.25, 0.25),
).snap_wall(wall_edge_index=0, wall_offset=0.8, dist_to_wall=0.15)

# design.add_glb_model(
#     filepath="./kmart_ladder.glb",
#     location=(0, 0, 0.75 + 0.1),
# ).snap_wall(wall_edge_index=0, wall_offset=1.7, dist_to_wall=0.15)


design.build("output.blend")
