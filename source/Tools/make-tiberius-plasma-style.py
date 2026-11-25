#!/usr/bin/env python3
"""Build the "Tiberius" Plasma style (panel, popups, tooltips, task and list highlights).

Every frame is a Plasma 9-slice SVG (topleft, top, topright, left, center, right, bottomleft,
bottom, bottomright, optionally with a prefix such as "mask-", "shadow-", "focus-" ...).
Frames are drawn like the Tiberius icon plates: 45-degree cut corners (top-left and
bottom-right), thin teal border, light bevel on the top-left cut, orange bevel on the
bottom-right cut, a short orange bar at the top right and dashes at the bottom left.

Files we don't draw fall back to Breeze (Plasma's "default" style).

Usage: make-tiberius-plasma-style.py <output dir, e.g. ~/.local/share/plasma/desktoptheme/Tiberius>
"""
import gzip, json, math, os, shutil, sys

TEAL, TEAL_L, ORG, BG = "#22d3c5", "#5ae8dc", "#f28c38", "#0c1217"
SLICES = ("topleft", "top", "topright", "left", "center", "right", "bottomleft", "bottom", "bottomright")


# ---------------- geometry ----------------
def cut_polygon(W, H, k):
    """Outer polygon with 45-degree cuts. k = dict(tl, tr, br, bl). Returns points + side tags."""
    tl, tr, br, bl = (k.get(n, 0) for n in ("tl", "tr", "br", "bl"))
    pts, tags = [], []
    def add(p, tag):
        if pts and abs(pts[-1][0] - p[0]) < 1e-9 and abs(pts[-1][1] - p[1]) < 1e-9:
            tags[-1] = tag                  # zero-length cut: the edge from here is the next side
        else:
            pts.append(p); tags.append(tag)
    add((0, tl), "tl"); add((tl, 0), "top"); add((W - tr, 0), "tr"); add((W, tr), "right")
    add((W, H - br), "br"); add((W - br, H), "bottom"); add((bl, H), "bl"); add((0, H - bl), "left")
    if abs(pts[0][0] - pts[-1][0]) < 1e-9 and abs(pts[0][1] - pts[-1][1]) < 1e-9:
        pts.pop(); tags.pop()
    # tag i = side of the edge that STARTS at point i
    return pts, tags


