# -*- coding: utf-8 -*-
"""
สร้างแบบติดตั้งระบบกล้องวงจรปิด CCTV – บ้านคุณพอล (25/11/2026)
ถอดจากแบบร่างมือ 32831.jpg

ขนาดทั้งหมดเป็น "ขนาดโดยประมาณ" ที่ย่อขยายจากสัดส่วนแบบร่าง
โดยกำหนด FL1 กว้าง ≈16.0 ม. (ตามที่ลูกค้าให้ประมาณให้)
เมื่อวัดหน้างานแล้ว แก้ค่าพิกัดในส่วน PLAN DATA / CAMERA DATA แล้วรันใหม่:
    python generate_cctv.py
ผลลัพธ์: DXF (AutoCAD 2D), PDF ชุดแบบ, PNG รายแผ่น, CSV ตารางกล้อง
"""
import math, csv, os
from shapely.geometry import LineString, Polygon, box, MultiPolygon
from shapely.ops import unary_union
import ezdxf
from ezdxf.enums import TextEntityAlignment, MTextEntityAlignment
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon as MPoly, Rectangle, Arc
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
for f in ("tahoma.ttf", "tahomabd.ttf"):
    p = os.path.join(r"C:\Windows\Fonts", f)
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams["font.family"] = "Tahoma"

PROJECT = "บ้านคุณพอล"
DATE = "25/11/2026"
APX = "≈"

# =====================================================================
# PLAN DATA  (หน่วย: เมตร, จุดอ้างอิง 0,0 = มุมซ้ายล่างของแต่ละแปลน)
# =====================================================================
EXT, INT = 0.20, 0.12


class Plan:
    def __init__(self, key, title, offset, footprint, walls, openings=(), dashed=(),
                 rooms=(), furn=(), doors=(), stairs=(), dims=(), parking=None):
        self.key, self.title, self.offset = key, title, offset
        self.footprint, self.walls, self.openings = footprint, walls, openings
        self.dashed, self.rooms, self.furn, self.doors = dashed, rooms, furn, doors
        self.stairs, self.dims, self.parking = stairs, dims, parking
        polys = [LineString([(a, b), (c, d)]).buffer(t / 2, cap_style="square", join_style="mitre")
                 for a, b, c, d, t in walls]
        u = unary_union(polys)
        for o in openings:
            u = u.difference(box(*o))
        self.wall_geom = u
        self.obst = u.boundary
        self.floor = footprint.difference(u)


FL1 = Plan(
    "FL1", "แปลนชั้น 1 (FL1-IN)", (0, 0),
    Polygon([(0, 0), (16, 0), (16, 7.4), (14.5, 7.4), (14.5, 12), (0, 12)]),
    walls=[
        (0, 0, 0, 12, EXT), (0, 12, 14.5, 12, EXT), (14.5, 12, 14.5, 7.4, EXT),
        (14.5, 7.4, 16, 7.4, EXT), (16, 7.4, 16, 1.8, EXT), (0, 1.8, 16, 1.8, EXT),
        (0, 8.7, 14.5, 8.7, INT), (2.2, 1.8, 2.2, 8.7, INT),
        (3.5, 8.7, 3.5, 12, INT), (6.3, 8.7, 6.3, 12, INT),
        (9.0, 8.7, 9.0, 12, INT), (11.0, 8.7, 11.0, 12, INT),
    ],
    openings=[(5.6, 1.6, 7.8, 2.0),      # ประตูทางเข้าหลัก (บานคู่)
              (11.8, 8.55, 12.7, 8.85),  # ประตูห้อง 5 (ตามแบบร่าง)
              (2.0, 3.6, 2.4, 4.6)],     # ช่องเปิดทางเดินข้าง
    dashed=[((0, 0), (16, 0), "แนวขอบหลังคากันสาด / ขอบทางเดิน"),
            ((14.3, 1.8), (14.3, 7.4), "แนวช่องเปิด/เสา")],
    rooms=[
        ("ห้อง 1", box(0, 8.7, 3.5, 12), None),
        ("ห้อง 2", box(3.5, 8.7, 6.3, 12), None),
        ("ห้อง 3", box(6.3, 8.7, 9.0, 12), None),
        ("ห้อง 4\n(เสนอเป็นห้อง NVR)", box(9.0, 8.7, 11.0, 12), (10.0, 10.1)),
        ("ห้อง 5", box(11.0, 8.7, 14.5, 12), (13.0, 10.6)),
        ("พื้นที่ขายสินค้า", Polygon([(2.2, 1.8), (16, 1.8), (16, 7.4), (14.5, 7.4), (14.5, 8.7), (2.2, 8.7)]), (12.0, 3.0)),
        ("ทางเดินข้าง", box(0, 1.8, 2.2, 8.7), (1.1, 6.2)),
        ("ทางเดินหน้าร้าน (มีหลังคาคลุม)", box(0, 0, 16, 1.8), (12.2, 0.9)),
    ],
    furn=[(2.7, 6.3, 5.9, 0.5, "ชั้นวาง 1"), (3.5, 3.7, 5.4, 0.5, "ชั้นวาง 2"),
          (11.5, 5.6, 2.2, 0.45, "ชั้นวาง 3"), (2.95, 4.8, 0.95, 0.4, "โต๊ะ"),
          (8.3, 5.15, 1.0, 0.35, "โต๊ะ")],
    doors=[(11.8, 8.7, 0.9, 0, 1), (5.6, 1.8, 1.1, 0, 1), (7.8, 1.8, 1.1, 180, -1)],
    dims=[  # (x1,y1,x2,y2, ตำแหน่งเส้นบอกขนาด, แนว h/v)
        (0, 0, 16, 0, -1.5, "h"), (0, 0, 2.2, 0, -0.75, "h"), (2.2, 0, 5.6, 0, -0.75, "h"),
        (5.6, 0, 7.8, 0, -0.75, "h"), (7.8, 0, 14.3, 0, -0.75, "h"), (14.3, 0, 16, 0, -0.75, "h"),
        (0, 12, 3.5, 12, 12.75, "h"), (3.5, 12, 6.3, 12, 12.75, "h"), (6.3, 12, 9.0, 12, 12.75, "h"),
        (9.0, 12, 11.0, 12, 12.75, "h"), (11.0, 12, 14.5, 12, 12.75, "h"), (0, 12, 14.5, 12, 13.5, "h"),
        (0, 0, 0, 1.8, -0.85, "v"), (0, 1.8, 0, 8.7, -0.85, "v"), (0, 8.7, 0, 12, -0.85, "v"),
        (0, 0, 0, 12, -1.65, "v"), (16, 0, 16, 7.4, 21.2, "v"),
        (16.6, 10, 20.4, 10, 10.7, "h"),
    ],
    parking=(16.6, 0, 20.4, 10),
)

FL2 = Plan(
    "FL2", "แปลนชั้น 2 (FL2-IN)", (26, 0),
    box(0, 0, 14, 11.5),
    walls=[(0, 0, 14, 0, EXT), (14, 0, 14, 11.5, EXT), (14, 11.5, 0, 11.5, EXT), (0, 11.5, 0, 0, EXT),
           (2.1, 0, 2.1, 7.2, INT)],
    openings=[(-0.2, 2.0, 0.2, 3.2)],
    dashed=[((0, 6.7), (14, 8.8), "แนวคาน/เส้นประตามแบบร่าง")],
    rooms=[("FL2 – โซน A", Polygon([(0, 6.7), (14, 8.8), (14, 11.5), (0, 11.5)]), (11.4, 10.0)),
           ("FL2 – โซน B", box(0, 0, 2.1, 6.95), (1.05, 4.8)),
           ("FL2 – โซน C (พื้นที่หลัก)", Polygon([(2.1, 0), (14, 0), (14, 8.8), (2.1, 7.0)]), (8.0, 3.6))],
    dims=[(0, 0, 14, 0, -1.4, "h"), (0, 0, 2.1, 0, -0.7, "h"), (2.1, 0, 14, 0, -0.7, "h"),
          (0, 0, 0, 11.5, -1.0, "v")],
)

ST1 = Plan("ST1", "โถงบันได FL1", (0, -11), box(0, 0, 5.3, 6.1),
           walls=[(0, 0, 5.3, 0, EXT), (5.3, 0, 5.3, 6.1, EXT), (5.3, 6.1, 0, 6.1, EXT), (0, 6.1, 0, 0, EXT)],
           rooms=[("โถงบันได FL1", box(0, 0, 5.3, 6.1), (3.4, 3.0))],
           stairs=[(0.2, 0.3, 1.25, 3.4, "ขึ้น")],
           dims=[(0, 0, 5.3, 0, -0.7, "h"), (0, 0, 0, 6.1, -0.7, "v")])
ST2 = Plan("ST2", "โถงบันได FL2", (7.5, -11), box(0, 0, 5.3, 4.9),
           walls=[(0, 0, 5.3, 0, EXT), (5.3, 0, 5.3, 4.9, EXT), (5.3, 4.9, 0, 4.9, EXT), (0, 4.9, 0, 0, EXT)],
           rooms=[("โถงบันได FL2", box(0, 0, 5.3, 4.9), (3.3, 3.1))],
           stairs=[(0.2, 0.25, 1.2, 2.9, "ลง")],
           dims=[(0, 0, 5.3, 0, -0.7, "h"), (0, 0, 0, 4.9, -0.7, "v")])
CA = Plan("CA", "ทางเดิน A (FL2)", (15, -7.5), box(0, 0, 10, 1.9),
          walls=[(0, 0, 10, 0, EXT), (10, 0, 10, 1.9, EXT), (10, 1.9, 0, 1.9, EXT), (0, 1.9, 0, 0, EXT)],
          rooms=[("ทางเดิน A (FL2)", box(0, 0, 10, 1.9), (8.4, 0.95))],
          dims=[(0, 0, 10, 0, -0.6, "h"), (0, 0, 0, 1.9, -0.6, "v")])
