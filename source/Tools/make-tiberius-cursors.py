#!/usr/bin/env python3
"""Build the "Tiberius" cursor theme: dark angular shapes, teal edge, orange accents.

Writes both formats: cursors_scalable/ (SVG, used by Plasma 6) and cursors/ (Xcursor bitmaps,
used by everything else). Needs PySide6 (QtSvg) to draw the bitmaps.
Usage: make-tiberius-cursors.py ~/.local/share/icons/Tiberius-cursors [preview.png]
"""
import json, math, os, shutil, struct, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

T, TL, O, BG, OUT = "#22d3c5", "#5ae8dc", "#f28c38", "#0c1217", "#05080a"
BREEZE = "/usr/share/icons/breeze_cursors/cursors"
SIZES = (24, 30, 36, 48, 60, 72)
CAN = 32                                # drawing area; nominal size 24


def solid(d, edge=TL, w=1.5, body=BG):
    """Filled shape: dark halo (readable on white), coloured edge, dark body."""
    return (f'<path d="{d}" fill="{OUT}" stroke="{OUT}" stroke-opacity="0.75" stroke-width="{w + 2}" stroke-linejoin="miter"/>'
            f'<path d="{d}" fill="{body}" stroke="{edge}" stroke-width="{w}" stroke-linejoin="miter"/>')


def line(d, col=TL, w=1.8, halo=True):
    h = f'<path d="{d}" fill="none" stroke="{OUT}" stroke-opacity="0.8" stroke-width="{w + 2}" stroke-linecap="square"/>' if halo else ""
    return h + f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}"/>'


def fill(d, col=O):
    return f'<path d="{d}" fill="{col}"/>'


def rot(body, a, x=16, y=16):
    return f'<g transform="rotate({a:g} {x} {y})">{body}</g>'


# the main pointer is larger and filled, so it is easy to find on dark areas
ARROW_D = "M4 4V26L10 20H20Z"
ARROW = solid(ARROW_D, TL, 2, "#0e6f6b") + fill("M6.2 20.4V14.5L11 19.2L8.2 18.8Z")


def tri(cx, cy, r, turn, w):
    """Cut-corner triangle from the logo: three segments, one of them orange."""
    out = ""
    for i in range(3):
        a0, a1 = math.radians(turn + i * 120 - 90), math.radians(turn + i * 120 + 30)
        p, q = (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))
        f = lambda t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        a, b = f(0.2), f(0.8)
        # short bend at the cut corner
        am = math.radians(turn + i * 120 - 90)
        p2 = (cx + r * math.cos(math.radians(turn + (i + 2) * 120 - 90)), cy + r * math.sin(math.radians(turn + (i + 2) * 120 - 90)))
        c = (p[0] + (p2[0] - p[0]) * 0.2, p[1] + (p2[1] - p[1]) * 0.2)
        mid = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
        out += line(f"M{mid[0]:.2f} {mid[1]:.2f}L{a[0]:.2f} {a[1]:.2f}L{b[0]:.2f} {b[1]:.2f}", O if i == 0 else TL, w)
    return out


def ring(turn):
    return tri(16, 16, 13, turn, 2.4) + tri(16, 16, 5, -turn, 1.4)


def arrow_with(badge):
    return ARROW + badge


PLATE = "M21.5 20H30V27.5L27.5 30H19V22.5Z"
def shift(d, w, halo):
    return f'<g transform="translate(2 2)">{line(d, O, w, halo)}</g>'


def badge(inner, edge=T):
    return solid(PLATE, edge, 1.2) + inner


DOUBLE = solid("M16 2L22 8.5H18V23.5H22L16 30L10 23.5H14V8.5H10Z") + fill("M15.2 14H16.8V18H15.2Z")
FOUR = solid("M16 2L20 7H17.4V14.6H25V12L30 16L25 20V17.4H17.4V25H20L16 30L12 25H14.6V17.4H7V20L2 16L7 12V14.6H14.6V7H12Z") + fill("M14.6 14.6H17.4V17.4H14.6Z")
# no hands: clickable = orange arrow with target brackets; grab = open brackets; grabbing = clamped brackets
HAND = (solid(ARROW_D, O, 2, "#6e3d12") + fill("M6.2 20.4V14.5L11 19.2L8.2 18.8Z", TL)
        + line("M17 4H24L27 7V13", TL, 1.8) + line("M22 24V26L19 29H13", TL, 1.8))
def grips(a, b, w):
    """Four cut-corner brackets; a = outer edge, b = arm end, measured from the centre."""
    c = a - 3
    return "".join(rot(line(f"M{16 - a} {16 - b}V{16 - c}L{16 - c} {16 - a}H{16 - b}", TL, w), q) for q in (0, 90, 180, 270))
