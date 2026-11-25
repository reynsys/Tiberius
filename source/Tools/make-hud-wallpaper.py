#!/usr/bin/env python3
"""TIBERIUS HUD wallpaper (DAMN theme): a large cut-corner triangle frame with a turning core.

Original artwork, drawn from code. The layout is inspired by a GraphicRiver HUD concept
(open apex on top, two chevron corners at the bottom, wing lines with labels), but every
shape is drawn here, so the result can be published with the theme.

Usage:
  make-hud-wallpaper.py <out-dir>              render all 900 frames (30 s @ 30 fps)
  make-hud-wallpaper.py <out-dir> 0 300 600    render only these frames (previews)
  make-hud-wallpaper.py --still <file.png> [t] single still (lock screen / fallback), t = 0..1
Then: ffmpeg -framerate 30 -i <out-dir>/f%04d.png -c:v libvpx-vp9 -b:v 0 -crf 32 -pix_fmt yuv420p out.webm
"""
import math, os, sys
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1920, 1200
SS = 2                                   # supersampling for clean edges
FPS, SECS = 30, 30
N = FPS * SECS
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(HERE, "sources", "fonts", "Oxanium.ttf")

BAR = (214, 247, 243); TEAL = (34, 211, 197); TEAL_L = (90, 232, 220)
DTEAL = (24, 118, 128); DIM = (30, 78, 88); ORG = (242, 140, 56); DORG = (150, 82, 30)

# layout is designed on a 1180 x 814 board centred on the core at (590, 470)
K = 1.45
CX0, CY0 = 590, 470
SCX, SCY = W / 2, H * 0.49


def P(x, y):
    """board coords -> supersampled pixel coords"""
    return ((SCX + (x - CX0) * K) * SS, (SCY + (y - CY0) * K) * SS)


def mirror(pts):
    return [(2 * CX0 - x, y) for x, y in pts]


def font(size, weight="Medium"):
    f = ImageFont.truetype(FONT_FILE, int(size * K * SS))
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def col(c, k=1.0):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# ---------- drawing helpers (all take board coordinates) ----------
def band(g, pts, widths, fill):
    """Thick polyline with sharp mitred joints; widths per vertex (tapering)."""
    if isinstance(widths, (int, float)):
        widths = [widths] * len(pts)
    Q = [P(*p) for p in pts]
    left, right = [], []
    n = len(Q)
    for i in range(n):
        w = widths[i] * K * SS / 2
        if i == 0:
            nx, ny = _norm(Q[0], Q[1])
        elif i == n - 1:
            nx, ny = _norm(Q[-2], Q[-1])
        else:
            a, b = _norm(Q[i - 1], Q[i]), _norm(Q[i], Q[i + 1])
            mx, my = a[0] + b[0], a[1] + b[1]
            ml = math.hypot(mx, my) or 1
            mx, my = mx / ml, my / ml
            d = mx * a[0] + my * a[1] or 1
            nx, ny = mx / d, my / d
        left.append((Q[i][0] + nx * w, Q[i][1] + ny * w))
        right.append((Q[i][0] - nx * w, Q[i][1] - ny * w))
    g.polygon(left + right[::-1], fill=fill)