CB = Plan("CB", "ทางเดิน B", (15, -11.5), box(0, 0, 11.2, 1.8),
          walls=[(0, 0, 11.2, 0, EXT), (11.2, 0, 11.2, 1.8, EXT), (11.2, 1.8, 0, 1.8, EXT), (0, 1.8, 0, 0, EXT)],
          rooms=[("ทางเดิน B", box(0, 0, 11.2, 1.8), (9.6, 0.9))],
          dims=[(0, 0, 11.2, 0, -0.6, "h"), (0, 0, 0, 1.8, -0.6, "v")])

PLANS = {p.key: p for p in (FL1, FL2, ST1, ST2, CA, CB)}

# =====================================================================
# CAMERA DATA  (ทิศ: 0°=ขวา/ตะวันออกของแบบ, 90°=ขึ้น/ด้านหลังอาคาร)
# =====================================================================
TYPES = {
    "Dome":   dict(color="#1f6fd1", desc="Dome 4MP IR (ติดฝ้า ภายใน)"),
    "Turret": dict(color="#13985a", desc="Turret 4MP IR (ใต้ชายคา/ทางเดิน)"),
    "Bullet": dict(color="#e07b00", desc="Bullet 4MP IR IP67 (ภายนอก)"),
}


def C(cid, plan, x, y, d, typ, lens, hfov, rng, area, outdoor=False):
    return dict(id=cid, plan=plan, x=x, y=y, dir=d, type=typ, lens=lens, hfov=hfov, rng=rng,
                area=area, outdoor=outdoor, h=3.0 if outdoor else 2.8)


LABEL_OFFSET = {  # ปรับตำแหน่งป้ายชื่อกล้องที่ซ้อนกัน (dx, dy จากตัวกล้อง)
    "CAM-17": (-0.8, -0.55), "CAM-18": (0.85, -0.5), "CAM-03": (0.55, 0.5), "CAM-04": (-0.55, 0.5), "CAM-26": (-0.6, 0.55), "CAM-27": (0.6, 0.55),
}


CAMS = [
    C("CAM-01", "FL1", 16.25, 3.0, 60, "Bullet", "4MP 2.8–12mm VF", 60, 22, "ลานจอดรถ / ทางรถเข้า", True),
    C("CAM-02", "FL1", 15.7, 0.5, 195, "Bullet", "4MP 4mm", 85, 15, "ทางเดินหน้าร้านฝั่งขวา / มุมลานจอด", True),
    C("CAM-03", "FL1", 6.0, 0.4, 0, "Turret", "4MP 2.8mm", 100, 12, "หน้าร้าน (มองไปทางขวา)", True),
    C("CAM-04", "FL1", 5.0, 0.4, 180, "Turret", "4MP 2.8mm", 100, 12, "หน้าร้าน (มองไปทางซ้าย)", True),
    C("CAM-05", "FL1", 6.7, 2.5, 270, "Dome", "4MP 2.8mm", 100, 8, "ประตูทางเข้าหลัก (จับหน้าคนเข้า-ออก)"),
    C("CAM-06", "FL1", 8.4, 2.25, 140, "Dome", "4MP 2.8mm", 100, 12, "พื้นที่ขายด้านหน้า / หน้าชั้นวาง 2"),
    C("CAM-07", "FL1", 8.6, 0.4, 0, "Turret", "4MP 2.8mm", 100, 12, "ทางเดินหน้าร้าน (ไปทางลานจอด)", True),
    C("CAM-08", "FL1", 15.6, 5.3, 180, "Dome", "4MP 4mm", 85, 14, "พื้นที่ขายฝั่งขวา (มองเข้าร้าน)"),
    C("CAM-09", "FL1", 15.6, 3.6, 200, "Dome", "4MP 2.8mm", 100, 10, "มุมหน้า-ขวาภายในร้าน"),
    C("CAM-10", "FL1", 9.6, 4.6, 175, "Dome", "4MP 4mm", 85, 14, "ทางเดินระหว่างชั้นวาง 1–2"),
    C("CAM-11", "FL1", 10.0, 6.2, 30, "Dome", "4MP 2.8mm", 100, 10, "พื้นที่ขายหลัง-ขวา / หน้าห้อง 5"),
    C("CAM-12", "FL1", 12.7, 7.9, 270, "Dome", "4MP 2.8mm", 100, 10, "พื้นที่ขายฝั่งขวา / ชั้นวาง 3"),
    C("CAM-13", "FL1", 9.2, 7.5, 180, "Dome", "4MP 4mm", 85, 14, "ทางเดินหลังชั้นวาง 1 / หน้าห้อง 1–3"),
    C("CAM-14", "FL1", 0.6, 2.2, 90, "Turret", "4MP 4mm", 85, 14, "ทางเดินข้างซ้าย"),
    C("CAM-15", "FL1", 0.5, 11.5, -40, "Dome", "4MP 2.8mm", 100, 6, "ห้อง 1"),
    C("CAM-16", "FL1", 6.0, 9.3, 160, "Dome", "4MP 2.8mm", 100, 6, "ห้อง 2"),
    C("CAM-17", "FL1", 8.7, 11.6, 200, "Dome", "4MP 2.8mm", 100, 6, "ห้อง 3"),
    C("CAM-18", "FL1", 9.3, 11.6, -30, "Dome", "4MP 2.8mm", 100, 6, "ห้อง 4 (ห้อง NVR/Rack)"),
    C("CAM-19", "FL2", 8.0, 10.8, 200, "Dome", "4MP 2.8mm", 100, 10, "FL2 โซน A ฝั่งขวา"),
    C("CAM-20", "FL2", 5.3, 10.6, 0, "Dome", "4MP 2.8mm", 100, 10, "FL2 โซน A กลาง-ขวา"),
    C("CAM-21", "FL2", 4.2, 8.2, 90, "Dome", "4MP 2.8mm", 100, 8, "FL2 โซน A (แนวคาน)"),
    C("CAM-22", "FL2", 2.9, 9.2, 180, "Dome", "4MP 2.8mm", 100, 8, "FL2 โซน A ฝั่งซ้าย"),
    C("CAM-23", "FL2", 1.0, 9.2, -20, "Dome", "4MP 2.8mm", 100, 10, "FL2 โซน A มุมซ้าย"),
    C("CAM-24", "ST1", 0.4, 5.7, -45, "Dome", "4MP 2.8mm", 100, 8, "โถงบันได FL1"),
    C("CAM-25", "ST2", 4.9, 0.4, 135, "Dome", "4MP 2.8mm", 100, 8, "โถงบันได FL2"),
    C("CAM-26", "CA", 4.2, 0.95, 180, "Turret", "4MP 4mm", 85, 12, "ทางเดิน A (มองซ้าย)"),
    C("CAM-27", "CA", 5.8, 0.95, 0, "Turret", "4MP 4mm", 85, 12, "ทางเดิน A (มองขวา)"),
    C("CAM-28", "CB", 4.1, 0.9, 180, "Turret", "4MP 4mm", 85, 12, "ทางเดิน B (มองซ้าย)"),
    C("CAM-29", "CB", 7.0, 0.9, 0, "Turret", "4MP 4mm", 85, 12, "ทางเดิน B (มองขวา)"),
    C("CAM-30", "FL1", 11.6, 11.6, -75, "Dome", "4MP 2.8mm", 100, 6, "ห้อง 5 / ประตูห้อง 5 (*เลขในแบบร่างอ่านไม่ชัด)"),
]

# =====================================================================
# EQUIPMENT & CABLING
# =====================================================================
EQUIP = {
    "RACK-1": dict(plan="FL1", x=10.55, y=9.1, w=0.6, d=0.4,
                   text="RACK-1  (ตู้ Rack 12U ติดผนัง)\nNVR 32CH + PoE SW 24P + UPS"),
    "RACK-2": dict(plan="FL2", x=10.8, y=11.1, w=0.5, d=0.3,
                   text="RACK-2  (ตู้ Rack 6U ติดผนัง)\nPoE SW 16P"),
}
RISER = {"FL1": (9.3, 9.05), "FL2": (11.4, 11.15)}
TRUNK = {  # name: (plan, y, xmin, xmax)
    "FL1-MAIN": ("FL1", 8.35, 0.4, 14.2),
    "FL1-BACK": ("FL1", 11.7, 0.4, 14.2),
    "FL2-MAIN": ("FL2", 11.1, 0.4, 13.6),
}
FLOOR_H = 3.5      # ความสูงชั้น (สมมติ) สำหรับท่อ Riser
DROP_ALLOW = 3.0   # สายขึ้น/ลงตู้ + ลงหัวกล้อง + Service loop (ม.)
SLACK = 1.10       # เผื่อ 10%
EST_DETAIL_LEN = 30  # ระยะประมาณสำหรับกล้องในแบบขยาย (ยังไม่ทราบตำแหน่งจริงในอาคาร)


def path_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def route_for(cam):
    p = cam["plan"]
    if p == "FL1":
        r = EQUIP["RACK-1"]
        tname = "FL1-BACK" if cam["y"] > 8.7 else "FL1-MAIN"
        _, ty, x0, x1 = TRUNK[tname]
        xr = min(max(cam["x"], x0), x1)
        return [(r["x"], r["y"]), (r["x"], ty), (xr, ty), (xr, cam["y"]), (cam["x"], cam["y"])]
    if p == "FL2":
        r = EQUIP["RACK-2"]
        _, ty, x0, x1 = TRUNK["FL2-MAIN"]
        xr = min(max(cam["x"], x0), x1)
        return [(r["x"], r["y"]), (xr, ty), (xr, cam["y"]), (cam["x"], cam["y"])]
    return None


ports = {"SW1": 0, "SW2": 0}
for cam in CAMS:
    rt = route_for(cam)
    cam["route"] = rt
    if rt:
        cam["len"] = math.ceil((path_len(rt) + DROP_ALLOW) * SLACK)
        cam["est"] = False
    else:
        cam["len"] = EST_DETAIL_LEN
        cam["est"] = True
    sw = "SW1" if cam["plan"] in ("FL1", "ST1") else "SW2"
    ports[sw] += 1
    cam["sw"], cam["port"] = sw, ports[sw]