OPEN = grips(12, 5, 2) + solid("M16 11L21 16L16 21L11 16Z", O, 1.6) + fill("M15 15H17V17H15Z")
CLOSED = grips(8.5, 2, 2.2) + fill("M16 11.5L20.5 16L16 20.5L11.5 16Z")
OCT = "M11 4H21L28 11V21L21 28H11L4 21V11Z"
NO = line(OCT + "M8.5 8.5L23.5 23.5", O, 2.6)
IB = line("M11 5L13.5 5L16 7.5L18.5 5H21M16 7.5V24.5M11 27H13.5L16 24.5L18.5 27H21", TL, 1.8) + fill("M14.7 14.7H17.3V17.3H14.7Z")
CROSS = line("M16 3V12M16 20V29M3 16H12M20 16H29", TL, 1.6) + fill("M15 15H17V17H15Z")
COL = solid("M12 12V9L5 16L12 23V20H13.2V12ZM20 12V9L27 16L20 23V20H18.8V12Z") + line("M16 5V27", O, 1.4)
LENS = line("M9 4H17L22 9V15L17 20H9L4 15V9ZM19.5 17.5L27 25", TL, 2)
PLUS = solid("M13.5 5H18.5V13.5H27V18.5H18.5V27H13.5V18.5H5V13.5H13.5Z") + fill("M14.8 14.8H17.2V17.2H14.8Z")
UP = solid("M16 3L24 13H18.5V28H13.5V13H8Z") + line("M15 25.5H17", O, 1.6, False)

C = {   # name: (hotspot, body)
    "default": ((4, 4), ARROW),
    "right_ptr": ((28, 4), f'<g transform="translate(32 0) scale(-1 1)">{ARROW}</g>'),
    "center_ptr": ((16, 4), UP), "up-arrow": ((16, 3), UP),
    "down-arrow": ((16, 29), rot(UP, 180)), "left-arrow": ((3, 16), rot(UP, -90)), "right-arrow": ((29, 16), rot(UP, 90)),
    "pointer": ((4, 4), HAND), "openhand": ((16, 16), OPEN), "closedhand": ((16, 16), CLOSED), "dnd-move": ((16, 16), CLOSED),
    "text": ((16, 16), IB), "vertical-text": ((16, 16), rot(IB, 90)),
    "crosshair": ((16, 16), CROSS), "cell": ((16, 16), PLUS),
    "size_ver": ((16, 16), DOUBLE), "size_hor": ((16, 16), rot(DOUBLE, 90)),
    "size_fdiag": ((16, 16), rot(DOUBLE, -45)), "size_bdiag": ((16, 16), rot(DOUBLE, 45)),
    "fleur": ((16, 16), FOUR), "all-scroll": ((16, 16), FOUR),
    "col-resize": ((16, 16), COL), "row-resize": ((16, 16), rot(COL, 90)),
    "not-allowed": ((16, 16), NO), "x-cursor": ((16, 16), line("M6 6L26 26M26 6L6 26", O, 3)),
    "pirate": ((16, 16), line("M6 6L26 26M26 6L6 26", O, 3)),
    "copy": ((4, 4), arrow_with(badge(shift("M22.5 20.5V25.5M20 23H25", 1.6, False)))),
    "alias": ((4, 4), arrow_with(badge(shift("M20 25.5L25 20.5M21.5 20.5H25V24", 1.6, False)))),
    "context-menu": ((4, 4), arrow_with(badge(shift("M20 21H25.5M20 23.2H25.5M20 25.4H24", 1.2, False)))),
    "help": ((4, 4), arrow_with(badge(shift("M20.8 21V20.2H24.4V22.4L22.5 23.2V24.4M22.5 25.4V26.6", 1.5, False)))),
    "no-drop": ((4, 4), arrow_with(badge(shift("M20 20.5L25 25.5M25 20.5L20 25.5", 1.8, False), O))),
    "dnd-no-drop": ((4, 4), arrow_with(badge(shift("M20 20.5L25 25.5M25 20.5L20 25.5", 1.8, False), O))),
    "zoom-in": ((13, 12), LENS + line("M13 8.5V15.5M9.5 12H16.5", O, 1.8)),
    "zoom-out": ((13, 12), LENS + line("M9.5 12H16.5", O, 1.8)),
    "pencil": ((4, 28), solid("M4 28L6 20.5L21 5.5L26.5 11L11.5 26Z") + line("M18 8.5L23.5 14", O, 1.6, False)),
    "draft": ((4, 28), solid("M4 28L6 20.5L21 5.5L26.5 11L11.5 26Z") + line("M18 8.5L23.5 14", O, 1.6, False)),
    "color-picker": ((4, 28), solid("M4 28L5 23L16 12L14 10L16 8L18 10L22.5 4.5L27.5 9.5L22 14L24 16L22 18L20 16L9 27Z") + line("M9 22.5L11.5 25", O, 1.4, False)),
}
# window edges share the resize arrows
for a, b in (("top_side", "size_ver"), ("bottom_side", "size_ver"), ("left_side", "size_hor"), ("right_side", "size_hor"),
             ("top_left_corner", "size_fdiag"), ("bottom_right_corner", "size_fdiag"),
             ("top_right_corner", "size_bdiag"), ("bottom_left_corner", "size_bdiag"), ("wayland-cursor", "default")):
    C[a] = C[b]