def _norm(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1
    return (-dy / l, dx / l)


def line(g, pts, w, fill):
    g.line([P(*p) for p in pts], fill=fill, width=max(1, int(w * K * SS)))


def arc_band(g, cx, cy, r, a0, a1, w, fill, step=1.5):
    """Filled ring segment from angle a0 to a1 (degrees, 0 = right, 90 = down)."""
    n = max(2, int(abs(a1 - a0) / step))
    outer, inner = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        outer.append(P(cx + (r + w / 2) * math.cos(a), cy + (r + w / 2) * math.sin(a)))
        inner.append(P(cx + (r - w / 2) * math.cos(a), cy + (r - w / 2) * math.sin(a)))
    g.polygon(outer + inner[::-1], fill=fill)


def ticks(g, cx, cy, r, a0, a1, every, length, w, colour_fn):
    a = a0
    i = 0
    while a <= a1 + 1e-6:
        L, c = colour_fn(i, a)
        if c:
            ra = math.radians(a)
            line(g, [(cx + r * math.cos(ra), cy + r * math.sin(ra)),
                     (cx + (r + L) * math.cos(ra), cy + (r + L) * math.sin(ra))], w, c)
        a += every
        i += 1


def cut_triangle(cx, cy, r, cut, rot=0):
    v = [(cx + r * math.cos(math.radians(-90 + rot + k * 120)),
          cy + r * math.sin(math.radians(-90 + rot + k * 120))) for k in range(3)]
    pts = []
    for k in range(3):
        p, q, o = v[k], v[(k + 1) % 3], v[(k - 1) % 3]
        pts.append((p[0] + (o[0] - p[0]) * cut, p[1] + (o[1] - p[1]) * cut))
        pts.append((p[0] + (q[0] - p[0]) * cut, p[1] + (q[1] - p[1]) * cut))
    return pts


def text(g, x, y, s, size, fill, weight="Medium", anchor="la"):
    g.text(P(x, y), s, font=font(size, weight), fill=fill, anchor=anchor)


def both(fn, pts, *a, **kw):
    fn(pts, *a, **kw)
    fn(mirror(pts), *a, **kw)


# ---------- background ----------
def background():
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx - SCX) / W, (yy - SCY) / H)
    glow = np.clip(1 - d * 1.6, 0, 1) ** 1.6
    base = np.array([7, 11, 15], np.float32)
    tint = np.array([16, 58, 70], np.float32)
    img = base + glow[..., None] * tint
    # side haze like the reference's bright edges, kept dim
    edge = np.clip(np.abs(xx - SCX) / (W / 2) - 0.55, 0, 1) ** 2
    img += edge[..., None] * np.array([6, 30, 40], np.float32)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    g = ImageDraw.Draw(im)
    for x in range(12, W, 40):                       # dot grid
        for y in range(12, H, 40):
            g.point((x, y), fill=(28, 52, 58))
    for _ in range(260):                             # scattered diagonal dashes
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        l = rng.uniform(5, 12)
        g.line([(x, y), (x + l, y - l)], fill=(22, 44, 52), width=1)
    return im


# ---------- geometry of the triangle ----------
R_TRI = 360          # centre -> (virtual) corner of the equilateral triangle
CUT = 70             # how far each corner is cut back along the edges
CS = 0.85            # size of the core relative to its first design


def rot(pt, deg):
    a = math.radians(deg)
    x, y = pt[0] - CX0, pt[1] - CY0
    return (CX0 + x * math.cos(a) - y * math.sin(a), CY0 + x * math.sin(a) + y * math.cos(a))


def corner_piece(deg):
    """One cut corner of the triangle (designed for the top corner, then rotated).
    Heavy chevron with short arms; each arm continues as a narrower stepped bar, three
    blocks and a hairline with an end tick (all aligned on the outer edge). A pointed
    orange chevron sits inside it."""
    A = (CX0, CY0 - R_TRI)
    s3 = math.sqrt(3) / 2
    edges = (((-0.5, s3), (-s3, -0.5)), ((0.5, s3), (s3, -0.5)))   # (direction, outward normal)
    def pt(s, e, off=0.0):
        d, n = e
        return (A[0] + s * d[0] + off * n[0], A[1] + s * d[1] + off * n[1])
    L, R = edges
    parts = [([pt(CUT + 40, L), pt(CUT, L), pt(CUT, R), pt(CUT + 40, R)], 12, BAR)]
    for e in edges:
        parts += [
            ([pt(CUT + 47, e, 3), pt(CUT + 84, e, 3)], 6, BAR),             # stepped, narrower
            ([pt(CUT + 90, e, 4), pt(CUT + 97, e, 4)], 4, BAR),             # blocks
            ([pt(CUT + 101, e, 4), pt(CUT + 108, e, 4)], 4, BAR),
            ([pt(CUT + 112, e, 4), pt(CUT + 119, e, 4)], 4, ORG),
            ([pt(CUT + 125, e, 5), pt(CUT + 165, e, 5)], 1.6, BAR),         # hairline
            ([pt(CUT + 165, e, 5), pt(CUT + 165, e, -4)], 1.6, BAR),        # end tick
        ]
    # pointed orange chevron (thick at the point, sharp ends)
    O = (A[0], A[1] + CUT * s3 + 22)
    tip = lambda e, l: (O[0] + l * e[0][0], O[1] + l * e[0][1])
    parts.append(([tip(L, 58), O, tip(R, 58)], [0.4, 10, 0.4], ORG))
    return [([rot(q, deg) for q in pts], w, c) for pts, w, c in parts]