UPLINK_LEN = math.ceil((math.dist((EQUIP["RACK-1"]["x"], EQUIP["RACK-1"]["y"]), RISER["FL1"]) +
                        FLOOR_H + math.dist(RISER["FL2"], (EQUIP["RACK-2"]["x"], EQUIP["RACK-2"]["y"])) +
                        DROP_ALLOW) * SLACK)

# =====================================================================
# FIELD OF VIEW (ray-cast against walls)
# =====================================================================


def visibility(cam):
    plan = PLANS[cam["plan"]]
    cx, cy, R = cam["x"], cam["y"], cam["rng"]
    n = int(cam["hfov"])
    pts = [(cx, cy)]
    for i in range(n + 1):
        a = math.radians(cam["dir"] - cam["hfov"] / 2 + cam["hfov"] * i / n)
        ex, ey = cx + R * math.cos(a), cy + R * math.sin(a)
        inter = LineString([(cx, cy), (ex, ey)]).intersection(plan.obst)
        best, bd = (ex, ey), R
        if not inter.is_empty:
            for g in getattr(inter, "geoms", [inter]):
                for c in g.coords:
                    dd = math.dist((cx, cy), c)
                    if 1e-6 < dd < bd:
                        bd, best = dd, c
        pts.append(best)
    return Polygon(pts).buffer(0)


SITE_CLIP = {"FL1": box(-0.3, -2.0, 20.4, 12.1)}  # ตัด FOV ภายนอกไม่ให้เกินขอบเขตแบบ
for cam in CAMS:
    cam["fov"] = visibility(cam)
    clip = SITE_CLIP.get(cam["plan"], PLANS[cam["plan"]].footprint)
    cam["fov"] = cam["fov"].intersection(clip)
    if cam["fov"].geom_type != "Polygon":
        cam["fov"] = max(geoms(cam["fov"]), key=lambda g: g.area)

COVER = {}
for key, plan in PLANS.items():
    fovs = [c["fov"] for c in CAMS if c["plan"] == key]
    cov = unary_union(fovs) if fovs else Polygon()
    blind = plan.floor.difference(cov).buffer(-0.08).buffer(0.08)
    blind = unary_union([g for g in getattr(blind, "geoms", [blind]) if g.area > 0.4]) if not blind.is_empty else blind
    COVER[key] = dict(cov=cov, blind=blind,
                      pct=100 * (1 - blind.area / plan.floor.area))

FOV_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2",
              "#17becf", "#bcbd22", "#7f7f7f", "#393b79", "#ad494a", "#637939", "#8c6d31"]
for i, cam in enumerate(CAMS):
    cam["fcol"] = FOV_COLORS[i % len(FOV_COLORS)]


def geoms(g):
    if g.is_empty:
        return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]


# =====================================================================
# MATPLOTLIB DRAWING
# =====================================================================

def poly_patch(g, **kw):
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    from shapely.geometry.polygon import orient
    g = orient(g, 1.0)
    verts, codes = [], []
    for ring in [g.exterior] + list(g.interiors):
        pts = list(ring.coords)
        verts += pts
        codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
    return PathPatch(Path(verts, codes), **kw)


def cam_shape(x, y, d, s=1.0):
    body = [(-0.3, -0.14), (0.05, -0.14), (0.05, 0.14), (-0.3, 0.14)]
    lens = [(0.05, 0), (0.32, 0.18), (0.32, -0.18)]
    a = math.radians(d)
    rot = lambda pts: [(x + s * (px * math.cos(a) - py * math.sin(a)), y + s * (px * math.sin(a) + py * math.cos(a))) for px, py in pts]
    return rot(body), rot(lens)


def draw_cam(ax, cam, label_extra="", s=1.0, fs=6.5):
    col = TYPES[cam["type"]]["color"]
    b, l = cam_shape(cam["x"], cam["y"], cam["dir"], s)
    ax.add_patch(MPoly(b, closed=True, fc=col, ec="k", lw=0.5, zorder=20))
    ax.add_patch(MPoly(l, closed=True, fc="white", ec=col, lw=0.9, zorder=20))
    a = math.radians(cam["dir"] + 180)
    tx, ty = cam["x"] + 0.62 * s * math.cos(a), cam["y"] + 0.62 * s * math.sin(a)
    if cam["id"] in LABEL_OFFSET:
        tx, ty = cam["x"] + LABEL_OFFSET[cam["id"]][0], cam["y"] + LABEL_OFFSET[cam["id"]][1]
    ax.text(tx, ty, cam["id"].replace("CAM-", "CAM-") + label_extra, fontsize=fs, ha="center", va="center",
            zorder=25, color=col, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=col, lw=0.5, alpha=0.92))


def draw_dim(ax, d, fs=6):
    x1, y1, x2, y2, off, o = d
    col = "#555"
    if o == "h":
        ax.plot([x1, x2], [off, off], color=col, lw=0.5)
        for x, y in ((x1, y1), (x2, y2)):
            ax.plot([x, x], [y, off], color=col, lw=0.3, ls=":")
            ax.plot([x - 0.1, x + 0.1], [off - 0.1, off + 0.1], color=col, lw=0.8)
        ax.text((x1 + x2) / 2, off + 0.08, f"{APX}{abs(x2 - x1):.2f}", fontsize=fs, ha="center", va="bottom", color="#333")
    else:
        ax.plot([off, off], [y1, y2], color=col, lw=0.5)
        for x, y in ((x1, y1), (x2, y2)):
            ax.plot([x, off], [y, y], color=col, lw=0.3, ls=":")
            ax.plot([off - 0.1, off + 0.1], [y - 0.1, y + 0.1], color=col, lw=0.8)
        ax.text(off - 0.08, (y1 + y2) / 2, f"{APX}{abs(y2 - y1):.2f}", fontsize=fs, ha="right", va="center",
                rotation=90, color="#333")


def draw_plan(ax, plan, mode="pos", fs=6.5, cam_scale=1.0, show_dims=True):
    # floor
    for g in geoms(plan.footprint):
        ax.add_patch(MPoly(list(g.exterior.coords), closed=True, fc="#fbfaf6", ec="none", zorder=0))
    if plan.parking:
        x0, y0, x1, y1 = plan.parking
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#f2f2f2", ec="#888", hatch="////", lw=0.6, zorder=0))
        ax.plot([x1, x1], [y0 - 0.3, y1 + 0.3], color="#555", lw=1.2)
        ax.text((x0 + x1) / 2, y1 - 1.3, "ลานจอดรถ /\nทางรถเข้า", ha="center", va="center", fontsize=fs + 1,
                fontweight="bold", color="#444", bbox=dict(fc="white", ec="none", alpha=0.85))
        ax.text(x1 + 0.15, 5.0, "แนวขอบเขต/รั้ว\n(ตามแบบร่าง)", rotation=90, fontsize=fs - 1, va="center", color="#555")
    # FOV
    if mode == "fov":
        for cam in CAMS:
            if cam["plan"] != plan.key:
                continue
            for g in geoms(cam["fov"]):
                ax.add_patch(MPoly(list(g.exterior.coords), closed=True, fc=cam["fcol"], ec=cam["fcol"],
                                   alpha=0.16, lw=0.6, zorder=2))
        for g in geoms(COVER[plan.key]["blind"]):
            ax.add_patch(poly_patch(g, fc="none", ec="#d00000", hatch="xxx", lw=0.5, zorder=3))
    # furniture
    for x, y, w, h, t in plan.furn:
        ax.add_patch(Rectangle((x, y), w, h, fc="#e6e1d6", ec="#7a7062", lw=0.6, zorder=4))
        ax.text(x + w / 2, y + h / 2, t, fontsize=fs - 1.5, ha="center", va="center", color="#5a5040", zorder=5)
    for x0, y0, x1, y1, t in plan.stairs:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec="#333", lw=0.6, zorder=4))
        yy = y0
        while yy < y1:
            ax.plot([x0, x1], [yy, yy], color="#333", lw=0.4, zorder=5)
            yy += 0.25
        ax.annotate("", xy=((x0 + x1) / 2, y1 - 0.2), xytext=((x0 + x1) / 2, y0 + 0.2),
                    arrowprops=dict(arrowstyle="->", lw=0.8), zorder=6)
        ax.text(x1 + 0.1, (y0 + y1) / 2, f"บันได ({t})", fontsize=fs - 1, rotation=90, va="center")
    # walls
    for g in geoms(plan.wall_geom):
        ax.add_patch(poly_patch(g, fc="#3a3a3a", ec="#111", lw=0.4, zorder=10))
    for p1, p2, t in plan.dashed:
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#666", lw=0.8, ls=(0, (5, 3)), zorder=9)
    # doors
    for hx, hy, w, wa, sw in plan.doors:
        end = wa + 90 * sw
        ax.plot([hx, hx + w * math.cos(math.radians(end))], [hy, hy + w * math.sin(math.radians(end))],
                color="#7a3b00", lw=1.0, zorder=11)
        ax.add_patch(Arc((hx, hy), 2 * w, 2 * w, theta1=min(wa, end), theta2=max(wa, end), color="#7a3b00",
                         lw=0.5, ls="--", zorder=11))
    # room labels
    for name, poly, pos in plan.rooms:
        px, py = pos if pos else (poly.centroid.x, poly.centroid.y)
        ax.text(px, py, f"{name}\n{APX}{poly.area:.1f} ตร.ม.", fontsize=fs, ha="center", va="center", color="#222",
                zorder=8, linespacing=1.2)
    # cabling
    if mode == "cable":
        for tname, (pk, ty, x0, x1) in TRUNK.items():
            if pk == plan.key:
                ax.plot([x0, x1], [ty, ty], color="#c000c0", lw=4, alpha=0.25, solid_capstyle="butt", zorder=12)
        for cam in CAMS:
            if cam["plan"] == plan.key and cam["route"]:
                xs, ys = zip(*cam["route"])
                ax.plot(xs, ys, color="#d00000", lw=0.6, zorder=13)
        if plan.key in RISER:
            rx, ry = RISER[plan.key]
            ax.add_patch(plt.Circle((rx, ry), 0.18, fc="#ffd400", ec="k", lw=0.6, zorder=16))
            ax.text(rx + 0.25, ry + 0.25, "RISER", fontsize=fs - 1.5, va="bottom", zorder=16)
            rk = EQUIP["RACK-1" if plan.key == "FL1" else "RACK-2"]
            ax.plot([rk["x"], rx], [rk["y"], ry], color="#0050c8", lw=1.4, ls="--", zorder=14)
    # equipment
    for ek, e in EQUIP.items():
        if e["plan"] == plan.key:
            ax.add_patch(Rectangle((e["x"] - e["w"] / 2, e["y"] - e["d"] / 2), e["w"], e["d"], fc="#0050c8",
                                   ec="k", lw=0.6, zorder=18))
            ax.text(e["x"], e["y"], "NVR" if ek == "RACK-1" else "SW", color="white", fontsize=fs - 2,
                    ha="center", va="center", zorder=19, fontweight="bold")
            if mode in ("cable", "pos"):
                ax.annotate(e["text"], xy=(e["x"], e["y"]), xytext=(15.0, 10.9) if plan.key == "FL1" else (e["x"] - 3.2, e["y"] - 1.9),
                            fontsize=fs - 1, color="#0050c8", zorder=30,
                            arrowprops=dict(arrowstyle="-", color="#0050c8", lw=0.5),
                            bbox=dict(fc="white", ec="#0050c8", lw=0.4, alpha=0.95))
    # cameras
    for cam in CAMS:
        if cam["plan"] == plan.key:
            extra = f"\n{cam['len']} ม." + ("*" if cam["est"] else "") if mode == "cable" else ""
            draw_cam(ax, cam, extra, s=cam_scale, fs=fs)
            if mode == "pos":
                a = math.radians(cam["dir"])
                ax.annotate("", xy=(cam["x"] + 1.2 * math.cos(a), cam["y"] + 1.2 * math.sin(a)),
                            xytext=(cam["x"] + 0.35 * math.cos(a), cam["y"] + 0.35 * math.sin(a)),
                            arrowprops=dict(arrowstyle="-|>", color=TYPES[cam["type"]]["color"], lw=0.8), zorder=19)
    if show_dims:
        for d in plan.dims:
            draw_dim(ax, d, fs=fs - 1)
    ax.set_aspect("equal")
    ax.axis("off")