N, DELAY = 36, 40
ANIM = {
    "wait": ((16, 16), [ring(360 / N * i) for i in range(N)]),
    "progress": ((4, 4), [ARROW + tri(24, 25, 6.5, 360 / N * i, 1.6) for i in range(N)]),
}


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{CAN}" height="{CAN}" viewBox="0 0 {CAN} {CAN}">{body}</svg>'


def render(body, px):
    img = QImage(px, px, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(svg(body).encode())).render(p)
    p.end()
    return img


def xcursor(path, hot, frames):
    chunks = []
    for s in SIZES:
        px = round(s * CAN / 24)
        for body in frames:
            img = render(body, px)
            data = bytes(img.constBits())
            k = px / CAN
            chunks.append((s, struct.pack("<9I", 36, 0xFFFD0002, s, 1, px, px, round(hot[0] * k), round(hot[1] * k),
                                          DELAY if len(frames) > 1 else 0) + data))
    pos = 16 + 12 * len(chunks)
    toc, body = b"", b""
    for s, c in chunks:
        toc += struct.pack("<3I", 0xFFFD0002, s, pos)
        pos += len(c)
        body += c
    with open(path, "wb") as f:
        f.write(b"Xcur" + struct.pack("<3I", 16, 0x10000, len(chunks)) + toc + body)


def main(dst, preview=None):
    app = QGuiApplication([])
    if os.path.exists(dst):
        shutil.rmtree(dst)
    xd, sd = os.path.join(dst, "cursors"), os.path.join(dst, "cursors_scalable")
    os.makedirs(xd); os.makedirs(sd)
    allc = {n: (h, [b]) for n, (h, b) in C.items()}
    allc.update(ANIM)
    for n, (hot, frames) in allc.items():
        xcursor(os.path.join(xd, n), hot, frames)
        d = os.path.join(sd, n)
        os.makedirs(d)
        meta = []
        for i, b in enumerate(frames):
            fn = f"{n}.svg" if len(frames) == 1 else f"{n}-{i + 1:02d}.svg"
            with open(os.path.join(d, fn), "w") as f:
                f.write(svg(b))
            m = {"filename": fn, "hotspot_x": hot[0], "hotspot_y": hot[1], "nominal_size": 24}
            if len(frames) > 1:
                m["delay"] = DELAY
            meta.append(m)
        with open(os.path.join(d, "metadata.json"), "w") as f:
            json.dump(meta, f, indent=1)
    links = 0
    for n in sorted(os.listdir(BREEZE)):            # same alias names as KDE's own set
        p = os.path.join(BREEZE, n)
        if os.path.islink(p) and n not in allc:
            for base in (xd, sd):
                os.symlink(os.readlink(p), os.path.join(base, n))
            links += 1
        elif n not in allc and not os.path.islink(p):
            print("not drawn:", n)
    for base in (xd, sd):
        for n in os.listdir(base):
            if not os.path.exists(os.path.join(base, n)):
                print("broken link", n)
    with open(os.path.join(dst, "index.theme"), "w") as f:
        f.write("[Icon Theme]\nName=Tiberius Cursors\nComment=Tiberius sci-fi HUD cursors\nInherits=breeze_cursors\n")
    print(f"{len(allc)} cursors, {links} aliases -> {dst}")
    if preview:
        from PySide6.QtGui import QColor, QFont
        names = [n for n in allc if n not in ("center_ptr", "dnd-move", "all-scroll", "pirate", "draft", "dnd-no-drop", "wayland-cursor")
                 and not n.endswith(("_side", "_corner"))]
        cols, cell = 10, 112
        rows = math.ceil(len(names) / cols)
        im = QImage(cols * cell, rows * cell + 90, QImage.Format_RGB32)
        im.fill(QColor("#11181d"))
        p = QPainter(im)
        for i, n in enumerate(names):
            fr = allc[n][1]
            x, y = i % cols * cell, i // cols * cell
            p.drawImage(x + 16, y + 8, render(fr[len(fr) // 5], 80))
            p.setPen(QColor("#9fb2ba")); p.drawText(x + 8, y + 106, n)
        for half, col in ((0, "#ffffff"), (1, "#0c1217")):      # real size on white and dark
            p.fillRect(half * cols * cell // 2, rows * cell + 10, cols * cell // 2, 80, QColor(col))
            for i, n in enumerate(names[:14]):
                fr = allc[n][1]
                p.drawImage(half * cols * cell // 2 + 14 + i * 38, rows * cell + 34, render(fr[0], 32))
        p.end()
        im.save(preview)


if __name__ == "__main__":
    main(os.path.expanduser(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None)