def slab(g, p0, p1, w, fill, flip=False):
    """Bar of constant width whose ends are cut at 45 degrees (a HUD trapezoid).
    flip=True turns it 180 degrees (long side at the bottom)."""
    if p1[0] < p0[0]:                     # mirrored copies keep the same orientation
        p0, p1 = p1, p0
    u = (p1[0] - p0[0], p1[1] - p0[1]); l = math.hypot(*u); u = (u[0] / l, u[1] / l)
    n = (-u[1], u[0]) if not flip else (u[1], -u[0]); h = w / 2
    pts = [(p0[0] + n[0] * h, p0[1] + n[1] * h), (p1[0] + n[0] * h, p1[1] + n[1] * h),
           (p1[0] - n[0] * h - u[0] * w, p1[1] - n[1] * h - u[1] * w),
           (p0[0] - n[0] * h + u[0] * w, p0[1] - n[1] * h + u[1] * w)]
    g.polygon([P(*q) for q in pts], fill=fill)


def tab(g, cx, cy, r, ang, length, h, fill):
    """Small block sitting on a ring, sides at 45 degrees."""
    a = math.radians(ang)
    ab, at = length / 2 / r, max(0.2, length / 2 - h) / (r + h)
    pts = [(cx + r * math.cos(a - ab), cy + r * math.sin(a - ab)),
           (cx + (r + h) * math.cos(a - at), cy + (r + h) * math.sin(a - at)),
           (cx + (r + h) * math.cos(a + at), cy + (r + h) * math.sin(a + at)),
           (cx + r * math.cos(a + ab), cy + r * math.sin(a + ab))]
    g.polygon([P(*q) for q in pts], fill=fill)


