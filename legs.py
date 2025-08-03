# Run using /Applications/FreeCAD.app/Contents/MacOS/FreeCAD legs.py
#
# Optional: Add this as a macro in FreeCAD:
# doc = App.ActiveDocument or App.newDocument("Legs")
# for obj in doc.Objects:
#     doc.removeObject(obj.Name)
# exec(open("/Users/davidhin/Documents/dwell/legs.py", encoding="utf-8").read())

import FreeCAD as App
import FreeCADGui
import Draft
from FreeCAD import Vector
import Part


doc = App.ActiveDocument or App.newDocument("Legs")


def main():
    TABLE_WIDTH = 2900
    TABLE_LENGTH = 1100
    TABLE_HEIGHT = 710
    LEG_SECTION_SIZE = 90

    LONG_LEG_WIDTH = 2000
    LONG_LEG_LENGTH = 375

    SHORT_LEG_WIDTH = 300
    SHORT_LEG_LENGTH = 500
    SHORT_LEG_ANGLE_OFFSET = -200

    rect(TABLE_WIDTH, TABLE_LENGTH, Vector(0, 0, TABLE_HEIGHT))

    long_floor_point_a = Vector(-LONG_LEG_WIDTH / 2, -LONG_LEG_LENGTH / 2, 0)
    long_table_point_a = Vector(LONG_LEG_WIDTH / 2, -LONG_LEG_LENGTH / 2, TABLE_HEIGHT)
    leg(
        long_floor_point_a,
        long_table_point_a,
        TABLE_HEIGHT,
        side=LEG_SECTION_SIZE,
        name="Long_A",
    )

    long_floor_point_b = Vector(LONG_LEG_WIDTH / 2, LONG_LEG_LENGTH / 2, 0)
    long_table_point_b = Vector(-LONG_LEG_WIDTH / 2, LONG_LEG_LENGTH / 2, TABLE_HEIGHT)
    leg(
        long_floor_point_b,
        long_table_point_b,
        TABLE_HEIGHT,
        side=LEG_SECTION_SIZE,
        name="Long_B",
    )

    short_floor_point_a = Vector(
        -SHORT_LEG_WIDTH / 2 - SHORT_LEG_ANGLE_OFFSET / 2, -SHORT_LEG_LENGTH / 2, 0
    )
    short_table_point_a = Vector(
        -SHORT_LEG_WIDTH / 2 + SHORT_LEG_ANGLE_OFFSET / 2,
        SHORT_LEG_LENGTH / 2,
        TABLE_HEIGHT,
    )
    leg(
        short_floor_point_a,
        short_table_point_a,
        TABLE_HEIGHT,
        side=LEG_SECTION_SIZE,
        name="Short_A",
    )

    short_floor_point_b = Vector(
        SHORT_LEG_WIDTH / 2 + SHORT_LEG_ANGLE_OFFSET / 2, SHORT_LEG_LENGTH / 2, 0
    )
    short_table_point_b = Vector(
        SHORT_LEG_WIDTH / 2 - SHORT_LEG_ANGLE_OFFSET / 2,
        -SHORT_LEG_LENGTH / 2,
        TABLE_HEIGHT,
    )
    leg(
        short_floor_point_b,
        short_table_point_b,
        TABLE_HEIGHT,
        side=LEG_SECTION_SIZE,
        name="Short_B",
    )

    # Projected length of short leg
    label_distance(
        set_z(long_table_point_a, TABLE_HEIGHT + 15),
        set_z(short_table_point_a, TABLE_HEIGHT + 15),
    )
    label_distance(
        set_z(long_table_point_b, TABLE_HEIGHT + 15),
        set_z(short_table_point_b, TABLE_HEIGHT + 15),
    )
    label_distance(
        set_z(long_table_point_a, TABLE_HEIGHT + 15),
        set_z(short_table_point_b, TABLE_HEIGHT + 15),
    )
    label_distance(
        set_z(long_table_point_b, TABLE_HEIGHT + 15),
        set_z(short_table_point_a, TABLE_HEIGHT + 15),
    )
    label_distance(
        set_z(long_table_point_a, TABLE_HEIGHT + 15),
        set_z(long_table_point_b, TABLE_HEIGHT + 15),
    )
    label_distance(
        set_z(short_table_point_a, TABLE_HEIGHT + 15),
        set_z(short_floor_point_a, TABLE_HEIGHT + 15),
    )
    label_distance(
        set_z(short_table_point_a, TABLE_HEIGHT + 15),
        set_z(short_table_point_b, TABLE_HEIGHT + 15),
        text_gap=40,
    )
    label_distance(
        vertex(App.ActiveDocument.Short_B, "bottom", 0),
        vertex(App.ActiveDocument.Short_B, "top", 0),
    )
    label_distance(
        vertex(App.ActiveDocument.Short_B, "bottom", 0),
        vertex(App.ActiveDocument.Short_B, "bottom", 1),
    )
    label_distance(
        vertex(App.ActiveDocument.Short_B, "bottom", 1),
        vertex(App.ActiveDocument.Short_B, "bottom", 2),
    )

    doc.recompute()


