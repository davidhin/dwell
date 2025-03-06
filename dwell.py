import bpy  # type: ignore
import os
import math


class Dwell:
    def __init__(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        self.width = 0
        self.depth = 0
        self.height = 0
        self.thickness = 0

    def create_floor(self, width, depth):
        self.width = width
        self.depth = depth
        bpy.ops.mesh.primitive_plane_add(size=2, location=(width / 2, depth / 2, 0))
        floor = bpy.context.active_object
        floor.scale.x = width / 2
        floor.scale.y = depth / 2

    def create_walls(self, height, thickness):
        self.height = height
        self.thickness = thickness
        bpy.ops.mesh.primitive_cube_add(
            size=2, location=(self.width / 2, thickness / 2, height / 2)
        )
        wall_front = bpy.context.active_object
        wall_front.scale.x = self.width / 2
        wall_front.scale.y = thickness / 2
        wall_front.scale.z = height / 2
        bpy.ops.mesh.primitive_cube_add(
            size=2, location=(self.width / 2, self.depth - thickness / 2, height / 2)
        )
        wall_back = bpy.context.active_object
        wall_back.scale.x = self.width / 2
        wall_back.scale.y = thickness / 2
        wall_back.scale.z = height / 2
        bpy.ops.mesh.primitive_cube_add(
            size=2, location=(thickness / 2, self.depth / 2, height / 2)
        )
        wall_left = bpy.context.active_object
        wall_left.scale.x = thickness / 2
        wall_left.scale.y = self.depth / 2
        wall_left.scale.z = height / 2
        bpy.ops.mesh.primitive_cube_add(
            size=2, location=(self.width - thickness / 2, self.depth / 2, height / 2)
        )
        wall_right = bpy.context.active_object
        wall_right.scale.x = thickness / 2
        wall_right.scale.y = self.depth / 2
        wall_right.scale.z = height / 2

    def add_window(self, wall, window_width, window_height, window_sill):
        offset = 0.01
        if wall == "front":
            cx = self.width / 2
            cy = self.thickness + offset
            cz = window_sill + window_height / 2
            rot = (math.radians(90), 0, 0)
        elif wall == "back":
            cx = self.width / 2
            cy = self.depth - self.thickness - offset
            cz = window_sill + window_height / 2
            rot = (math.radians(-90), 0, 0)
        elif wall == "left":
            cx = self.thickness + offset
            cy = self.depth / 2
            cz = window_sill + window_height / 2
            rot = (0, math.radians(-90), 0)
        elif wall == "right":
            cx = self.width - self.thickness - offset
            cy = self.depth / 2
            cz = window_sill + window_height / 2
            rot = (0, math.radians(90), 0)
        else:
            return
        bpy.ops.mesh.primitive_plane_add(size=2, location=(cx, cy, cz), rotation=rot)
        window = bpy.context.active_object
        window.scale.x = window_width / 2
        window.scale.y = window_height / 2

    def build(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)
        bpy.ops.wm.save_as_mainfile(filepath=filepath, check_existing=False)
        print(f"Scene saved as {filepath}")
