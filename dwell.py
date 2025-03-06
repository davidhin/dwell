import bpy  # type: ignore
import os


class Dwell:
    def __init__(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

    def create_floor(self, size):
        bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))

    def build(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)
        bpy.ops.wm.save_as_mainfile(filepath=filepath, check_existing=False)
        print(f"Scene saved as {filepath}")
