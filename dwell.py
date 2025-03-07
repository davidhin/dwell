import bpy  # type: ignore
from mathutils import Vector, Matrix  # type: ignore
import numpy as np  # type: ignore
import os
import math
from collections import namedtuple

Wall = namedtuple(
    "Wall",
    ["mid_x", "mid_y", "unit_x", "unit_y", "normal", "length", "angle", "object"],
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
        normal = Vector((-unit_y, unit_x, 0))
        normal.normalize()
        angle = math.atan2(v2[1] - v1[1], v2[0] - v1[0])
        wall_obj = (
            self.wall_objects[edge_index]
            if edge_index < len(self.wall_objects)
            else None
        )
        return Wall(mid_x, mid_y, unit_x, unit_y, normal, length, angle, wall_obj)

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
        self,
        filepath,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
        floor=False,
        snap_line=False,
        wall_edge_index=None,
    ):
        bpy.ops.import_scene.gltf(filepath=filepath)
        imported_objects = bpy.context.selected_objects
        obj = imported_objects[-1]
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
                obj.location.z -= min_z + 0.001

            if snap_line and wall_edge_index is not None:
                wall = self.get_wall(wall_edge_index)
                self.snap_line_to_wall(obj, wall)

    def snap_line_to_wall(self, obj, wall):
        # Update scene and get evaluated object
        bpy.context.view_layer.update()

        # Rotate the object against the wall based on oriented bounding box
        obj.rotation_mode = "XYZ"
        bbox = self.bounding_box_obb(obj)
        obj_unit_vector = (bbox[0] - bbox[2]).normalized()
        angle = math.atan2(
            obj_unit_vector.cross(wall.normal).z, obj_unit_vector.dot(wall.normal)
        )
        obj.rotation_euler = (0, 0, angle)

        # Set initial position
        obj.location.x = wall.mid_x
        obj.location.y = wall.mid_y
        bbox = self.bounding_box_obb(obj)
        offset = (bbox[0] - bbox[2]).length / 2

        # Move back of object against wall
        obj.location.x += wall.normal.x * offset
        obj.location.y += wall.normal.y * offset

        # Offset against wall thickness
        obj.location.x += wall.normal.x * (self.thickness / 2)
        obj.location.y += wall.normal.y * (self.thickness / 2)

    def debug_cube(self, vector):
        bpy.ops.mesh.primitive_cube_add(size=0.1, location=vector)

    def bounding_box_aabb(self, obj):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        return [eval_obj.matrix_world @ Vector(corner) for corner in eval_obj.bound_box]

    # CHATGPT wrote this method
    def bounding_box_obb(self, obj):
        # Get evaluated mesh from the object
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        # Extract vertices in world space
        verts = [obj.matrix_world @ v.co for v in mesh.vertices]
        eval_obj.to_mesh_clear()
        if not verts:
            return None

        # Project vertices onto XY plane (ignoring Z)
        pts = [(v.x, v.y) for v in verts]
        # Remove duplicates and sort points lexicographically
        pts = sorted(set(pts))

        # Compute 2D convex hull using the monotone chain algorithm.
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower = []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        upper = []
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        hull = lower[:-1] + upper[:-1]  # convex hull vertices in order

        if len(hull) < 3:
            # Not enough points for a 2D hull, return AABB in XY
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            min_xy = (min(xs), min(ys))
            max_xy = (max(xs), max(ys))
            rect = [
                Vector((min_xy[0], min_xy[1])),
                Vector((min_xy[0], max_xy[1])),
                Vector((max_xy[0], max_xy[1])),
                Vector((max_xy[0], min_xy[1])),
            ]
        else:
            # Rotating calipers: iterate over hull edges to find minimum area rectangle.
            min_area = None
            best_rect = None
            for i in range(len(hull)):
                # Current edge from hull[i] to hull[(i+1)%len(hull)]
                p1 = Vector(hull[i])
                p2 = Vector(hull[(i + 1) % len(hull)])
                edge_dir = (p2 - p1).normalized()
                # Angle to rotate edge so it aligns with the X axis
                angle = math.atan2(edge_dir.y, edge_dir.x)
                # Create a 2D rotation matrix (for XY)
                rot = Matrix.Rotation(-angle, 2)
                # Rotate all hull points into edge-aligned coordinates
                rotated = [rot @ Vector(pt) for pt in hull]
                xs = [p.x for p in rotated]
                ys = [p.y for p in rotated]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                area = (max_x - min_x) * (max_y - min_y)
                if min_area is None or area < min_area:
                    min_area = area
                    # Rectangle corners in rotated (edge-aligned) space:
                    rect_rot = [
                        Vector((min_x, min_y)),
                        Vector((min_x, max_y)),
                        Vector((max_x, max_y)),
                        Vector((max_x, min_y)),
                    ]
                    # Rotate corners back to world XY coordinates
                    inv_rot = Matrix.Rotation(angle, 2)
                    best_rect = [inv_rot @ p for p in rect_rot]
            rect = best_rect

        # Now, we have the best-fit rectangle in the XY plane as 4 Vectors.
        # Get the Z extents from the original vertices:
        zs = [v.z for v in verts]
        min_z = min(zs)
        max_z = max(zs)

        # Construct the 8 corners of the OBB: combine each rectangle corner with min_z and max_z.
        obb = []
        for corner in rect:
            obb.append(Vector((corner.x, corner.y, min_z)))
            obb.append(Vector((corner.x, corner.y, max_z)))
        return obb

    def build(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)
        bpy.ops.wm.save_as_mainfile(filepath=filepath, check_existing=False)
        print(f"Scene saved as {filepath}")
