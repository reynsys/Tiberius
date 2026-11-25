#!/usr/bin/env python3
"""Collect every Tiberius part into KDE Store packages (one archive per part) in ../Store.
Only our own artwork plus Apache-2.0 glyphs and the OFL font; reference images are never included."""
import json, os, re, shutil, subprocess, sys, tarfile
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
H = os.path.expanduser
out = os.path.join(root, "Store"); work = os.path.join(sys.argv[1], "pkg")
for d in (out, work):
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
run = lambda script, dst, *a: subprocess.run([sys.executable, os.path.join(here, script), *a, dst], check=True)
W = lambda *p: os.path.join(work, *p)
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w").write(text)
def pack(name, *dirs):
    with tarfile.open(os.path.join(out, name + ".tar.gz"), "w:gz") as t:
        for d in dirs:
            def clean(i):
                i.uid = i.gid = 0; i.uname = i.gname = ""          # no user name inside archives
                return i
            t.add(d, arcname=os.path.basename(d), filter=clean)
OFL = open(os.path.join(here, "sources/fonts/OFL.txt")).read()
APACHE = open(os.path.join(here, "sources/material-symbols-sharp/LICENSE")).read()

run("make-tiberius-icons.py", W("icons", "Tiberius"), os.path.join(here, "sources/material-symbols-sharp"))
write(W("icons/Tiberius/LICENSE-glyphs-Apache-2.0.txt"), "Glyphs: Material Symbols Sharp by Google, modified (placed in frames, recoloured).\n\n" + APACHE)
pack("Tiberius-icons", W("icons/Tiberius"))
run("make-tiberius-cursors.py", W("cursors", "Tiberius-cursors")) ; pack("Tiberius-cursors", W("cursors/Tiberius-cursors"))
run("make-tiberius-plasma-style.py", W("style", "Tiberius"))
shutil.copy(os.path.join(here, "Tiberius.colors"), W("style/Tiberius/colors")); pack("Tiberius-plasma-style", W("style/Tiberius"))
subprocess.run([sys.executable, os.path.join(here, "make-tiberius-window-decoration.py"), W("deco", "Tiberius"), "12"], check=True)
pack("Tiberius-window-decoration", W("deco/Tiberius"))
run("make-tiberius-kvantum.py", W("kv", "Tiberius")); pack("Tiberius-kvantum", W("kv/Tiberius"))
shutil.copy(os.path.join(here, "Tiberius.colors"), os.path.join(out, "Tiberius.colors"))
for w in ("clock", "keyboard"):
    src = os.path.join(root, "Widgets", "org.tiberius." + w)
    write(os.path.join(src, "contents/fonts/OFL.txt"), OFL)
    shutil.make_archive(os.path.join(out, f"org.tiberius.{w}"), "zip", src)
    os.rename(os.path.join(out, f"org.tiberius.{w}.zip"), os.path.join(out, f"org.tiberius.{w}.plasmoid"))
shutil.copy(os.path.join(root, "Wallpapers/tiberius-hud.png"), os.path.join(out, "Tiberius-wallpaper.png"))
shutil.copy(os.path.join(root, "Wallpapers/tiberius-hud.webm"), os.path.join(out, "Tiberius-wallpaper-video.webm"))
g = W("org.tiberius.desktop")
write(os.path.join(g, "metadata.json"), json.dumps({"KPackageStructure": "Plasma/LookAndFeel", "X-Plasma-APIVersion": "2",
    "KPlugin": {"Id": "org.tiberius.desktop", "Name": "Tiberius", "Description": "Sci-fi HUD desktop in teal and orange",
                "Authors": [{"Name": "Rey Osman"}], "License": "GPL-3.0-or-later", "Version": "0.1", "Category": ""}}, indent=4))
write(os.path.join(g, "contents/defaults"), """[kdeglobals][KDE]
widgetStyle=kvantum

[kdeglobals][General]
ColorScheme=Tiberius

[kdeglobals][Icons]
Theme=Tiberius

[plasmarc][Theme]
name=Tiberius

[kcminputrc][Mouse]
cursorTheme=Tiberius-cursors

[kwinrc][org.kde.kdecoration2]
library=org.kde.kwin.aurorae.v2
theme=__aurorae__svg__Tiberius
""")
prev = os.path.join(sys.argv[1], "store-preview.png")
if os.path.exists(prev):
    os.makedirs(os.path.join(g, "contents/previews"))
    subprocess.run(["magick", prev, "-resize", "600x", os.path.join(g, "contents/previews/preview.png")], check=True)
    subprocess.run(["magick", prev, "-quality", "90", os.path.join(g, "contents/previews/fullscreenpreview.jpg")], check=True)
    shutil.copy(prev, os.path.join(out, "preview-desktop.png"))
pack("Tiberius-global-theme", g)
for f in sorted(os.listdir(out)):
    print(f, os.path.getsize(os.path.join(out, f)) // 1024, "KB")