def frame(sheet_no, title, total):
    fig = plt.figure(figsize=(16.54, 11.69))
    fig.patches.append(Rectangle((0.008, 0.01), 0.984, 0.98, transform=fig.transFigure, fill=False, lw=1.5, ec="k"))
    tb = fig.add_axes([0.008, 0.01, 0.984, 0.075])
    tb.set_xlim(0, 100); tb.set_ylim(0, 10); tb.axis("off")
    tb.add_patch(Rectangle((0, 0), 100, 10, fill=False, lw=1.2))
    cols = [(0, 16, "LOTUS TECHNOLOGY", "ผู้ออกแบบระบบ CCTV"),
            (16, 46, f"โครงการ: ติดตั้งระบบกล้องวงจรปิด CCTV – {PROJECT}", "แบบติดตั้ง (Preliminary – ขนาดโดยประมาณ ต้องวัดยืนยันหน้างาน)"),
            (46, 74, title, "ชื่อแบบ"),
            (74, 86, "ไม่ได้มาตราส่วน\nหน่วย: เมตร", "มาตราส่วน"),
            (86, 93, DATE, "วันที่ / Rev.A"),
            (93, 100, f"{sheet_no}/{total}", "แผ่นที่")]
    for x0, x1, big, small in cols:
        tb.plot([x0, x0], [0, 10], color="k", lw=0.8)
        tb.text(x0 + 0.5, 8.6, small, fontsize=7, color="#555", va="top")
        tb.text((x0 + x1) / 2, 4.0, big, fontsize=11 if len(big) < 40 else 9.5, ha="center", va="center",
                fontweight="bold")
    return fig


def legend_axes(fig, rect, mode, extra_notes=()):
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 10); ax.set_ylim(0, 40); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 10, 40, fill=False, lw=0.8))
    y = 38.8
    ax.text(0.3, y, "สัญลักษณ์ (Legend)", fontsize=10, fontweight="bold", va="top"); y -= 1.6
    for t, v in TYPES.items():
        b, l = cam_shape(0.9, y - 0.25, 0, 1.0)
        ax.add_patch(MPoly(b, fc=v["color"], ec="k", lw=0.5)); ax.add_patch(MPoly(l, fc="white", ec=v["color"]))
        ax.text(1.6, y - 0.25, v["desc"], fontsize=7.5, va="center"); y -= 1.1
    ax.add_patch(Rectangle((0.6, y - 0.5), 0.6, 0.4, fc="#0050c8")); ax.text(1.6, y - 0.3, "ตู้ Rack / NVR / PoE Switch", fontsize=7.5, va="center"); y -= 1.1
    ax.add_patch(Rectangle((0.5, y - 0.55), 0.8, 0.5, fc="#3a3a3a")); ax.text(1.6, y - 0.3, "ผนัง (ภายนอก 0.20 / ภายใน 0.12 ม.)", fontsize=7.5, va="center"); y -= 1.1
    ax.add_patch(Rectangle((0.5, y - 0.55), 0.8, 0.5, fc="#e6e1d6", ec="#7a7062")); ax.text(1.6, y - 0.3, "ชั้นวางสินค้า / โต๊ะ", fontsize=7.5, va="center"); y -= 1.1
    ax.plot([0.5, 1.3], [y - 0.3, y - 0.3], color="#666", ls=(0, (5, 3))); ax.text(1.6, y - 0.3, "เส้นประตามแบบร่าง (ขอบหลังคา/คาน/ช่องเปิด)", fontsize=7.5, va="center"); y -= 1.1
    if mode == "fov":
        ax.add_patch(MPoly([(0.5, y - 0.6), (1.3, y - 0.2), (1.3, y - 0.6)], fc="#1f77b4", alpha=0.25)); ax.text(1.6, y - 0.4, "มุมมองกล้อง (FOV) – ตัดตามแนวผนัง", fontsize=7.5, va="center"); y -= 1.1
        ax.add_patch(Rectangle((0.5, y - 0.6), 0.8, 0.45, fc="none", ec="#d00000", hatch="xxx")); ax.text(1.6, y - 0.4, "จุดอับสายตา (Blind spot) ที่เหลือ", fontsize=7.5, va="center"); y -= 1.1
    if mode == "cable":
        ax.plot([0.5, 1.3], [y - 0.3, y - 0.3], color="#c000c0", lw=5, alpha=0.3); ax.text(1.6, y - 0.3, "แนวท่อหลัก/รางเดินสาย (Trunk) ในฝ้า", fontsize=7.5, va="center"); y -= 1.1
        ax.plot([0.5, 1.3], [y - 0.3, y - 0.3], color="#d00000", lw=0.8); ax.text(1.6, y - 0.3, "สาย LAN CAT6 ไปกล้อง (1 เส้น/กล้อง)", fontsize=7.5, va="center"); y -= 1.1
        ax.plot([0.5, 1.3], [y - 0.3, y - 0.3], color="#0050c8", lw=1.4, ls="--"); ax.text(1.6, y - 0.3, "สาย Uplink CAT6 ระหว่างตู้", fontsize=7.5, va="center"); y -= 1.1
        ax.add_patch(plt.Circle((0.9, y - 0.3), 0.18, fc="#ffd400", ec="k")); ax.text(1.6, y - 0.3, "จุดท่อ Riser ขึ้น-ลงชั้น", fontsize=7.5, va="center"); y -= 1.1
    y -= 0.6
    ax.text(0.3, y, "หมายเหตุ", fontsize=10, fontweight="bold", va="top"); y -= 1.4
    notes = [
        f"ขนาดทุกค่าเป็นขนาดโดยประมาณ ({APX}) ย่อขยายจากสัดส่วนแบบร่าง โดยกำหนด FL1 กว้าง {APX}16.0 ม. – ต้องวัดยืนยันหน้างานก่อนติดตั้ง",
        "ตำแหน่งและทิศกล้องเป็นไปตามแบบร่างต้นฉบับ (CAM-30 = กล้องในห้อง 5 ที่เลขในแบบร่างอ่านไม่ชัด)",
        "ความสูงติดตั้ง: ภายใน ≈2.8 ม. (ใต้ฝ้า) / ภายนอก ≈3.0 ม.",
        "ทิศ 0° = ขวาของแบบ, 90° = ด้านหลังอาคาร (ทวนเข็ม)",
    ] + list(extra_notes)
    import textwrap
    for i, n in enumerate(notes, 1):
        lines = textwrap.wrap(n, 52)
        ax.text(0.3, y, f"{i}.", fontsize=7.2, va="top")
        ax.text(0.9, y, "\n".join(lines), fontsize=7.2, va="top", linespacing=1.35)
        y -= 0.95 * len(lines) + 0.35
    return ax


# =====================================================================
# 3D
# =====================================================================

def extrude(geom, z0, z1):
    faces = []
    for g in geoms(geom):
        rings = [list(g.exterior.coords)] + [list(r.coords) for r in g.interiors]
        for ring in rings:
            for (x1, y1), (x2, y2) in zip(ring[:-1], ring[1:]):
                faces.append([(x1, y1, z0), (x2, y2, z0), (x2, y2, z1), (x1, y1, z1)])
        faces.append([(x, y, z1) for x, y in g.exterior.coords])
    return faces


