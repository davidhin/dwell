import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from dwell import Dwell

design = Dwell()

design.create_floor(40, 30)
design.create_walls(5, 0.2)
design.add_window("left", 2, 1.5, 4)
design.build("output.blend")