def label_distance(
    p1: Vector,
    p2: Vector,
    gap: float = 1.0,  # line-to-edge offset (mm)
    text_gap: float = 0.0,  # extra offset for the label itself
    fontsize: float = 0.08,
    arrowsize: float = 0.05,
    line_width: float = 0.05,
    keep_upright: bool = True,
    label: str = "Dimension",
):
    # ---------- pick a perpendicular in the XY plane ----------
    direction = p2 - p1
    direction.normalize()
    perp = Vector(1, 0, 0) if abs(direction.y) > abs(direction.x) else Vector(0, 1, 0)

    # position for the dimension-line
    dim_pos = (p1 + p2) * 0.5 + perp * gap

    # ------------------ create the dimension ------------------
    dim = Draft.make_dimension(p1, p2, dim_pos)

    # upright mode if the build supports one
    if keep_upright:
        for m in ("2D", "Flat", "Screen"):
            if m in dim.ViewObject.listDisplayModes():
                dim.ViewObject.DisplayMode = m
                break

    # tiny styling
    dim.ViewObject.FontSize = fontsize
    dim.ViewObject.ArrowSize = arrowsize
    dim.ViewObject.LineWidth = line_width

    # ---------------- move the label itself ------------------
    # label sits on the dim-line + optional extra offset
    dim.ViewObject.TextPosition = dim_pos + perp * text_gap
    dim.Label = label

    App.ActiveDocument.recompute()
    return dim


def vertex(shape, face, index):
    face = max(
        shape.Shape.Faces,
        key=lambda f: (
            f.normalAt(0.5, 0.5).z if face == "top" else -f.normalAt(0.5, 0.5).z
        ),
    )
    return face.Vertexes[index].Point


def set_z(v: Vector, z: float):
    return Vector(v.x, v.y, z)


# ─────────── helper: un-trimmed prism ───────────
def raw_leg(p1: Vector, p2: Vector, side=12):
    OVERLAP = 200
    axis = p2 - p1
    axis.normalize()
    up = Vector(0, 0, 1) if abs(axis.z) < 0.99 else Vector(0, 1, 0)
    x = axis.cross(up)
    x.normalize()
    x *= side / 2
    y = axis.cross(x)
    y.normalize()
    y *= side / 2
    base = [p1 + x + y, p1 + x - y, p1 - x - y, p1 - x + y]
    wire = Part.makePolygon(base + [base[0]])
    return Part.Face(wire).extrude(p2 - p1 + axis * OVERLAP * 2)  # a bit longer


# ─────────── final leg, trimmed flush ───────────
def leg(p1, p2, table_height, side, name):
    OVERLAP = 200
    prism = raw_leg(
        p1 - (p2 - p1).normalize() * OVERLAP, p2 + (p2 - p1).normalize() * OVERLAP, side
    )
    box = Part.makeBox(5000, 5000, table_height, Vector(-5000 / 2, -5000 / 2, 0))
    trimmed = prism.common(box)  # Boolean intersection
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = trimmed
    return obj


def rect(width, height, origin):
    ox, oy, oz = origin.x, origin.y, origin.z
    hw = width / 2
    hh = height / 2
    p0 = App.Vector(ox - hw, oy - hh, oz)
    p1 = App.Vector(ox + hw, oy - hh, oz)
    p2 = App.Vector(ox + hw, oy + hh, oz)
    p3 = App.Vector(ox - hw, oy + hh, oz)
    wire = Part.makePolygon([p0, p1, p2, p3, p0])  # close the loop
    face = Part.Face(wire)
    obj = doc.addObject("Part::Feature", "Rectangle")
    obj.Shape = face
    return obj


main()

# ────────── GUI niceties: grid & axis cross ──────────
if App.GuiUp:

    # 1. Switch to Draft so the grid object exists
    FreeCADGui.activateWorkbench("DraftWorkbench")

    # # 2. Turn the grid *on* (robust to different FreeCAD versions)
    # try:  # 0.20 / 0.21 / 0.22 dev
    #     # toggleGrid() returns True if the grid is *now* visible
    #     if not Draft.toggleGrid():  # grid was already on → nothing to do
    #         pass
    # except AttributeError:  # very old build → use command ID
    #     FreeCADGui.runCommand("Draft_ToggleGrid", 0)

    # FreeCADGui.runCommand("Draft_ToggleGrid", 1)

    # 3. Show the origin axis-cross
    FreeCADGui.ActiveDocument.ActiveView.setAxisCross(False)

    # 4. Fit view so you see everything plus the grid
    # FreeCADGui.SendMsgToActiveView("ViewFit")