def draw3d(ax, plan, title, wall_h=1.2):
    ax.computed_zorder = False
    fl = [[(x, y, 0) for x, y in g.exterior.coords] for g in geoms(plan.footprint)]
    ax.add_collection3d(Poly3DCollection(fl, fc="#efe9dc", ec="#bbb", lw=0.3, zorder=1))
    if plan.parking:
        x0, y0, x1, y1 = plan.parking
        ax.add_collection3d(Poly3DCollection([[(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)]], fc="#d9d9d9", ec="#999", lw=0.3, zorder=1))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, 0.05, "ลานจอดรถ", fontsize=7, ha="center", zorder=8)
    for cam in CAMS:
        if cam["plan"] != plan.key:
            continue
        for g in geoms(cam["fov"]):
            ax.add_collection3d(Poly3DCollection([[(x, y, 0.02) for x, y in g.exterior.coords]],
                                                 fc=cam["fcol"], alpha=0.2, ec="none", zorder=2))
    segs = []
    for a, b, c, d, t in plan.walls:
        s_ = LineString([(a, b), (c, d)]).buffer(t / 2, cap_style="square", join_style="mitre")
        for o in plan.openings:
            s_ = s_.difference(box(*o))
        segs.append(s_)
    ax.add_collection3d(Poly3DCollection(extrude(MultiPolygon([p for s_ in segs for p in geoms(s_)]), 0, wall_h),
                                         fc="#b9b9b9", ec="#666", lw=0.25, alpha=0.95, zorder=3))
    for x, y, w, h, t in plan.furn:
        ax.add_collection3d(Poly3DCollection(extrude(box(x, y, x + w, y + h), 0, 1.0), fc="#c8b48a", ec="#8a7650", lw=0.3, zorder=4))
    for ek, e in EQUIP.items():
        if e["plan"] == plan.key:
            ax.add_collection3d(Poly3DCollection(extrude(box(e["x"] - e["w"] / 2, e["y"] - e["d"] / 2, e["x"] + e["w"] / 2, e["y"] + e["d"] / 2), 0.0, 1.0), fc="#0050c8", ec="k", lw=0.3, zorder=4))
            ax.text(e["x"], e["y"], 1.3, ek, fontsize=6.5, color="#0050c8", ha="center", zorder=8)
    for cam in CAMS:
        if cam["plan"] != plan.key:
            continue
        col = TYPES[cam["type"]]["color"]
        z = cam["h"]
        ext = list(cam["fov"].exterior.coords) if cam["fov"].geom_type == "Polygon" else []
        if len(ext) > 3:
            for px, py in (ext[1], ext[len(ext) // 2], ext[-2]):
                ax.plot([cam["x"], px], [cam["y"], py], [z, 0.02], color=col, lw=0.5, alpha=0.7, zorder=5)
        ax.plot([cam["x"], cam["x"]], [cam["y"], cam["y"]], [0, z], color="#555", lw=0.4, ls=":", zorder=5)
        ax.scatter([cam["x"]], [cam["y"]], [z], color=col, s=26, edgecolor="k", linewidth=0.4, depthshade=False, zorder=6)
        ax.text(cam["x"], cam["y"], z + 0.3, cam["id"].replace("CAM-", ""), fontsize=7, color=col,
                fontweight="bold", ha="center", zorder=7)
    minx, miny, maxx, maxy = plan.footprint.bounds
    if plan.parking:
        maxx = max(maxx, plan.parking[2])
        miny = -2.0
    ax.set_xlim(minx, maxx); ax.set_ylim(miny, maxy); ax.set_zlim(0, 4)
    ax.set_box_aspect((maxx - minx, maxy - miny, 4))
    ax.view_init(elev=38, azim=-62)
    ax.set_axis_off()
    ax.set_title(title, fontsize=12, fontweight="bold")


# =====================================================================
# BUILD PDF / PNG
# =====================================================================
TOTAL = 8
pdf_path = os.path.join(OUT, f"CCTV_{PROJECT}_ชุดแบบติดตั้ง.pdf")
png_dir = os.path.join(OUT, "PNG")
os.makedirs(png_dir, exist_ok=True)
PLAN_RECT = [0.015, 0.095, 0.725, 0.88]
LEG_RECT = [0.75, 0.095, 0.235, 0.88]
pages = []


def finish(fig, name):
    fig.savefig(os.path.join(png_dir, name + ".png"), dpi=160)
    pages.append(fig)


def plan_limits(ax, plan, pad=2.2):
    minx, miny, maxx, maxy = plan.footprint.bounds
    if plan.parking:
        maxx = max(maxx, plan.parking[2] + 1.2)
    ax.set_xlim(minx - pad, maxx + pad * 0.6)
    ax.set_ylim(miny - pad, maxy + pad)


def details_axes(fig, rect_list, mode):
    for plan, rect in zip((ST1, ST2, CA, CB), rect_list):
        ax = fig.add_axes(rect)
        draw_plan(ax, plan, mode, fs=6.5)
        plan_limits(ax, plan, pad=1.2)
        ax.set_title(f"แบบขยาย: {plan.title}", fontsize=9, fontweight="bold")


# S-01 FL1 position
fig = frame(1, "S-01 แปลนชั้น 1 – ตำแหน่งติดตั้งกล้อง CCTV", TOTAL)
ax = fig.add_axes(PLAN_RECT); draw_plan(ax, FL1, "pos"); plan_limits(ax, FL1)
ax.set_title("แปลนชั้น 1 (FL1-IN) – ตำแหน่งกล้องและทิศทางการหันกล้อง (Viewing Direction)", fontsize=12, fontweight="bold")
legend_axes(fig, LEG_RECT, "pos", ["ไม่พบตำแหน่งเคาน์เตอร์แคชเชียร์ในแบบร่าง – ถ้ามี กรุณาระบุ เพื่อเพิ่ม/ปรับกล้องจับเคาน์เตอร์",
                                   "ห้อง 1–4 ไม่มีประตูในแบบร่าง – ระบุตำแหน่งประตูจริงหน้างาน"])
finish(fig, "S-01_FL1_Camera_Position")

# S-02 FL2 + details position
fig = frame(2, "S-02 แปลนชั้น 2 + แบบขยาย – ตำแหน่งกล้อง", TOTAL)
ax = fig.add_axes([0.015, 0.43, 0.46, 0.51]); draw_plan(ax, FL2, "pos"); plan_limits(ax, FL2, 1.8)
ax.set_title("แปลนชั้น 2 (FL2-IN) – ตำแหน่งกล้อง", fontsize=12, fontweight="bold")
details_axes(fig, [[0.475, 0.55, 0.13, 0.42], [0.61, 0.55, 0.13, 0.42], [0.02, 0.25, 0.36, 0.17], [0.38, 0.25, 0.36, 0.17]], "pos")
legend_axes(fig, LEG_RECT, "pos", ["ตำแหน่งโถงบันไดและทางเดิน A/B เทียบกับแปลนหลักไม่ระบุในแบบร่าง – แสดงเป็นแบบขยายแยก ต้องยืนยันหน้างาน",
                                   "ทางเดิน B ไม่ได้ระบุชั้นในแบบร่าง – คิดเป็น FL2"])
finish(fig, "S-02_FL2_Details_Camera_Position")

# S-03 FOV FL1
fig = frame(3, "S-03 แปลนชั้น 1 – มุมมองและพื้นที่ครอบคลุม (FOV)", TOTAL)
ax = fig.add_axes(PLAN_RECT); draw_plan(ax, FL1, "fov"); plan_limits(ax, FL1)
ax.set_title(f"แปลนชั้น 1 – Field of View  |  ครอบคลุมพื้นที่ภายใน {APX}{COVER['FL1']['pct']:.0f}%", fontsize=12, fontweight="bold")
legend_axes(fig, LEG_RECT, "fov", ["FOV คำนวณจากมุมเลนส์ (HFOV) และระยะใช้งาน ตัดตามแนวผนัง (ยังไม่คิดการบังของชั้นวางสูง)",
                                   "ชั้นวางสูง >1.8 ม. อาจบังมุมมองบางส่วน – ปรับมุมกล้องหน้างาน"])
finish(fig, "S-03_FL1_FOV")

# S-04 FOV FL2 + details
fig = frame(4, "S-04 แปลนชั้น 2 + แบบขยาย – มุมมอง (FOV)", TOTAL)
ax = fig.add_axes([0.015, 0.43, 0.46, 0.51]); draw_plan(ax, FL2, "fov"); plan_limits(ax, FL2, 1.8)
ax.set_title(f"แปลนชั้น 2 – Field of View  |  ครอบคลุม {APX}{COVER['FL2']['pct']:.0f}%", fontsize=12, fontweight="bold")
details_axes(fig, [[0.475, 0.55, 0.13, 0.42], [0.61, 0.55, 0.13, 0.42], [0.02, 0.25, 0.36, 0.17], [0.38, 0.25, 0.36, 0.17]], "fov")
legend_axes(fig, LEG_RECT, "fov", ["FL2 โซน C (พื้นที่หลัก) ยังไม่มีกล้องตามแบบร่าง → จุดอับขนาดใหญ่ เสนอเพิ่ม (Option) Dome 2.8mm 2 ตัว ที่มุมโซน C หากต้องการเฝ้าระวังพื้นที่นี้"])
finish(fig, "S-04_FL2_Details_FOV")

# S-05 Cabling FL1
fig = frame(5, "S-05 แปลนชั้น 1 – แนวเดินสาย LAN CAT6 / ตำแหน่ง NVR", TOTAL)
ax = fig.add_axes(PLAN_RECT); draw_plan(ax, FL1, "cable", show_dims=False); plan_limits(ax, FL1)
ax.set_title("แปลนชั้น 1 – Layout การเดินสายระบบ CCTV (ระยะสายต่อกล้องระบุใต้ชื่อกล้อง)", fontsize=12, fontweight="bold")
legend_axes(fig, LEG_RECT, "cable", [
    f"ระยะสาย = ระยะตามแนวท่อ + {DROP_ALLOW:.0f} ม. (ขึ้น-ลงตู้/ลงหัวกล้อง/Service loop) + เผื่อ 10%",
    "เดินสายในฝ้า ร้อยท่อ EMT/PVC 1/2\" ต่อกล้อง, แนว Trunk ใช้รางเดินสาย/ท่อ 1-1/4\"",
    "กล้องภายนอก (CAM-01,02,03,04,07) ใช้สาย CAT6 Outdoor + กล่องกันน้ำ IP66 + ท่อ HDPE/EMT",
    "สาย CAT6 ต่อเส้นต้องไม่เกิน 90 ม. (TIA-568) – ทุกเส้นในแบบนี้ผ่าน",
    "ตู้ RACK-1 ติดผนังห้อง 4 สูง ≈1.5 ม. มีปลั๊กแยกวงจร + สายดิน"])
finish(fig, "S-05_FL1_Cabling")

# S-06 Cabling FL2 + riser
fig = frame(6, "S-06 แปลนชั้น 2 – แนวเดินสาย + ไดอะแกรมระบบ", TOTAL)
ax = fig.add_axes([0.015, 0.40, 0.46, 0.54]); draw_plan(ax, FL2, "cable", show_dims=False); plan_limits(ax, FL2, 1.8)
ax.set_title("แปลนชั้น 2 – Layout การเดินสาย", fontsize=12, fontweight="bold")
# system riser diagram
ax = fig.add_axes([0.48, 0.10, 0.26, 0.85]); ax.set_xlim(0, 10); ax.set_ylim(0, 40); ax.axis("off")
ax.set_title("ไดอะแกรมระบบ (System Riser Diagram)", fontsize=11, fontweight="bold")


def blk(x, y, w, h, t, c="#0050c8"):
    ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=c, lw=1.0))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.5)


