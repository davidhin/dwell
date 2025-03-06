import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from dwell import Dwell

design = Dwell()

design.create_floor(10)
design.build("output.blend")
