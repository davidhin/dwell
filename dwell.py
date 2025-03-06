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

    def create_floor(self, vertices):
        self.vertices = vertices
        mesh = bpy.data.meshes.new("Floor")
        floor = bpy.data.objects.new("Floor", mesh)
        bpy.context.collection.objects.link(floor)
        verts = [(x, y, 0) for (x, y) in vertices]
        face = [i for i in range(len(verts))]
        mesh.from_pydata(verts, [], [face])
        mesh.update()
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        self.width = max(xs) - min(xs)
        self.depth = max(ys) - min(ys)

    def create_walls(self, height, thickness):
        self.height = height
        self.thickness = thickness
        for i in range(len(self.vertices)):
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % len(self.vertices)]
            mid_x = (v1[0] + v2[0]) / 2
            mid_y = (v1[1] + v2[1]) / 2
            length = math.sqrt((v2[0] - v1[0]) ** 2 + (v2[1] - v1[1]) ** 2)
            angle = math.atan2(v2[1] - v1[1], v2[0] - v1[0])
            bpy.ops.mesh.primitive_cube_add(
                size=2, location=(mid_x, mid_y, height / 2), rotation=(0, 0, angle)
            )
            wall = bpy.context.active_object
            wall.scale.x = length / 2
            wall.scale.y = thickness / 2
            wall.scale.z = height / 2

    def add_window(self, edge_index, window_width, window_height, sill, offset=0):
        v1 = self.vertices[edge_index]
        v2 = self.vertices[(edge_index + 1) % len(self.vertices)]
        mid_x = (v1[0] + v2[0]) / 2
        mid_y = (v1[1] + v2[1]) / 2
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        length = math.sqrt(dx * dx + dy * dy)
        angle = math.atan2(dy, dx)
        unit_x = dx / length
        unit_y = dy / length
        cx = mid_x + unit_x * offset
        cy = mid_y + unit_y * offset
        bpy.ops.mesh.primitive_plane_add(
            size=2,
            location=(cx, cy, sill + window_height / 2),
            rotation=(math.radians(90), 0, angle),
        )
        window = bpy.context.active_object
        window.scale.x = window_width / 2
        window.scale.y = window_height / 2

    def build(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)
        bpy.ops.wm.save_as_mainfile(filepath=filepath, check_existing=False)
        print(f"Scene saved as {filepath}")