ax.add_patch(Rectangle((0.3, 22.5), 9.4, 15.5, fill=False, ls="--", ec="#888")); ax.text(0.5, 37.6, "ชั้น 2 – RACK-2 (6U)", fontsize=8, va="top", color="#555")
ax.add_patch(Rectangle((0.3, 1.0), 9.4, 20.5, fill=False, ls="--", ec="#888")); ax.text(0.5, 21.1, "ชั้น 1 – RACK-1 (12U) ห้อง 4", fontsize=8, va="top", color="#555")
blk(2.5, 31.5, 5, 2.2, f"PoE Switch 16 Port Gigabit\n(ใช้ {ports['SW2']} พอร์ต, งบ PoE ≥150W)")
fl2c = [c["id"].replace("CAM-", "") for c in CAMS if c["sw"] == "SW2"]
ax.text(5, 36.2, "กล้อง: " + ", ".join(fl2c), ha="center", fontsize=7.5, color="#d00000")
ax.annotate("", xy=(5, 33.7), xytext=(5, 35.8), arrowprops=dict(arrowstyle="<-", color="#d00000"))
ax.text(5.2, 34.6, f"CAT6 × {ports['SW2']} เส้น", fontsize=7, color="#d00000")
blk(2.5, 25.0, 5, 1.8, "Patch Panel CAT6 24P")
ax.plot([5, 5], [26.8, 31.5], color="k", lw=0.8)
ax.plot([7.5, 8.7, 8.7, 7.5], [15.3, 15.3, 25.9, 25.9], color="#0050c8", lw=1.6, ls="--")
ax.text(9.1, 20.6, f"Uplink CAT6 × 2 เส้น (1 สำรอง) ≈{UPLINK_LEN} ม./เส้น ผ่านท่อ Riser", fontsize=7,
        color="#0050c8", rotation=90, ha="center", va="center")
blk(2.5, 14.4, 5, 1.8, "Patch Panel CAT6 24P")
blk(2.5, 11.0, 5, 2.2, f"PoE Switch 24 Port Gigabit\n(ใช้ {ports['SW1']} พอร์ต, งบ PoE ≥250W)")
blk(2.5, 7.4, 5, 2.4, "NVR 32CH 4K H.265+\nHDD 2×10TB (≈30 วัน)")
blk(2.5, 3.8, 5, 2.2, "UPS 1.5kVA Line-Interactive\n+ PDU / ปลั๊กราง")
blk(7.8, 7.6, 1.8, 2.0, "จอ\nMonitor\n24\"")
ax.plot([7.5, 7.8], [8.6, 8.6], color="k")
ax.text(8.7, 6.4, "HDMI", fontsize=6.5, ha="center")
ax.plot([5, 5], [13.2, 14.4], color="k", lw=0.8); ax.plot([5, 5], [9.8, 11.0], color="k", lw=0.8); ax.plot([5, 5], [6.0, 7.4], color="k", lw=0.8)
fl1c = [c["id"].replace("CAM-", "") for c in CAMS if c["sw"] == "SW1"]
ax.text(5, 19.6, "กล้อง: " + ", ".join(fl1c[:10]) + "\n" + ", ".join(fl1c[10:]), ha="center", fontsize=7.5, color="#d00000")
ax.annotate("", xy=(5, 16.2), xytext=(5, 18.6), arrowprops=dict(arrowstyle="<-", color="#d00000"))
ax.text(1.0, 17.4, f"CAT6 × {ports['SW1']} เส้น", fontsize=7, color="#d00000")
ax.text(5, 1.6, "Router/Internet ของลูกค้า → LAN NVR (ดูผ่านมือถือ)", ha="center", fontsize=7, color="#555")
legend_axes(fig, LEG_RECT, "cable", [
    f"RACK-2 ติดผนังชั้น 2 ใกล้ท่อ Riser (ตำแหน่งสมมติ – ยืนยันหน้างาน). สมมติความสูงชั้น {FLOOR_H} ม.",
    f"กล้องในแบบขยาย (CAM-24..29) ระยะสายคิดประมาณ {EST_DETAIL_LEN} ม./เส้น (*) จนกว่าจะทราบตำแหน่งจริง",
    "CAM-24 ต่อเข้า RACK-1, CAM-25..29 ต่อเข้า RACK-2"])
ax2 = fig.add_axes([0.02, 0.10, 0.45, 0.28]); ax2.axis("off")
ax2.set_title("ระยะสายต่อกล้อง (ม.)", fontsize=9, fontweight="bold", loc="left")
rows = [[c["id"], c["sw"] + f"-P{c['port']:02d}", f"{c['len']}{'*' if c['est'] else ''}"] for c in CAMS]
half = (len(rows) + 2) // 3
tbl_rows = []
for i in range(half):
    r = []
    for k in range(3):
        j = i + k * half
        r += rows[j] if j < len(rows) else ["", "", ""]
    tbl_rows.append(r)
t = ax2.table(cellText=tbl_rows, colLabels=["กล้อง", "Port", "ม."] * 3, loc="upper left", cellLoc="center")
t.auto_set_font_size(False); t.set_fontsize(7); t.scale(1, 1.05)
finish(fig, "S-06_FL2_Cabling_Riser")

# S-07 3D
fig = frame(7, "S-07 ภาพ 3D ประกอบตำแหน่งติดตั้ง", TOTAL)
ax = fig.add_axes([0.0, 0.30, 0.62, 0.64], projection="3d"); draw3d(ax, FL1, "3D ชั้น 1 (FL1) – ตำแหน่งกล้อง + พื้นที่ครอบคลุม")
ax = fig.add_axes([0.55, 0.38, 0.45, 0.56], projection="3d"); draw3d(ax, FL2, "3D ชั้น 2 (FL2)")
for i, plan in enumerate((ST1, ST2, CA, CB)):
    ax = fig.add_axes([0.01 + i * 0.245, 0.09, 0.24, 0.25], projection="3d"); draw3d(ax, plan, plan.title)
fig.text(0.62, 0.36, "ภาพ 3D เพื่อประกอบความเข้าใจ: ผนังแสดงแบบตัด (Cutaway) สูง 1.2 ม. เพื่อให้มองเห็นภายใน,\nกล้องแสดงที่ระดับติดตั้ง, พื้นที่สีบนพื้น = พื้นที่ครอบคลุมของกล้องแต่ละตัว",
         fontsize=8, color="#444")
finish(fig, "S-07_3D_Views")

# S-08 schedule + BOM
fig = frame(8, "S-08 ตารางกล้อง (Camera Schedule) + รายการอุปกรณ์ (BOM)", TOTAL)
ax = fig.add_axes([0.015, 0.40, 0.97, 0.57]); ax.axis("off")
ax.set_title("ตารางกล้อง CCTV (Camera Schedule)", fontsize=12, fontweight="bold", loc="left")
hdr = ["กล้อง", "ตำแหน่ง/แปลน", "ประเภท", "ความละเอียด/เลนส์", "HFOV", "ทิศ (°)", "สูงติดตั้ง", "พื้นที่เฝ้าระวัง", "Switch-Port", "ระยะสาย (ม.)", "สาย"]
rows = []
for c in CAMS:
    rows.append([c["id"], PLANS[c["plan"]].title, c["type"], c["lens"], f"{c['hfov']}°", f"{c['dir'] % 360:.0f}",
                 f"{APX}{c['h']:.1f} ม.", c["area"], f"{c['sw']}-P{c['port']:02d}",
                 f"{c['len']}{' (ประมาณ)' if c['est'] else ''}", "CAT6 Outdoor" if c["outdoor"] else "CAT6"])
t = ax.table(cellText=rows, colLabels=hdr, loc="upper left", cellLoc="left",
             colWidths=[0.05, 0.11, 0.05, 0.09, 0.04, 0.04, 0.05, 0.27, 0.06, 0.07, 0.07])
t.auto_set_font_size(False); t.set_fontsize(6.8); t.scale(1, 1.08)
for (r, cc), cell in t.get_celld().items():
    if r == 0:
        cell.set_facecolor("#dde6f5"); cell.set_text_props(fontweight="bold")