def offset_polygon(pts, d):
    """Inset a convex clockwise polygon by d (screen coords, y down)."""
    n = len(pts)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy)
        nx, ny = -dy / l, dx / l            # inward normal for clockwise order on screen
        lines.append(((a[0] + nx * d, a[1] + ny * d), (dx, dy)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-12:
            out.append(p2); continue
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def clip(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman clip of a polygon to a rectangle."""
    def edge(points, inside, inter):
        res = []
        for i in range(len(points)):
            cur, prev = points[i], points[i - 1]
            if inside(cur):
                if not inside(prev):
                    res.append(inter(prev, cur))
                res.append(cur)
            elif inside(prev):
                res.append(inter(prev, cur))
        return res
    def ix(x):
        return lambda p, q: (x, p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0]))
    def iy(y):
        return lambda p, q: (p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1]), y)
    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not poly:
            break
        poly = edge(poly, inside, inter)
    return poly


def poly_d(poly, dx, dy):
    return "M" + " L".join(f"{x + dx:.3f},{y + dy:.3f}" for x, y in poly) + " Z"


# ---------------- frame description ----------------
def frame_shapes(f, W, H):
    """List of (polygon, fill, opacity) for a frame spec drawn at size W x H."""
    out, inner = [], None
    pts, tags = cut_polygon(W, H, f.get("cuts", {}))
    b = f.get("border", 0)
    if f.get("fill"):
        out.append((offset_polygon(pts, b * 0.5) if b else pts, f["fill"], f.get("fill_opacity", 1)))
    sides = f.get("sides", {})                  # side -> (width, colour, opacity)
    for i, tag in enumerate(tags):
        spec = sides.get(tag) or (sides.get("all") if tag not in sides else None)
        if tag in ("tl", "tr", "br", "bl") and tag not in sides:
            spec = sides.get("cuts") or sides.get("all")
        if not spec:
            continue
        w, colr, op = spec
        a, c = pts[i], pts[(i + 1) % len(pts)]
        inner = offset_polygon(pts, w)
        out.append(([a, c, inner[(i + 1) % len(pts)], inner[i]], colr, op))
    for acc in f.get("accents", []):
        out.append(acc(W, H))
    return out


def accent_bevel(corner, width, colour, opacity=1.0, k=None):
    """Thick band lying on a cut corner (like the icon plates' bevels)."""
    def make(W, H, corner=corner, width=width, colour=colour, opacity=opacity, k=k):
        kk = k
        if corner == "tl":
            a, c, n = (0, kk), (kk, 0), (1, 1)
        elif corner == "br":
            a, c, n = (W, H - kk), (W - kk, H), (-1, -1)
        elif corner == "tr":
            a, c, n = (W - kk, 0), (W, kk), (-1, 1)
        else:
            a, c, n = (kk, H), (0, H - kk), (1, -1)
        s = width / math.sqrt(2)
        return ([a, c, (c[0] + n[0] * s, c[1] + n[1] * s), (a[0] + n[0] * s, a[1] + n[1] * s)], colour, opacity)
    return make


def accent_rect(fx, fy, w, h, colour, opacity=1.0):
    """Rectangle positioned relative to a corner: fx/fy are callables (W,H)->x/y."""
    def make(W, H):
        x, y = fx(W, H), fy(W, H)
        return ([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], colour, opacity)
    return make


# ---------------- SVG writer ----------------
class Sheet:
    def __init__(self):
        self.parts, self.y = [], 0

    def frame(self, prefix, f, C, M=None):
        """Draw the 9 slices of frame f with corner size C (middle M) under the given prefix."""
        M = M or C
        W = H = 2 * C + M
        shapes = frame_shapes(f, W, H)
        ox, oy = 0, self.y
        cuts = [0, C, C + M, W]
        for r in range(3):
            for c in range(3):
                name = prefix + SLICES[r * 3 + c]
                x0, x1, y0, y1 = cuts[c], cuts[c + 1], cuts[r], cuts[r + 1]
                g = [f'<rect x="{ox + x0}" y="{oy + y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#000" fill-opacity="0.004"/>']
                for poly, colr, op in shapes:
                    cp = clip(poly, x0, y0, x1, y1)
                    if len(cp) >= 3:
                        g.append(f'<path d="{poly_d(cp, ox, oy)}" fill="{colr}" fill-opacity="{op}"/>')
                self.parts.append(f'<g id="{name}">' + "".join(g) + "</g>")
        self.y += W + 10

    def hints(self, prefix, margins):
        for side, v in margins.items():
            if v is None:
                continue
            w, h = (v, 2) if side in ("left", "right") else (2, v)
            self.parts.append(f'<rect id="{prefix}hint-{side}-margin" x="{400 + len(self.parts) % 7 * 12}" '
                              f'y="{self.y}" width="{max(w, 0.0001)}" height="{max(h, 0.0001)}" fill="#ff00ff" fill-opacity="0.004"/>')
            self.y += max(h, 2) + 2

    def shadow(self, size, strength=0.45):
        """9-slice shadow (gradients only, QtSvg has no blur)."""
        s, uid = size, len(self.parts)
        oy = self.y
        defs = [
            f'<linearGradient id="sg{uid}v" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity="{strength}"/></linearGradient>',
            f'<radialGradient id="sg{uid}r" cx="1" cy="1" r="1"><stop offset="0" stop-color="#000" stop-opacity="{strength}"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>']
        self.parts.append("<defs>" + "".join(defs) + "</defs>")
        def corner(name, rot, x, y):
            self.parts.append(f'<g id="shadow-{name}"><rect x="{x}" y="{y}" width="{s}" height="{s}" fill="url(#sg{uid}r)" '
                              f'transform="rotate({rot} {x + s / 2} {y + s / 2})"/></g>')
        def side(name, rot, x, y, w, h):
            self.parts.append(f'<g id="shadow-{name}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#sg{uid}v)" '
                              f'transform="rotate({rot} {x + w / 2} {y + h / 2})"/></g>')
        corner("topleft", 0, 0, oy); side("top", 0, s, oy, s, s); corner("topright", 90, 2 * s, oy)
        side("left", -90, 0, oy + s, s, s)
        self.parts.append(f'<rect id="shadow-center" x="{s}" y="{oy + s}" width="{s}" height="{s}" fill="#000" fill-opacity="0"/>')
        side("right", 90, 2 * s, oy + s, s, s)
        corner("bottomleft", -90, 0, oy + 2 * s); side("bottom", 180, s, oy + 2 * s, s, s); corner("bottomright", 180, 2 * s, oy + 2 * s)
        self.y += 3 * s + 10
        self.hints("shadow-", {"top": s, "bottom": s, "left": s, "right": s})

    def write(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not any('id="hint-stretch-borders"' in p for p in self.parts):
            self.parts.append('<rect id="hint-stretch-borders" x="580" y="0" width="4" height="4" fill-opacity="0.004"/>')
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="%d">\n' % (self.y + 20)
               + "\n".join(self.parts) + "\n</svg>\n")
        with gzip.open(path, "wb") as f:
            f.write(svg.encode())


# ---------------- the Tiberius frames ----------------
def plate(C, cut, fill_op, border_op=0.85, bevels=True, bar=True, dashes=True, b=1.4):
    f = {"cuts": {"tl": cut, "br": cut}, "fill": BG, "fill_opacity": fill_op, "border": b,
         "sides": {"all": (b, TEAL, border_op)}, "accents": []}
    if bevels:
        f["accents"] += [accent_bevel("tl", 2.6, TEAL_L, 1, cut), accent_bevel("br", 3.2, ORG, 1, cut)]
    if bar:
        f["accents"].append(accent_rect(lambda W, H: W - C + 2, lambda W, H: 3.2, C - 6, 1.6, ORG))
    if dashes:
        step = (C - 5) / 3                       # keep the dashes inside the corner piece
        for i in range(3):
            f["accents"].append(accent_rect(lambda W, H, i=i: 3 + i * step, lambda W, H: H - 4.4,
                                            step * 0.6, 1.4, TEAL, 0.7))
    return f


def mask_of(f):
    return {"cuts": f["cuts"], "fill": "#000", "fill_opacity": 1}


def dialog_like(path, C=20, cut=10, fill_op=0.95, margin=10, shadow=12):
    sh = Sheet()
    f = plate(C, cut, fill_op)
    sh.frame("", f, C)
    sh.frame("mask-", mask_of(f), C)
    sh.hints("", {"top": margin, "bottom": margin, "left": margin, "right": margin})
    if shadow:
        sh.shadow(shadow)
    sh.write(path)


def corner_motif(W, H, k, arm_x, arm_y, thick=2.6, hair=20, hair_b=8):
    """Corner design from ImG/corner-reference.png, kept inside the W x H rectangle.
    Returns [(convex polygon, colour, opacity)]: L in the cut-off corner, inner line with bright
    segments on the bends (top-left teal, bottom-right orange) and equal square brackets."""
    d = 3                                                # distance of the inner line
    n = k + d * (2 - math.sqrt(2))                       # inner line bends at (n, d) and (d, n)
    e = d + thick
    m = n + thick * (2 - math.sqrt(2)) - 0               # inner side of the bright segments
    L = k * 0.5
    q = [([(0, 0), (L, 0), (L, 2.6), (2.6, 2.6)], 1), ([(0, 0), (2.6, 2.6), (2.6, L), (0, L)], 1)]
    # inner hairline: diagonal + run along the top
    q += [([(n, d), (d, n), (d + 0.6, n + 0.4), (n + 0.4, d + 0.6)], 0.8),
          ([(n, d), (arm_x + hair, d), (arm_x + hair, d + 0.8), (n, d + 0.8)], 0.7)]
    # bright segments: along the edges, then a short piece down the diagonal
    sl = thick
    q += [([(n, d), (arm_x, d), (arm_x - sl, e), (m, e)], 1), ([(n, d), (m, e), (n - 4 + (m - n), e + 2), (n - 4, d + 4)], 1),
          ([(d, n), (d, arm_y), (e, arm_y - sl), (e, m)], 1), ([(d, n), (e, m), (e + 2, n - 4 + (m - n)), (d + 4, n - 4)], 1)]
    out = []
    for poly, op in q:
        out.append((poly, TEAL_L, op))
        out.append(([(W - x, H - y) for x, y in poly], ORG, op))
    b = [([(0, 0), (arm_x, 0), (arm_x - 3, 3), (3, 3)], 1), ([(0, 0), (3, 3), (3, arm_y - 8), (0, arm_y - 5)], 1),
         ([(6, 5.4), (arm_x + hair_b, 5.4), (arm_x + hair_b, 6.2), (6, 6.2)], 0.6)]
    for poly, op in b:
        out.append(([(W - x, y) for x, y in poly], ORG, op))
        out.append(([(x, H - y) for x, y in poly], TEAL_L, op))
    return out


def panel(path):
    sh = Sheet()
    k, M = 17, 8

    def nine(prefix, shapes, cx, cy):
        xs, ys = [0, cx, cx + M, 2 * cx + M], [0, cy, cy + M, 2 * cy + M]
        for r in range(3):
            for c in range(3):
                g = [f'<rect x="{xs[c]}" y="{sh.y + ys[r]}" width="{xs[c + 1] - xs[c]}" height="{ys[r + 1] - ys[r]}" fill="#000" fill-opacity="0.004"/>']
                for poly, colr, op in shapes:
                    cp = clip(poly, xs[c], ys[r], xs[c + 1], ys[r + 1])
                    if len(cp) >= 3:
                        g.append(f'<path d="{poly_d(cp, 0, sh.y)}" fill="{colr}" fill-opacity="{op}"/>')
                sh.parts.append(f'<g id="{prefix}{SLICES[r * 3 + c]}">' + "".join(g) + "</g>")
        sh.y += ys[3] + 10

    f = {"cuts": {"tl": k, "br": k}, "fill": BG, "fill_opacity": 0.93, "border": 1.4,
         "sides": {"all": (1.4, TEAL, 0.85), "br": (1.4, ORG, 0.85)}}
    cx, cy = 64, 22                              # two corners must fit in the 46 px panel height
    W, H = 2 * cx + M, 2 * cy + M
    shapes = frame_shapes(f, W, H) + corner_motif(W, H, k, 38, cy)
    pts, _ = cut_polygon(W, H, f["cuts"])
    nine("", shapes, cx, cy)
    nine("mask-", [(pts, "#000", 1)], cx, cy)
    sh.hints("", {"top": 4, "bottom": 2, "left": 12, "right": 20})
    sh.hints("thick-", {"top": 6, "bottom": 6, "left": 12, "right": 20})
    sh.shadow(10, 0.35)
    sh.write(path)


def popup(path, C=28, k=17, fill_op=1, margin=10, shadow=12):
    """Popups and widgets: the taskbar's corners in a small 9-slice (smallest popup 56 px)."""
    sh = Sheet()
    f = {"cuts": {"tl": k, "br": k}, "fill": BG, "fill_opacity": fill_op, "border": 1.4,
         "sides": {"all": (1.4, TEAL, 0.85), "br": (1.4, ORG, 0.85)},
         "accents": []}
    W = 3 * C
    for poly, colr, op in corner_motif(W, W, k, C, C, hair=0, hair_b=0):
        f["accents"].append(lambda _w, _h, t=(poly, colr, op): t)
    sh.frame("", f, C)
    sh.frame("mask-", {"cuts": f["cuts"], "fill": "#000", "fill_opacity": 1}, C)
    sh.hints("", {"top": margin, "bottom": margin, "left": margin, "right": margin})
    if shadow:
        sh.shadow(shadow)
    sh.write(path)


def heading(path):
    sh = Sheet()
    hdr = {"fill": "#13222b", "fill_opacity": 0, "border": 0,
           "sides": {"bottom": (1.4, TEAL, 0.7)},
           "accents": [accent_rect(lambda W, H: 0, lambda W, H: H - 2.4, 12, 2.4, ORG)]}
    ftr = {"fill": "#13222b", "fill_opacity": 0, "border": 0, "sides": {"top": (1.4, TEAL, 0.5)}}
    sh.frame("header-", hdr, 8)
    sh.frame("footer-", ftr, 8)
    sh.parts.append('<rect id="hint-stretch-borders" x="500" y="0" width="4" height="4" fill-opacity="0.004"/>')
    sh.hints("", {"top": 6, "bottom": 6, "left": 8, "right": 8})
    sh.write(path)


def viewitem(path):
    sh = Sheet()
    C, cut = 6, 4
    def item(fill_op, border_op):
        f = {"cuts": {"tl": cut, "br": cut}, "fill": TEAL, "fill_opacity": fill_op, "border": 1}
        if border_op:
            f["sides"] = {"all": (1, TEAL, border_op)}
            f["accents"] = [accent_bevel("br", 2, ORG, border_op, cut)]
        return f
    sh.frame("normal-", item(0, 0), C)
    sh.frame("hover-", item(0.10, 0.55), C)
    sh.frame("selected-", item(0.20, 0.8), C)
    sh.frame("selected+hover-", item(0.28, 1.0), C)
    sh.hints("", {"top": 4, "bottom": 4, "left": 6, "right": 6})
    sh.write(path)


def tasks(path):
    sh = Sheet()
    C = 6
    edge_for = {"": "bottom", "north-": "top", "west-": "left", "east-": "right"}
    for loc, edge in edge_for.items():
        def st(line_w, line_col, line_op, fill_op, border_op=0, fill=TEAL):
            f = {"fill": fill, "fill_opacity": fill_op, "border": 0, "sides": {edge: (line_w, line_col, line_op)}}
            if border_op:
                f["cuts"] = {"tl": 3, "br": 3}
                f["sides"] = {"all": (1, TEAL, border_op), edge: (line_w, line_col, line_op)}
            return f
        # running (open or minimised) = solid teal line, active = orange line,
        # needs attention = orange line + orange tint + outline
        sh.frame(loc + "normal-", st(3, TEAL, 1, 0), C)
        sh.frame(loc + "focus-", st(3, ORG, 1, 0.12), C)
        sh.frame(loc + "hover-", st(3, TEAL_L, 1, 0.10, border_op=0.6), C)
        sh.frame(loc + "attention-", {"fill": ORG, "fill_opacity": 0.22, "cuts": {"tl": 3, "br": 3},
                                      "sides": {"all": (1, ORG, 0.8), edge: (3, ORG, 1)}}, C)
        sh.frame(loc + "minimized-", st(3, TEAL, 1, 0), C)
        sh.frame(loc + "progress-", st(0.01, TEAL, 0, 0.28), C)
    sh.write(path)


def metadata(dst):
    meta = {
        "KPlugin": {
            "Authors": [{"Name": "Rey Osman"}],
            "Category": "",
            "Description": "Tiberius sci-fi HUD style: 45-degree cut corners, teal edges, orange accents",
            "Id": "Tiberius",
            "License": "GPL-3.0-or-later",
            "Name": "Tiberius",
            "Version": "0.1",
        },
        "X-Plasma-API": "5.0",
    }
    with open(os.path.join(dst, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=4)
    with open(os.path.join(dst, "plasmarc"), "w") as f:
        f.write("[Settings]\nFallbackTheme=default\n\n[AdaptiveTransparency]\nenabled=true\n")


def main(dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    metadata(dst)
    # Plasma may pick a "translucent", "opaque" or "solid" variant; give all of them our art
    for variant in ("", "translucent/", "opaque/", "solid/"):
        base = os.path.join(dst, variant)
        popup(os.path.join(base, "dialogs", "background.svgz"))
        popup(os.path.join(base, "widgets", "background.svgz"))
        dialog_like(os.path.join(base, "widgets", "tooltip.svgz"), C=12, cut=6, margin=7, shadow=8)
        panel(os.path.join(base, "widgets", "panel-background.svgz"))
    heading(os.path.join(dst, "widgets", "plasmoidheading.svgz"))
    viewitem(os.path.join(dst, "widgets", "viewitem.svgz"))
    tasks(os.path.join(dst, "widgets", "tasks.svgz"))
    print("Tiberius Plasma style ->", dst)


if __name__ == "__main__":
    main(os.path.expanduser(sys.argv[1]))