def pointer(g, cx, cy, r, ang, size, fill):
    """Solid triangle whose tip touches radius r; size > 0 sits outside and points inward,
    size < 0 sits inside and points outward."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    tipx, tipy = cx + r * ux, cy + r * uy
    bx, by = tipx + ux * size * 1.2, tipy + uy * size * 1.2
    hw = abs(size) * 0.75
    g.polygon([P(tipx, tipy), P(bx + vx * hw, by + vy * hw), P(bx - vx * hw, by - vy * hw)], fill=fill)


HEAD_Y = 411                         # panel header row (inside the frame)
HEADS = ("NAV // ASTRO", "SHIP // STATUS")


def header_layout(side):
    """x positions for the header: text start, slab (x0, x1), first slash. Right side mirrored."""
    w = font(9, "SemiBold").getlength(HEADS[side]) / (K * SS)
    tx = 84
    sx0, sx1 = tx + w + 7, tx + w + 45
    first = sx1 + 9
    return tx, (sx0, sx1), first


BASE_Y = CY0 + R_TRI / 2           # the triangle's bottom edge
PANEL = [(150, 398), (272, 398), (290, 416), (290, 540), (266, 564), (60, 564), (60, 418), (80, 398)]


# ---------- static frame (drawn once) ----------
def frame_box(g, x0, x1, y0, y1, c):
    """Thin frame with two 45 degree cut corners."""
    band(g, [(x0 + 6, y0), (x1, y0), (x1, y1 - 6), (x1 - 6, y1), (x0, y1), (x0, y0 + 6), (x0 + 6, y0)], 1.4, c)


def static_layer():
    im = Image.new("RGB", (W * SS, H * SS)); g = ImageDraw.Draw(im)
    # faint top header with a 45 degree notch
    band(g, [(-20, 92), (412, 92), (440, 120), (740, 120), (768, 92), (1200, 92)], 4, DIM)
    line(g, [(-20, 72), (1200, 72)], 1, col(DIM, 0.7))
    # faint long cross line with end dots
    line(g, [(205, 372), (975, 372)], 1.2, col(DIM, 1.1))
    for x in (205, 975):
        g.ellipse([*P(x - 3, 369), *P(x + 3, 375)], fill=TEAL)

    # ---- the triangle: the same corner piece at 0, 120 and 240 degrees ----
    for deg in (0, 120, 240):
        for pts, w, c in corner_piece(deg):
            band(g, pts, w, c)
    # middle of the base: notched bar with 45 degree bends
    band(g, [(536, BASE_Y), (550, BASE_Y), (570, BASE_Y + 20), (610, BASE_Y + 20),
             (630, BASE_Y), (644, BASE_Y)], 5, BAR)
    slab(g, (572, BASE_Y + 31), (608, BASE_Y + 31), 5, ORG)

    # upper wings: thin rail, framed loading bar (animated in the dynamic layer), 45 degree rise
    for side in (0, 1):
        m = (lambda q: q) if side == 0 else (lambda q: mirror(q))
        line(g, m([(100, 330), (236, 330)]), 2.5, BAR)
        band(g, m([(418, 330), (444, 304)]), 3, BAR)
        band(g, m([(452, 296), (460, 288)]), 3, BAR)
        # scale line under the bar with 45 degree drops at the ends
        band(g, m([(236, 340), (244, 348), (410, 348), (418, 340)]), 1.4, col(TEAL, 0.8))
        for i in range(17):
            x = 248 + i * 10
            line(g, m([(x, 348), (x, 352 if i % 4 else 356)]), 1, col(TEAL, 0.8))
    for x0 in (244, 770):
        frame_box(g, x0, x0 + 166, 317, 340, col(TEAL, 0.9))

    # lower wings: thin line, 45 degree drop, framed bar
    for side in (0, 1):
        m = (lambda q: q) if side == 0 else (lambda q: mirror(q))
        band(g, m([(30, 690), (196, 690), (246, 740), (292, 740)]), 2.5, BAR)
        band(g, m([(300, 716), (420, 716), (428, 724)]), 1.4, col(TEAL, 0.8))
        band(g, m([(300, 760), (420, 760)]), 1.4, col(TEAL, 0.8))
        slab(g, *m([(300, 764), (330, 764)]), 4, ORG)

    # side panels: 45-degree frame with a header bar; digits go inside (dynamic layer)
    for q in (PANEL, mirror(PANEL)):
        band(g, q + [q[0]], 1.4, col(DTEAL, 1.2))
    for side in (0, 1):
        tx, (a0, a1), _ = header_layout(side)
        seg = [(a0, HEAD_Y), (a1, HEAD_Y)]
        slab(g, *(mirror(seg) if side else seg), 6, DTEAL, flip=True)
        if side == 0:
            text(g, tx, HEAD_Y, HEADS[0], 9, TEAL, "SemiBold", "lm")
        else:
            text(g, 1180 - tx, HEAD_Y, HEADS[1], 9, TEAL, "SemiBold", "rm")
    for q in ([(60, 470), (290, 470)], mirror([(60, 470), (290, 470)])):
        line(g, q, 1, col(DTEAL, 0.9))

    # crosshair marks around the core
    for q in ([(424, 488), (440, 488)], mirror([(424, 488), (440, 488)])):
        band(g, q, 3, TEAL)
    band(g, [(590, CY0 - 168), (590, CY0 - 154)], 2, TEAL)
    band(g, [(590, CY0 + 150), (590, CY0 + 162)], 2, TEAL)

    # labels
    for x, name, code in ((105, "TBR-14", "[NAV-34]"), (1000, "TBR-03", "[COM-47]")):
        g.polygon([P(x, 244), P(x + 76, 244), P(x + 76, 256), P(x + 70, 262), P(x, 262)], fill=BAR)
        text(g, x + 38, 253, name, 11, (10, 20, 24), "Bold", "mm")
        text(g, x + 10, 268, code, 13, TEAL_L)
        for i in range(3):
            g.polygon([P(x + 34 + i * 9, 292), P(x + 41 + i * 9, 292), P(x + 37.5 + i * 9, 298)], fill=ORG)
    for x, name, mag in ((62, "DOCK-C", "18x"), (1072, "DOCK-A", "22x")):
        text(g, x, 700, name, 11, BAR, "SemiBold")
        text(g, x, 716, mag, 11, BAR, "SemiBold")
    return im


# ---------- moving parts ----------
SEGS = [(0, 38), (46, 22), (76, 58), (142, 14), (164, 48), (222, 34), (264, 9), (281, 61)]
rng = np.random.default_rng(7)
PARTS = [(rng.uniform(0, 1180), rng.uniform(80, 800), rng.uniform(8, 30), rng.uniform(0, 6.28),
          rng.random() < 0.3) for _ in range(40)]


def core_layer(t):
    """The ring and centre: solid shapes only, never blurred."""
    im = Image.new("RGB", (W * SS, H * SS)); g = ImageDraw.Draw(im)
    tau = 2 * math.pi
    c = lambda r: r * CS
    # top dial with drifting marker
    mark = -90 + 48 * math.sin(tau * t * 2)
    def top_tick(i, a):
        return (c(16) if i % 5 == 0 else c(9)), (ORG if abs(a - mark) < 4 else (BAR if i % 5 == 0 else TEAL))
    ticks(g, CX0, CY0, c(158), -150, -30, 4, 0, 2, top_tick)
    ra = math.radians(mark)
    pointer(g, CX0, CY0, c(177), mark, 8, ORG)                     # always points at the centre
    # lower fine scale with a moving highlight
    sweep = 20 + 140 * ((t * 3) % 1)
    def low_tick(i, a):
        d = abs(a - sweep)
        return (c(11) if i % 10 == 0 else c(6)), col(TEAL, 0.5 + (0.8 * (1 - d / 18) if d < 18 else 0))
    ticks(g, CX0, CY0, c(146), 22, 158, 2, 0, 1.4, low_tick)
    # heavy segmented ring with 45-degree tabs at each segment start
    rot_ = 360 * t
    for s0, ln in SEGS:
        arc_band(g, CX0, CY0, c(112), s0 + rot_, s0 + ln + rot_, c(22), (18, 82, 98))
        arc_band(g, CX0, CY0, c(124), s0 + rot_, s0 + ln + rot_, 2, (70, 180, 188))
    # bright outer arcs turning the other way, with tabs
    r2 = -720 * t
    for a0, a1, cl in ((-70, -18, TEAL_L), (62, 74, TEAL_L), (150, 158, ORG)):
        arc_band(g, CX0, CY0, c(137), a0 + r2, a1 + r2, c(8), cl)
    pointer(g, CX0, CY0, c(137) + c(5), -44 + r2, 9, ORG)          # triangle pointing at the arc
    # inner ring: four arcs with square-cut gaps and inward 45-degree teeth
    r3 = 1080 * t
    for k in range(4):
        arc_band(g, CX0, CY0, c(84), k * 90 + 6 + r3, k * 90 + 84 + r3, c(9), TEAL_L)
    # solid well
    g.ellipse([*P(CX0 - c(70), CY0 - c(70)), *P(CX0 + c(70), CY0 + c(70))], fill=(6, 18, 24))
    arc_band(g, CX0, CY0, c(66), 0, 359.9, 1.6, DTEAL)
    for k in range(4):                                               # triangles pointing at the inner arcs
        pointer(g, CX0, CY0, c(84) - c(5.5), k * 90 + 45 + r3, -7, TEAL_L)
    # centre emblem: cut-corner triangle (same family as the frame) + DAMN LAB
    tri = cut_triangle(CX0, CY0 - 14, 25, 0.2)
    band(g, tri + [tri[0]], 3.4, ORG)
    g.polygon([P(CX0, CY0 - 22), P(CX0 + 7, CY0 - 10), P(CX0 - 7, CY0 - 10)], fill=ORG)
    text(g, CX0, CY0 + 22, "TIBERIUS", 14, BAR, "SemiBold", "mm")
    text(g, CX0, CY0 + 38, "MK - IV", 8, ORG, "SemiBold", "mm")
    return im


def dynamic_layer(t):
    im = Image.new("RGB", (W * SS, H * SS)); g = ImageDraw.Draw(im)
    tau = 2 * math.pi
    # blinking slashes in the panel headers
    for side in (0, 1):
        for i in range(4):
            on = int(t * 60 + i + side * 2) % 6 < 3
            x = header_layout(side)[2] + i * 9
            pts = [(x, HEAD_Y + 5), (x + 6, HEAD_Y - 5)]
            band(g, mirror(pts) if side else pts, 3, BAR if on else DIM)
    # data rows (top half of the panels)
    r = np.random.default_rng(int(t * 30) // 15)
    for side in (0, 1):
        for row in range(4):
            y = 424 + row * 10
            x = 72
            for _ in range(7):
                ln = r.uniform(6, 22)
                seg = [(x, y), (x + ln, y)]
                band(g, mirror(seg) if side else seg, 3.5, BAR if r.random() < 0.72 else ORG)
                x += ln + 5
                if x > 270:
                    break
    # starship readouts (bottom half of the panels)
    sd = 47634.4 + t * 3.0
    hdg = (274.6 + 6 * math.sin(tau * t)) % 360
    nav = [("HDG", f"{hdg:05.1f}\u00b0"), ("VEL", f"{0.82 + 0.03 * math.sin(tau * t * 2):.3f} c"),
           ("R.A.", f"14h29m{int(43 + t * 10) % 60:02d}s"), ("DEC", f"-62\u00b040'{46 - int(t * 8) % 10:02d}\"")]
    ship = [("HULL", f"{98.2 - 0.4 * (0.5 + 0.5 * math.sin(tau * t)):.1f}%"),
            ("SHIELD", f"{int(84 + 9 * math.sin(tau * t * 3))}%"),
            ("WARP", f"{3.42 + 0.02 * math.sin(tau * t * 4):.2f}"),
            ("STARDATE", f"{sd:.1f}")]
    for i, (k, v) in enumerate(nav):
        y = 482 + i * 19
        text(g, 74, y, k, 11, TEAL, "SemiBold")
        text(g, 276, y, v, 12, ORG if i == 1 else BAR, "Bold", "ra")
    for i, (k, v) in enumerate(ship):
        y = 482 + i * 19
        text(g, 1180 - 276, y, k, 11, TEAL, "SemiBold")
        text(g, 1180 - 74, y, v, 12, ORG if i == 1 else BAR, "Bold", "ra")
    # shield cells next to the SHIELD value
    lvl = int(6 + 2 * math.sin(tau * t * 3))
    for i in range(8):
        x = 1180 - 210 + i * 7
        slab(g, (x, 508), (x + 5, 508), 5, ORG if i < lvl else DIM)

    # --- four different loading bars ---
    # upper left: segmented cells filling up, leading cell orange
    n = 18; p = (t * 2) % 1; filled = int(p * (n + 4))
    for i in range(n):
        x = 250 + i * 8.6
        c_ = BAR if i < filled - 1 else (ORG if i == filled - 1 else DIM)
        g.polygon([P(x + 3, 322), P(x + 7.5, 322), P(x + 4.5, 335), P(x, 335)], fill=c_)
    text(g, 244, 309, "CORE SYNC", 9, TEAL, "SemiBold", "lm")
    text(g, 410, 309, f"{min(100, int(p * 122)):03d}%", 9, BAR, "Bold", "rm")
    # upper right: solid fill + moving hatch for the rest
    fill_to = 776 + 154 * (0.35 + 0.5 * (0.5 + 0.5 * math.sin(tau * t)))
    g.rectangle([*P(776, 322), *P(fill_to, 335)], fill=BAR)
    off = (t * 60) % 1 * 10
    x = fill_to + 3 - 10 + off
    while x < 930:
        x0, x1 = max(x, fill_to + 3), min(x + 4, 930)
        if x1 > x0:
            g.polygon([P(x0 + 3, 322), P(x1 + 3, 322), P(x1, 335), P(x0, 335)], fill=DTEAL)
        x += 10
    text(g, 770, 309, "NAV LOCK", 9, TEAL, "SemiBold", "lm")
    text(g, 936, 309, f"{int((fill_to - 776) / 1.54):03d}%", 9, BAR, "Bold", "rm")
    # lower left: spectrum bars
    for i in range(14):
        k = 1 + i % 4
        h = 5 + 26 * abs(math.sin(tau * t * k + i * 0.9))
        x = 304 + i * 8.4
        g.rectangle([*P(x, 756 - h), *P(x + 5, 756)], fill=ORG if h > 26 else BAR)
    text(g, 300, 708, "SUBSPACE FREQ", 9, TEAL, "SemiBold", "lm")
    # lower right: chevrons lighting in sequence
    head = int(t * 90) % 16
    for i in range(12):
        x = 764 + i * 9.6
        lit = 0 <= head - i < 5
        band(g, [(x, 726), (x + 6, 738), (x, 750)], 3, ORG if head - i == 0 else (BAR if lit else DIM))
    text(g, 880, 708, "THRUST VECTOR", 9, TEAL, "SemiBold", "rm")

    # readouts under the base
    v1 = int(8953 + 400 * math.sin(tau * t * 2)); v2 = int(15679 + 900 * math.cos(tau * t))
    for x in (396, 712):
        text(g, x, 664, f"{v1:05d}", 12, BAR, "Bold"); text(g, x + 52, 664, f"{v1 + 18:05d}", 12, DTEAL, "Bold")
        text(g, x, 680, f"{v2:05d}", 12, BAR, "Bold"); text(g, x + 52, 680, f"{v2 - 7:05d}", 12, DTEAL, "Bold")
    # corner targets (turning)
    for cx in (150, 1030):
        arc_band(g, cx, 728, 20, 0, 359.9, 1.6, BAR)
        for k in range(3):
            a = k * 120 + 240 * t * (1 if cx < 590 else -1)
            arc_band(g, cx, 728, 12, a, a + 70, 3, TEAL_L)
        g.ellipse([*P(cx - 3, 725), *P(cx + 3, 731)], fill=ORG)
    # orange pulses running along the wing rails
    for path in ([(100, 330), (236, 330)], [(30, 690), (196, 690), (246, 740), (292, 740)]):
        for q, ph in ((path, 0), (mirror(path), 0.5)):
            f = (t * 4 + ph) % 1
            band(g, [_along(q, f), _along(q, min(1, f + 0.04))], 5, ORG)
    # floating particles
    for px, py, amp, p0, orange in PARTS:
        x = px + amp * math.sin(tau * t + p0); y = py + amp * 0.6 * math.cos(tau * 2 * t + p0)
        b = 0.55 + 0.3 * math.sin(tau * 3 * t + p0)
        g.ellipse([*P(x - 1.8, y - 1.8), *P(x + 1.8, y + 1.8)], fill=col(ORG if orange else TEAL, b))
    # scan line
    sy = 200 + 600 * ((t * 5) % 1)
    line(g, [(60, sy), (1120, sy)], 1.2, (30, 100, 108))
    return im


def _along(pts, f):
    segs = list(zip(pts, pts[1:]))
    lens = [math.dist(a, b) for a, b in segs]
    d = f * sum(lens)
    for (a, b), l in zip(segs, lens):
        if d <= l:
            k = d / l
            return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        d -= l
    return pts[-1]


def glow(layer, k1=0.8, k2=0.6):
    small = layer.resize((W // 2, H // 2), Image.BILINEAR)
    b1 = small.filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
    b2 = small.filter(ImageFilter.GaussianBlur(16)).resize((W, H), Image.BILINEAR)
    return b1.point(lambda v: int(v * k1)), b2.point(lambda v: int(v * k2))


BG = STATIC = STATIC_GLOW = NOISE = None


def init():
    global BG, STATIC, STATIC_GLOW, NOISE
    BG = background()
    STATIC = static_layer().resize((W, H), Image.LANCZOS)
    STATIC_GLOW = glow(STATIC, 0.3, 0.2)
    NOISE = np.random.default_rng(5).normal(0, 1.1, (H, W, 1))


def compose(t):
    dyn = dynamic_layer(t).resize((W, H), Image.LANCZOS)
    core = core_layer(t).resize((W, H), Image.LANCZOS)
    dg = glow(dyn, 0.35, 0.2)
    img = BG
    for layer in (*STATIC_GLOW, *dg):
        img = ImageChops.add(img, layer)
    # the core sits on its own dark disc so nothing blurry shows through it
    mask = Image.new("L", (W, H), 0)
    rr = 190 * CS * K
    ImageDraw.Draw(mask).ellipse([SCX - rr, SCY - rr, SCX + rr, SCY + rr], fill=170)
    img = Image.composite(Image.new("RGB", (W, H), (6, 14, 19)), img, mask.filter(ImageFilter.GaussianBlur(30)))
    img = ImageChops.lighter(img, STATIC)
    img = ImageChops.lighter(img, dyn)
    img = ImageChops.lighter(img, core)
    a = np.asarray(img, dtype=np.float32) + NOISE
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def frame(job):
    n, out = job
    path = os.path.join(out, f"f{n:04d}.png")
    if not os.path.exists(path):
        compose(n / N).save(path, compress_level=1)


if __name__ == "__main__":
    if sys.argv[1] == "--still":                 # --still out.png [t 0..1]
        init()
        compose(float(sys.argv[3]) if len(sys.argv) > 3 else 0.25).save(sys.argv[2])
        sys.exit()
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    todo = [int(x) for x in sys.argv[2:]] or range(N)
    with Pool(4, initializer=init) as p:
        p.map(frame, [(n, out) for n in todo], chunksize=4)