# BOM
n_type = {k: sum(1 for c in CAMS if c["type"] == k) for k in TYPES}
in_len = sum(c["len"] for c in CAMS if not c["outdoor"]) + 2 * UPLINK_LEN
out_len = sum(c["len"] for c in CAMS if c["outdoor"])
trunk_len = sum(x1 - x0 for _, (_, _, x0, x1) in TRUNK.items())
branch_len = sum(path_len(c["route"][2:]) for c in CAMS if c["route"])
BOM = [
    ["1", "กล้อง Dome 4MP IR 2.8mm/4mm (ภายใน) PoE", f"{n_type['Dome']}", "ตัว", "ตามตาราง Lens ในตารางกล้อง"],
    ["2", "กล้อง Turret 4MP IR 2.8mm/4mm PoE", f"{n_type['Turret']}", "ตัว", "ใต้ชายคา/ทางเดิน"],
    ["3", "กล้อง Bullet 4MP IR IP67 PoE (VF 2.8–12mm ×1, 4mm ×1)", f"{n_type['Bullet']}", "ตัว", "ภายนอก / ลานจอด (ทางเลือก: PTZ ที่ CAM-01)"],
    ["4", "NVR 32CH 4K H.265+ 4 SATA", "1", "เครื่อง", "รองรับขยายได้อีก 2 ช่อง"],
    ["5", "HDD Surveillance 10TB", "2", "ลูก", "≈30 วัน @4MP H.265+ ~2Mbps/กล้อง 24ชม."],
    ["6", "PoE Switch 24P Gigabit (PoE budget ≥250W) + 2 Uplink", "1", "ตัว", f"RACK-1 (ใช้ {ports['SW1']} พอร์ต)"],
    ["7", "PoE Switch 16P Gigabit (PoE budget ≥150W) + Uplink", "1", "ตัว", f"RACK-2 (ใช้ {ports['SW2']} พอร์ต)"],
    ["8", "ตู้ Rack ติดผนัง 12U / 6U", "1 / 1", "ตู้", "RACK-1 ห้อง 4 / RACK-2 ชั้น 2"],
    ["9", "Patch Panel CAT6 24P + สาย Patch cord", "2", "ชุด", ""],
    ["10", "สาย LAN CAT6 UTP (ภายใน) 305 ม./กล่อง", f"{math.ceil(in_len / 305)}", "กล่อง", f"รวม ≈{in_len} ม. (รวม Uplink 2 เส้น)"],
    ["11", "สาย LAN CAT6 Outdoor (PE) 305 ม./กล่อง", f"{math.ceil(out_len / 305)}", "กล่อง", f"รวม ≈{out_len} ม."],
    ["12", "ท่อ/รางเดินสาย Trunk 1-1/4\"", f"{APX}{math.ceil(trunk_len * 1.1)}", "ม.", "แนวท่อหลักในฝ้า"],
    ["13", "ท่อ EMT/PVC 1/2\" ย่อยไปกล้อง + ข้อต่อ/กล่องพัก", f"{APX}{math.ceil(branch_len * 1.1)}", "ม.", "ไม่รวมกล้องแบบขยาย (CAM-24..29)"],
    ["14", "กล่องพักสายกันน้ำ IP66 (กล้องภายนอก)", "5", "ใบ", "CAM-01,02,03,04,07"],
    ["15", "UPS 1.5kVA + PDU / จอ Monitor 24\" + สาย HDMI", "1", "ชุด", "RACK-1"],
]
ax = fig.add_axes([0.015, 0.10, 0.62, 0.28]); ax.axis("off")
ax.set_title("รายการอุปกรณ์โดยประมาณ (BOM)", fontsize=12, fontweight="bold", loc="left")
t = ax.table(cellText=BOM, colLabels=["#", "รายการ", "จำนวน", "หน่วย", "หมายเหตุ"], loc="upper left", cellLoc="left",
             colWidths=[0.04, 0.46, 0.08, 0.07, 0.35])
t.auto_set_font_size(False); t.set_fontsize(7); t.scale(1, 1.1)
for (r, cc), cell in t.get_celld().items():
    if r == 0:
        cell.set_facecolor("#dde6f5"); cell.set_text_props(fontweight="bold")
ax = fig.add_axes([0.65, 0.10, 0.335, 0.28]); ax.axis("off")
ax.set_title("ข้อมูลที่ต้องยืนยันหน้างาน", fontsize=11, fontweight="bold", loc="left")
todo = [
    f"1. วัดขนาดจริงทุกห้อง (แบบนี้ใช้ FL1 กว้าง {APX}16.0 ม. เป็นฐาน)",
    "2. ตำแหน่งเคาน์เตอร์แคชเชียร์ (ไม่มีในแบบร่าง)",
    "3. เลขกล้องในห้อง 5 (ใช้ CAM-30 ชั่วคราว)",
    "4. ตำแหน่งโถงบันได + ทางเดิน A/B ในอาคาร และชั้นของทางเดิน B",
    "5. ความสูงฝ้า/ชั้น และแนวท่อ Riser ระหว่างชั้น",
    "6. ประตูห้อง 1–4 และการใช้งานแต่ละห้อง",
    "7. FL2 โซน C ไม่มีกล้อง – ต้องการเพิ่มหรือไม่",
    f"สรุป: กล้องรวม {len(CAMS)} ตัว | Dome {n_type['Dome']} / Turret {n_type['Turret']} / Bullet {n_type['Bullet']}",
    f"ความครอบคลุม FL1 ≈{COVER['FL1']['pct']:.0f}%  |  FL2 ≈{COVER['FL2']['pct']:.0f}%",
]
ax.text(0.0, 0.92, "\n".join(todo), fontsize=8.2, va="top", linespacing=1.6, transform=ax.transAxes)
finish(fig, "S-08_Schedule_BOM")

with PdfPages(pdf_path) as pdf:
    for f in pages:
        pdf.savefig(f)
for f in pages:
    plt.close(f)

# CSV schedule
with open(os.path.join(OUT, f"CCTV_{PROJECT}_ตารางกล้อง.csv"), "w", newline="", encoding="utf-8-sig") as fcsv:
    w = csv.writer(fcsv)
    w.writerow(["Camera", "Plan", "X(m)", "Y(m)", "Direction(deg)", "Type", "Lens", "HFOV", "Mount H (m)", "Area",
                "Switch", "Port", "Cable (m)", "Cable estimated", "Cable type"])
    for c in CAMS:
        w.writerow([c["id"], PLANS[c["plan"]].title, c["x"], c["y"], c["dir"] % 360, c["type"], c["lens"], c["hfov"],
                    c["h"], c["area"], c["sw"], c["port"], c["len"], "Y" if c["est"] else "", "CAT6 Outdoor" if c["outdoor"] else "CAT6"])
    w.writerow([])
    w.writerow(["BOM"])
    for r in BOM:
        w.writerow(r)

# =====================================================================
# DXF (AutoCAD 2D)
# =====================================================================
doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.M
doc.header["$MEASUREMENT"] = 1
doc.styles.new("THAI", dxfattribs={"font": "tahoma.ttf"})
LAYERS = {
    "A-WALL": 7, "A-WALL-HATCH": 8, "A-DOOR": 30, "A-FURN": 41, "A-STAIR": 8, "A-DASH": 8, "A-ROOM-TEXT": 7,
    "A-DIM": 4, "A-PARKING": 9, "CCTV-CAM": 5, "CCTV-CAM-TEXT": 5, "CCTV-FOV": 3, "CCTV-BLIND": 1,
    "CCTV-CABLE": 1, "CCTV-CONDUIT": 6, "CCTV-EQUIP": 150, "CCTV-RISER": 2, "TITLE": 7,
}
for n, c in LAYERS.items():
    lay = doc.layers.add(n, color=c)
    if n == "A-DASH":
        lay.dxf.linetype = "DASHED"
msp = doc.modelspace()
ACI = {"Dome": 5, "Turret": 3, "Bullet": 30}

blk = doc.blocks.new("CCTV_CAM")
blk.add_lwpolyline([(-0.3, -0.14), (0.05, -0.14), (0.05, 0.14), (-0.3, 0.14)], close=True, dxfattribs={"color": 0})
blk.add_lwpolyline([(0.05, 0), (0.32, 0.18), (0.32, -0.18)], close=True, dxfattribs={"color": 0})
h = blk.add_hatch(color=0); h.paths.add_polyline_path([(-0.3, -0.14), (0.05, -0.14), (0.05, 0.14), (-0.3, 0.14)], is_closed=True)


def T(x, y, s, txt, layer, color=None, align=MTextEntityAlignment.MIDDLE_CENTER, width=None):
    attrs = {"style": "THAI", "char_height": s, "layer": layer}
    if color is not None:
        attrs["color"] = color
    m = msp.add_mtext(txt.replace("\n", "\\P"), dxfattribs=attrs)
    if width:
        m.dxf.width = width
    m.set_location((x, y), attachment_point=align)
    return m


def hatch_geom(g, ox, oy, layer, color, solid=True, transp=None, pattern="ANSI31", scale=0.3):
    for p in geoms(g):
        hh = msp.add_hatch(color=color, dxfattribs={"layer": layer})
        if not solid:
            hh.set_pattern_fill(pattern, scale=scale, color=color)
        hh.paths.add_polyline_path([(x + ox, y + oy) for x, y in p.exterior.coords][:-1], is_closed=True, flags=1)
        for r in p.interiors:
            hh.paths.add_polyline_path([(x + ox, y + oy) for x, y in r.coords][:-1], is_closed=True, flags=0)
        if transp is not None:
            hh.transparency = transp


def outline(g, ox, oy, layer, color=None):
    attrs = {"layer": layer}
    if color is not None:
        attrs["color"] = color
    for p in geoms(g):
        for ring in [p.exterior] + list(p.interiors):
            msp.add_lwpolyline([(x + ox, y + oy) for x, y in ring.coords], close=True, dxfattribs=attrs)


