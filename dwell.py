import bpy  # type: ignore
from mathutils import Vector  # type: ignore
import os
import math
from collections import namedtuple

Wall = namedtuple(
    "Wall", ["mid_x", "mid_y", "unit_x", "unit_y", "length", "angle", "object"]
)


class Dwell:
    def __init__(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        self.width = 0
        self.depth = 0
        self.height = 0
        self.thickness = 0
        self.wall_objects = []

    def create_floor(self, vertices):
        self.vertices = vertices
        mesh = bpy.data.meshes.new("Floor")
        floor = bpy.data.objects.new("Floor", mesh)
        bpy.context.collection.objects.link(floor)
        verts = [(x, y, 0) for (x, y) in vertices]
        face = list(range(len(verts)))
        mesh.from_pydata(verts, [], [face])
        mesh.update()
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        self.width = max(xs) - min(xs)
        self.depth = max(ys) - min(ys)

    def get_wall(self, edge_index):
        v1 = self.vertices[edge_index]
        v2 = self.vertices[(edge_index + 1) % len(self.vertices)]
        mid_x = (v1[0] + v2[0]) / 2
        mid_y = (v1[1] + v2[1]) / 2
        length = math.hypot(v2[0] - v1[0], v2[1] - v1[1])
        unit_x = (v2[0] - v1[0]) / length
        unit_y = (v2[1] - v1[1]) / length
        angle = math.atan2(v2[1] - v1[1], v2[0] - v1[0])
        wall_obj = (
            self.wall_objects[edge_index]
            if edge_index < len(self.wall_objects)
            else None
        )
        return Wall(mid_x, mid_y, unit_x, unit_y, length, angle, wall_obj)

    def create_walls(self, height, thickness):
        self.height = height
        self.thickness = thickness
        self.wall_objects = []
        for i in range(len(self.vertices)):
            wall = self.get_wall(i)
            bpy.ops.mesh.primitive_cube_add(
                size=2,
                location=(wall.mid_x, wall.mid_y, height / 2),
                rotation=(0, 0, wall.angle),
            )
            wall_obj = bpy.context.active_object
            wall_obj.scale.x = wall.length / 2
            wall_obj.scale.y = thickness / 2
            wall_obj.scale.z = height / 2
            self.wall_objects.append(wall_obj)

    def add_window(self, edge_index, window_width, window_height, sill, offset=0):
        wall = self.get_wall(edge_index)
        cx = wall.mid_x + wall.unit_x * offset
        cy = wall.mid_y + wall.unit_y * offset
        bpy.ops.mesh.primitive_plane_add(
            size=2,
            location=(cx, cy, sill + window_height / 2),
            rotation=(math.radians(90), 0, wall.angle),
        )
        window = bpy.context.active_object
        window.scale.x = window_width / 2
        window.scale.y = window_height / 2

    def add_opening(self, edge_index, opening_width, opening_height, sill=0, offset=0):
        wall = self.get_wall(edge_index)
        cx = wall.mid_x + wall.unit_x * offset
        cy = wall.mid_y + wall.unit_y * offset
        opening_center = (cx, cy, sill + opening_height / 2)
        bpy.ops.mesh.primitive_cube_add(
            size=2, location=opening_center, rotation=(0, 0, wall.angle)
        )
        opening_obj = bpy.context.active_object
        opening_obj.scale.x = opening_width / 2
        opening_obj.scale.y = self.thickness / 2 * 1.1
        opening_obj.scale.z = opening_height / 2
        mod = wall.object.modifiers.new(name="OpeningCutout", type="BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = opening_obj
        bpy.context.view_layer.objects.active = wall.object
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(opening_obj, do_unlink=True)

    def add_glb_model(
        self, filepath, location, rotation=(0, 0, 0), scale=(1, 1, 1), floor=False
    ):
        bpy.ops.import_scene.gltf(filepath=filepath)
        imported_objects = bpy.context.selected_objects
        obj = imported_objects[0]
        if obj:
            obj.location = location
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = rotation
            obj.scale = scale

            if floor:
                bpy.context.view_layer.update()
                depsgraph = bpy.context.evaluated_depsgraph_get()
                eval_obj = obj.evaluated_get(depsgraph)
                bbox = [
                    eval_obj.matrix_world @ Vector(corner)
                    for corner in eval_obj.bound_box
                ]
                min_z = min(v.z for v in bbox)
                obj.location.z -= min_z + 0.001  # adding a tiny epsilon to avoid gaps

    def build(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)
        bpy.ops.wm.save_as_mainfile(filepath=filepath, check_existing=False)
        print(f"Scene saved as {filepath}")
