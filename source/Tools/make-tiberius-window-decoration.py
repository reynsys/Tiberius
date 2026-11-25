#!/usr/bin/env python3
"""Build the "Tiberius" window decoration (Aurorae SVG theme).

Frame: 45-degree cuts top-left and bottom-right, teal edges, orange bevel bottom-right,
teal glow around the active window, HUD title bar with a raised button bay.
Changes title bars and borders only; the inside of windows belongs to Kvantum.

Usage: make-tiberius-window-decoration.py ~/.local/share/aurorae/themes/Tiberius
"""
import importlib.util, json, math, os, shutil, sys
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ps", os.path.join(here, "make-tiberius-plasma-style.py"))
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
TEAL, TEAL_L, ORG, BG = ps.TEAL, ps.TEAL_L, ps.ORG, ps.BG

P = 24                                  # room for the glow around the window
# KWin takes side/bottom thickness from its own "border size" option, not from the theme:
# Large = 8 px, Very Large = 12 px. Build for the size that will be used (2nd argument, default 12).
# Window contents are square, so the bottom-right cut must stay below twice the border.
SIDE = int(sys.argv[2]) if len(sys.argv) > 2 else 12
BOTTOM, TITLE = SIDE, 36
CUT = CUT_TL = CUT_BR = 2 * SIDE - 2
CL, CR, CT, CB, M = P + 110, P + 140, P + 70, P + 56, 20   # 9-slice sizes
BW, BH = 28, 22                         # buttons


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def shapes(active):
    """Everything in a frame, in sheet coordinates (window starts at P,P)."""
    W, H = CL + M + CR - 2 * P, CT + M + CB - 2 * P
    edge, edge_op = (TEAL, 0.95) if active else ("#3c5560", 0.8)
    hi = TEAL_L if active else "#4d6b76"
    org, org_op = (ORG, 1) if active else ("#8a5a34", 0.75)
    out = []
    pts, tags = ps.cut_polygon(W, H, {"tl": CUT_TL, "br": CUT_BR})

    def add(poly, col, op):
        out.append(([(x + P, y + P) for x, y in poly], col, op))

    # glow: many thin layers, strongest at the edge
    glow, peak = (TEAL, 0.012) if active else ("#000000", 0.018)
    for d in range(P - 1, 0, -1):
        add(ps.offset_polygon(pts, -d), glow, peak * (1 - d / P) + 0.003)
    for d in range(10, 0, -2):
        add(ps.offset_polygon(pts, -d), "#000000", 0.05)

    add(pts, BG, 1)
    # title bar body, slightly lighter, with a lit strip under the top edge
    add(ps.clip(pts, 0, 0, W, TITLE), "#13222b" if active else "#10171c", 0.9)
    add(ps.clip(pts, 0, 0, W, 5), TEAL, 0.10 if active else 0.03)

    # button bay (right): slanted raised panel reaching the right edge
    bx = W - 112
    bay = [(bx - 10, 4), (W - 4, 4), (W - 4, TITLE - 5), (bx + 17, TITLE - 5)]
    add(bay, TEAL, 0.10 if active else 0.04)
    add([(bx - 10, 4), (W - 4, 4), (W - 4, 5), (bx - 9.4, 5)], edge, 0.6 * edge_op)
    add([(bx - 10, 4), (bx - 8.6, 4), (bx + 18.4, TITLE - 5), (bx + 17, TITLE - 5)], edge, 0.8 * edge_op)
    # three slanted slashes left of the bay, fading out
    for i, op in enumerate((1, 0.65, 0.35)):
        x = bx - 14 - i * 7
        add([(x, 8), (x + 3, 8), (x + 16, 21), (x + 13, 21)], org, org_op * op)

    # separator under the title: thin line, heavy block at the left with a 45-degree step
    add(rect(0, TITLE - 2, W, 1.2), edge, 0.75 * edge_op)
    add([(CUT + 8, TITLE - 4), (CUT + 54, TITLE - 4), (CUT + 56.8, TITLE - 0.8), (CUT + 11.2, TITLE - 0.8)], hi, edge_op)
    for i in range(3):
        add(rect(CUT + 60 + i * 6, TITLE - 4, 3.5, 1.4), org, org_op * (1 - i * 0.25))
    # data ticks on the separator below the button bay
    for i in range(9):
        add(rect(W - 14 - i * 8, TITLE - 4.6, 1, 2.6 if i % 4 else 4), edge, 0.6 * edge_op)

    # outline
    inner = ps.offset_polygon(pts, 1.2)
    for i, tag in enumerate(tags):
        j = (i + 1) % len(pts)
        add([pts[i], pts[j], inner[j], inner[i]], org if tag == "br" else edge, 0.75 * edge_op)
    # corner motif (after ImG/corner-reference.png), drawn top-left, reflected bottom-right
    k = CUT
    L = round(k * 0.5) + 1
    motif = [
        # floating L in the true corner
        ([(-4, -4), (L - 4, -4), (L - 4, -1), (-1, -1), (-1, L - 4), (-4, L - 4)], 1),
        # bright segments on the two bends (slanted ends)
        ([(k - 6, 6), (k, 0), (k + 19, 0), (k + 16, 3), (k + 1.24, 3), (k - 1.76, 6)], 1),
        ([(6, k - 6), (0, k), (0, k + 19), (3, k + 16), (3, k + 1.24), (6, k - 1.76)], 1),
        # outer hairline, parallel to the edge, in the glow area
        ([(k + 40, -4), (k - 1.66, -4), (-4, k - 1.66), (-4, k + 26), (-3, k + 26), (-3, k - 1.24),
          (k - 1.24, -3), (k + 40, -3)], 0.6),
    ]
    # concave shapes are split into convex pieces before the 9-slice clipping
    def pieces(poly):
        n = len(poly)
        return [[poly[a], poly[a + 1], poly[n - 2 - a], poly[n - 1 - a]] for a in range(n // 2 - 1)]
    Lshape = motif[0][0]
    quads = [([Lshape[0], Lshape[1], Lshape[2], Lshape[3]], 1), ([Lshape[0], Lshape[3], Lshape[4], Lshape[5]], 1)]
    quads += [(q, op) for poly, op in motif[1:] for q in pieces(poly)]
    for q, op in quads:
        add(q, hi, edge_op * op)
        add([(W - x, H - y) for x, y in q], org, org_op * op)
    # square corners: the same L bracket twice, top-right orange, bottom-left teal
    br = [[(0, 0), (30, 0), (27, 3), (0, 3)], [(0, 0), (3, 0), (3, 27), (0, 30)],
          rect(-4, -4, 40, 1), rect(-4, -4, 1, 40)]
    for n, q in enumerate(br):
        op = 1 if n < 2 else 0.6
        add([(W - x, y) for x, y in q], org, org_op * op)
        add([(x, H - y) for x, y in q], hi, edge_op * op)
    # inner hairline next to the window contents and side markers
    add(rect(SIDE - 2.4, TITLE + 26, 0.8, H - TITLE - 66), edge, 0.45 * edge_op)
    add(rect(W - SIDE + 1.6, TITLE + 8, 0.8, H - TITLE - 60), edge, 0.45 * edge_op)
    for i in range(3):
        add(rect(SIDE - 4.6, TITLE + 8 + i * 4, 1.6, 2.4), org if i == 0 else edge, 0.9 * edge_op)
        add(rect(W - SIDE + 3, H - 36 - i * 4, 1.6, 2.4), org if i == 0 else edge, 0.9 * edge_op)
    # bottom border readouts
    for i in range(4):
        add(rect(38 + i * 7, H - SIDE / 2 - 1, 4.4, 1.6), edge, (0.9 - i * 0.18) * edge_op)
    for i in range(6):
        add(rect(W - 80 - i * 5, H - SIDE / 2 - 1, 1, 2.5), edge, 0.6 * edge_op)
    return out


class Sheet(ps.Sheet):
    def nine(self, prefix, shp):
        xs, ys = [0, CL, CL + M, CL + M + CR], [0, CT, CT + M, CT + M + CB]
        for r in range(3):
            for c in range(3):
                x0, x1, y0, y1 = xs[c], xs[c + 1], ys[r], ys[r + 1]
                g = [f'<rect x="{x0}" y="{self.y + y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#000" fill-opacity="0.001"/>']
                for poly, col, op in shp:
                    cp = ps.clip(poly, x0, y0, x1, y1)
                    if len(cp) >= 3:
                        g.append(f'<path d="{ps.poly_d(cp, 0, self.y)}" fill="{col}" fill-opacity="{op:.4f}"/>')
                self.parts.append(f'<g id="{prefix}-{ps.SLICES[r * 3 + c]}">' + "".join(g) + "</g>")
        self.y += ys[3] + 10

    def single(self, name, w, h, body):
        self.parts.append(f'<g id="{name}"><rect x="0" y="{self.y}" width="{w}" height="{h}" fill="#000" fill-opacity="0.001"/>'
                          f'<g transform="translate(0 {self.y})">{body}</g></g>')
        self.y += h + 10

    def save(self, path):
        w = CL + M + CR + 20
        with open(path, "w") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{self.y + 10}" viewBox="0 0 {w} {self.y + 10}">\n'
                    + "\n".join(self.parts) + f'\n<rect id="hint-stretch-borders" x="{w - 6}" y="0" width="4" height="4" fill-opacity="0.001"/>\n'
                    + f'<rect id="hint-tile-center" x="{w - 6}" y="8" width="4" height="4" fill-opacity="0.001"/>\n</svg>\n')


def decoration(path):
    sh = Sheet()
    sh.nine("decoration", shapes(True))
    sh.nine("decoration-inactive", shapes(False))
    W, H = CL + M + CR - 2 * P, CT + M + CB - 2 * P
    pts, _ = ps.cut_polygon(W, H, {"tl": CUT_TL, "br": CUT_BR})
    sh.nine("mask", [([(x + P, y + P) for x, y in pts], "#000", 1)])
    for name, body, line in (("decoration-maximized", "#13222b", TEAL), ("decoration-maximized-inactive", "#10171c", "#3c5560")):
        sh.single(name + "-center", 40, TITLE - 4, f'<rect width="40" height="{TITLE - 4}" fill="{body}"/>'
                  f'<rect y="{TITLE - 5.4}" width="40" height="1.4" fill="{line}" fill-opacity="0.8"/>')
    sh.save(path)


# ---------- buttons: glyphs in a 28 x 22 box, stroke colour filled in later ----------
GLYPH = {
    "close": "M9.5 6.5L18.5 15.5M18.5 6.5L9.5 15.5",
    "minimize": "M9 14.5H19M9 14.5V12M19 14.5V12",
    "maximize": "M11.5 6.5H19V13L16.5 15.5H9V9Z",
    "restore": "M11 6.5H19V12.5H17M9 9.5H16V15.5H9Z",
    "alldesktops": "M14 6L19 11L14 16L9 11ZM14 10V12",
    "keepabove": "M9 12L14 7L19 12M9 16L14 11L19 16",
    "keepbelow": "M9 6L14 11L19 6M9 10L14 15L19 10",
    "shade": "M9 6.5H19M10 14.5L14 10.5L18 14.5",
    "help": "M10.5 8.5L12.5 6.5H16L18 8.5V10L14.2 12V13.2M14.2 15V16.4",
    "appmenu": "M9 7H19M9 11H19M9 15H15",
}


def button(path, name):
    close = name == "close"
    main = ORG if close else TEAL
    plate = "M6 1.5H26.5V15.5L21.5 20.5H1.5V6Z"
    def draw(fill, fop, line, lop, glyph, gop, bevel, bop):
        return (f'<path d="{plate}" fill="{fill}" fill-opacity="{fop}" stroke="{line}" stroke-opacity="{lop}" stroke-width="1"/>'
                f'<path d="M26.5 15.5L21.5 20.5" stroke="{bevel}" stroke-opacity="{bop}" stroke-width="2"/>'
                f'<path d="{GLYPH[name]}" fill="none" stroke="{glyph}" stroke-opacity="{gop}" stroke-width="1.6" stroke-linejoin="miter"/>')
    st = {
        "active": draw(main, 0.10, main, 0.75, ORG if close else TEAL_L, 1, ORG, 1),
        "hover": draw(main, 0.95, main, 1, BG, 1, "#ffd0a0" if close else ORG, 1),
        "pressed": draw(main, 0.60, main, 1, "#ffffff", 1, ORG, 1),
        "deactivated": draw("#3c5560", 0.05, "#3c5560", 0.4, "#3c5560", 0.8, "#3c5560", 0.4),
        "inactive": draw("#3c5560", 0.08, "#3c5560", 0.7, "#6f8792", 0.9, "#8a5a34", 0.7),
        "hover-inactive": draw(main, 0.45, main, 0.9, "#ffffff", 1, ORG, 1),
        "pressed-inactive": draw(main, 0.60, main, 1, "#ffffff", 1, ORG, 1),
        "deactivated-inactive": draw("#3c5560", 0.03, "#3c5560", 0.25, "#3c5560", 0.5, "#3c5560", 0.25),
    }
    sh = Sheet()
    for k, body in st.items():
        sh.single(k + "-center", BW, BH, body)
    sh.save(path)


RC = f"""[General]
ActiveTextColor=220,240,240,255
InactiveTextColor=120,135,143,255
UseTextShadow=false
TitleAlignment=Left
TitleVerticalAlignment=Center
Animation=120
DecorationPosition=0
Shadow=true

[Layout]
BorderLeft={SIDE}
BorderRight={SIDE}
BorderBottom={BOTTOM}
TitleEdgeTop=6
TitleEdgeBottom=8
TitleEdgeLeft={CUT + 8}
TitleEdgeRight=12
TitleEdgeTopMaximized=4
TitleEdgeBottomMaximized=6
TitleEdgeLeftMaximized=8
TitleEdgeRightMaximized=6
TitleBorderLeft=8
TitleBorderRight=48
TitleHeight={BH}
ButtonWidth={BW}
ButtonWidthMenu=22
ButtonHeight={BH}
ButtonSpacing=3
ButtonMarginTop=0
ExplicitButtonSpacer=8
PaddingTop={P}
PaddingBottom={P}
PaddingLeft={P}
PaddingRight={P}
"""


def main(dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    decoration(os.path.join(dst, "decoration.svg"))
    for n in GLYPH:
        button(os.path.join(dst, n + ".svg"), n)
    with open(os.path.join(dst, os.path.basename(dst.rstrip("/")) + "rc"), "w") as f:
        f.write(RC)
    plugin = {"KPlugin": {"Id": "Tiberius", "Name": "Tiberius", "License": "GPL-3.0-or-later", "Version": "0.1",
                          "Description": "Tiberius sci-fi HUD window decoration", "Authors": [{"Name": "Rey Osman"}]}}
    with open(os.path.join(dst, "metadata.json"), "w") as f:
        json.dump(plugin, f, indent=4)
    with open(os.path.join(dst, "metadata.desktop"), "w") as f:
        f.write("[Desktop Entry]\nName=Tiberius\nComment=Tiberius sci-fi HUD window decoration\n"
                "X-KDE-PluginInfo-Author=Rey Osman\nX-KDE-PluginInfo-Name=Tiberius\n"
                "X-KDE-PluginInfo-Version=0.1\nX-KDE-PluginInfo-License=GPL-3.0-or-later\n")
    print("Tiberius window decoration ->", dst)


if __name__ == "__main__":
    main(os.path.expanduser(sys.argv[1]))
