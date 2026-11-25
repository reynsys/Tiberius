#!/usr/bin/env python3
"""Tiberius logo / Start-menu button: the wallpaper's cut-corner triangle, simplified
for small sizes. Three identical corner pieces (heavy chevron + narrower stepped arm),
a pointed orange chevron inside each corner, and a small solid cut-corner core.

Usage: make-tiberius-logo.py <out.svg>
"""
import math, sys

BAR, TEAL, ORG, DARK = "#d6f7f3", "#22d3c5", "#f28c38", "#0c0e11"
C = (32.0, 36.5)          # triangle centre
R = 33.0                  # centre -> virtual corner
CUT = 7.0                 # corner cut, along the edges
S3 = math.sqrt(3) / 2


def rot(p, deg):
    a = math.radians(deg)
    x, y = p[0] - C[0], p[1] - C[1]
    return (C[0] + x * math.cos(a) - y * math.sin(a), C[1] + x * math.sin(a) + y * math.cos(a))


def fmt(pts):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)


def corner(deg):
    A = (C[0], C[1] - R)
    edges = (((-0.5, S3), (-S3, -0.5)), ((0.5, S3), (S3, -0.5)))   # direction, outward normal
    def pt(s, e, off=0.0):
        d, n = e
        return rot((A[0] + s * d[0] + off * n[0], A[1] + s * d[1] + off * n[1]), deg)
    L, Rr = edges
    out = [f'<polyline points="{fmt([pt(CUT + 10, L), pt(CUT, L), pt(CUT, Rr), pt(CUT + 10, Rr)])}" '
           f'fill="none" stroke="{BAR}" stroke-width="6.4" stroke-linejoin="miter" stroke-miterlimit="8"/>']
    for e in edges:      # narrower stepped arm, aligned to the outer edge, after a small gap
        out.append(f'<line x1="{pt(CUT + 13, e, 1.4)[0]:.2f}" y1="{pt(CUT + 13, e, 1.4)[1]:.2f}" '
                   f'x2="{pt(CUT + 19, e, 1.4)[0]:.2f}" y2="{pt(CUT + 19, e, 1.4)[1]:.2f}" '
                   f'stroke="{TEAL}" stroke-width="3.6"/>')
    # pointed orange chevron
    O = (A[0], A[1] + CUT * S3 + 5.5)
    tip = lambda e, l: (O[0] + l * e[0][0], O[1] + l * e[0][1])
    inner = (O[0], O[1] + 5.0)
    out.append(f'<polygon points="{fmt([rot(p, deg) for p in (tip(L, 11), O, tip(Rr, 11), inner)])}" fill="{ORG}"/>')
    return out


def core():
    # small solid cut-corner triangle in the middle (reads at panel size)
    cx, cy = C
    t, k = 6.0, 0.22
    v = [(cx + t * math.cos(math.radians(-90 + i * 120)), cy + t * math.sin(math.radians(-90 + i * 120))) for i in range(3)]
    pts = []
    for i in range(3):
        p, q, o = v[i], v[(i + 1) % 3], v[(i - 1) % 3]
        pts += [(p[0] + (o[0] - p[0]) * k, p[1] + (o[1] - p[1]) * k), (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)]
    return [f'<polygon points="{fmt(pts)}" fill="{TEAL}"/>']


def main(out):
    body = []
    for deg in (0, 120, 240):
        body += corner(deg)
    body += core()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">\n  '
           + "\n  ".join(body) + "\n</svg>\n")
    with open(out, "w") as f:
        f.write(svg)


if __name__ == "__main__":
    main(sys.argv[1])