for key, plan in PLANS.items():
    ox, oy = plan.offset
    minx, miny, maxx, maxy = plan.footprint.bounds
    T(ox + (minx + maxx) / 2, oy + maxy + (2.4 if key in ("FL1", "FL2") else 0.9), 0.45 if key in ("FL1", "FL2") else 0.3,
      plan.title + " (ขนาดโดยประมาณ)", "TITLE")
    outline(plan.wall_geom, ox, oy, "A-WALL")
    hatch_geom(plan.wall_geom, ox, oy, "A-WALL-HATCH", 8)
    for p1, p2, t in plan.dashed:
        msp.add_line((p1[0] + ox, p1[1] + oy), (p2[0] + ox, p2[1] + oy), dxfattribs={"layer": "A-DASH", "ltscale": 0.02})
    for hx, hy, w, wa, sw in plan.doors:
        end = wa + 90 * sw
        msp.add_line((hx + ox, hy + oy), (hx + ox + w * math.cos(math.radians(end)), hy + oy + w * math.sin(math.radians(end))), dxfattribs={"layer": "A-DOOR"})
        msp.add_arc((hx + ox, hy + oy), w, min(wa, end), max(wa, end), dxfattribs={"layer": "A-DOOR"})
    for x, y, w, hh_, t in plan.furn:
        msp.add_lwpolyline([(x + ox, y + oy), (x + w + ox, y + oy), (x + w + ox, y + hh_ + oy), (x + ox, y + hh_ + oy)], close=True, dxfattribs={"layer": "A-FURN"})
        T(x + w / 2 + ox, y + hh_ / 2 + oy, 0.15, t, "A-FURN")
    for x0, y0, x1, y1, t in plan.stairs:
        msp.add_lwpolyline([(x0 + ox, y0 + oy), (x1 + ox, y0 + oy), (x1 + ox, y1 + oy), (x0 + ox, y1 + oy)], close=True, dxfattribs={"layer": "A-STAIR"})
        yy = y0
        while yy < y1:
            msp.add_line((x0 + ox, yy + oy), (x1 + ox, yy + oy), dxfattribs={"layer": "A-STAIR"})
            yy += 0.25
        T(x1 + 0.3 + ox, (y0 + y1) / 2 + oy, 0.18, f"บันได ({t})", "A-STAIR")
    for name, poly, pos in plan.rooms:
        px, py = pos if pos else (poly.centroid.x, poly.centroid.y)
        T(px + ox, py + oy, 0.2, f"{name}\n{APX}{poly.area:.1f} ตร.ม.", "A-ROOM-TEXT")
    if plan.parking:
        x0, y0, x1, y1 = plan.parking
        pk = box(x0, y0, x1, y1)
        outline(pk, ox, oy, "A-PARKING")
        hatch_geom(pk, ox, oy, "A-PARKING", 9, solid=False, pattern="ANSI31", scale=0.6)
        T((x0 + x1) / 2 + ox, y1 - 1.3 + oy, 0.3, "ลานจอดรถ / ทางรถเข้า", "A-PARKING", width=3.5)
    for x1, y1, x2, y2, off, o in plan.dims:
        if o == "h":
            d = msp.add_linear_dim(base=(x1 + ox, off + oy), p1=(x1 + ox, y1 + oy), p2=(x2 + ox, y2 + oy), angle=0,
                                   text=f"{APX}{abs(x2 - x1):.2f}", dimstyle="EZDXF",
                                   override={"dimtxt": 0.2, "dimasz": 0.15, "dimtxsty": "THAI", "dimexo": 0.1, "dimexe": 0.1, "dimtsz": 0.12},
                                   dxfattribs={"layer": "A-DIM"})
        else:
            d = msp.add_linear_dim(base=(off + ox, y1 + oy), p1=(x1 + ox, y1 + oy), p2=(x2 + ox, y2 + oy), angle=90,
                                   text=f"{APX}{abs(y2 - y1):.2f}", dimstyle="EZDXF",
                                   override={"dimtxt": 0.2, "dimasz": 0.15, "dimtxsty": "THAI", "dimexo": 0.1, "dimexe": 0.1, "dimtsz": 0.12},
                                   dxfattribs={"layer": "A-DIM"})
        d.render()
    # FOV + blind
    for cam in CAMS:
        if cam["plan"] != key:
            continue
        hatch_geom(cam["fov"], ox, oy, "CCTV-FOV", 3, transp=0.8)
        outline(cam["fov"], ox, oy, "CCTV-FOV", 3)
    hatch_geom(COVER[key]["blind"], ox, oy, "CCTV-BLIND", 1, solid=False, pattern="ANSI37", scale=0.4)
    # cabling
    for tname, (pk_, ty, x0, x1) in TRUNK.items():
        if pk_ == key:
            msp.add_lwpolyline([(x0 + ox, ty + oy), (x1 + ox, ty + oy)], dxfattribs={"layer": "CCTV-CONDUIT", "const_width": 0.12})
            T((x0 + x1) / 2 + ox, ty + 0.3 + oy, 0.16, f"แนวท่อหลัก/รางเดินสาย (Trunk) {tname}", "CCTV-CONDUIT")
    for cam in CAMS:
        if cam["plan"] == key and cam["route"]:
            msp.add_lwpolyline([(x + ox, y + oy) for x, y in cam["route"]], dxfattribs={"layer": "CCTV-CABLE"})
    if key in RISER:
        rx, ry = RISER[key]
        msp.add_circle((rx + ox, ry + oy), 0.18, dxfattribs={"layer": "CCTV-RISER"})
        T(rx + ox + 0.3, ry + oy, 0.15, "RISER", "CCTV-RISER", align=MTextEntityAlignment.MIDDLE_LEFT)
        rk = EQUIP["RACK-1" if key == "FL1" else "RACK-2"]
        msp.add_line((rk["x"] + ox, rk["y"] + oy), (rx + ox, ry + oy), dxfattribs={"layer": "CCTV-RISER", "linetype": "DASHED", "ltscale": 0.02})
    for ek, e in EQUIP.items():
        if e["plan"] == key:
            x0, y0 = e["x"] - e["w"] / 2 + ox, e["y"] - e["d"] / 2 + oy
            msp.add_lwpolyline([(x0, y0), (x0 + e["w"], y0), (x0 + e["w"], y0 + e["d"]), (x0, y0 + e["d"])], close=True, dxfattribs={"layer": "CCTV-EQUIP"})
            T(e["x"] + ox, e["y"] - 0.8 + oy, 0.14, e["text"], "CCTV-EQUIP", width=3.0)
    # cameras
    for cam in CAMS:
        if cam["plan"] != key:
            continue
        msp.add_blockref("CCTV_CAM", (cam["x"] + ox, cam["y"] + oy),
                         dxfattribs={"rotation": cam["dir"], "layer": "CCTV-CAM", "color": ACI[cam["type"]]})
        a = math.radians(cam["dir"] + 180)
        lx, ly = LABEL_OFFSET.get(cam["id"], (0.75 * math.cos(a), 0.75 * math.sin(a)))
        T(cam["x"] + ox + lx, cam["y"] + oy + ly, 0.17,
          f"{cam['id']}\n{cam['type'][0]} | {cam['len']}m{'*' if cam['est'] else ''}", "CCTV-CAM-TEXT", color=ACI[cam["type"]])

# schedule & notes in DXF
sx, sy = 44, 13
T(sx, sy + 1.2, 0.35, "ตารางกล้อง CCTV (Camera Schedule)", "TITLE", align=MTextEntityAlignment.TOP_LEFT)
lines = [f"{c['id']}  {c['type']:<6}  {c['lens']:<16}  {c['sw']}-P{c['port']:02d}  {c['len']} ม.{'(ประมาณ)' if c['est'] else ''}  – {c['area']}" for c in CAMS]
T(sx, sy + 0.4, 0.16, "\n".join(lines), "TITLE", align=MTextEntityAlignment.TOP_LEFT, width=16)
notes = ["หมายเหตุ:",
         f"1. ขนาดทั้งหมดเป็นขนาดโดยประมาณ ({APX}) ย่อขยายจากแบบร่าง (FL1 กว้าง {APX}16.0 ม.) ต้องวัดยืนยันหน้างาน",
         "2. ชั้น Layer: A-* = งานสถาปัตย์, CCTV-CAM = กล้อง, CCTV-FOV = มุมมอง, CCTV-BLIND = จุดอับ, CCTV-CABLE/CONDUIT = แนวสาย/ท่อ",
         "3. ทิศ 0° = ขวาของแบบ, หมุนทวนเข็ม | D=Dome, T=Turret, B=Bullet | * = ระยะสายประมาณ",
         "4. ปิด/เปิด Layer เพื่อพิมพ์เป็น: แบบตำแหน่งกล้อง / แบบ FOV / แบบเดินสาย",
         f"5. LOTUS TECHNOLOGY – โครงการ CCTV {PROJECT} – {DATE} – Rev.A (Preliminary)"]
T(sx, -3, 0.2, "\n".join(notes), "TITLE", align=MTextEntityAlignment.TOP_LEFT, width=20)
# frame
msp.add_lwpolyline([(-4, -14), (66, -14), (66, 17), (-4, 17)], close=True, dxfattribs={"layer": "TITLE"})
doc.set_modelspace_vport(height=34, center=(31, 1.5))
dxf_path = os.path.join(OUT, f"CCTV_{PROJECT}_แบบติดตั้ง.dxf")
doc.saveas(dxf_path)

print("PDF:", pdf_path)
print("DXF:", dxf_path)
print("ports", ports, "uplink", UPLINK_LEN)
for k, v in COVER.items():
    print(k, f"cover {v['pct']:.1f}%  blind {v['blind'].area:.1f} m2")
print("cable indoor", in_len, "outdoor", out_len, "max", max(c["len"] for c in CAMS))
