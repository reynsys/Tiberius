#!/usr/bin/env python3
"""Build the "Tiberius" Kvantum theme (the inside of application windows: buttons, tabs, menus,
fields, scrollbars, sliders ...). All artwork is drawn here; missing parts fall back to Kvantum's default.

Usage: make-tiberius-kvantum.py ~/.config/Kvantum/Tiberius
"""
import importlib.util, os, shutil, sys
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ps", os.path.join(here, "make-tiberius-plasma-style.py"))
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)
T, TL, O = ps.TEAL, ps.TEAL_L, ps.ORG
WIN, BASE, ALT, RAISED, TEXT, DIM, LINE = "#1a1e22", "#14181c", "#181d21", "#1f262b", "#dce3e8", "#78818a", "#2b4149"
PIECE = {"topleft": (0, 0), "top": (1, 0), "topright": (2, 0), "left": (0, 1), "": (1, 1), "right": (2, 1),
         "bottomleft": (0, 2), "bottom": (1, 2), "bottomright": (2, 2)}

parts, pos = [], [0]


def frame(el, state, C, fill=None, fo=1.0, border=None, bo=1.0, w=1.0, cuts=None, bevel=None, sides=None, M=8):
    """9 pieces named el-state, el-state-top ... Cut corners live in the corner pieces."""
    W = 2 * C + M
    f = {"cuts": cuts or {}, "sides": {}, "accents": []}
    if border:
        f["sides"] = {"all": (w, border, bo)}
        f["border"] = w
    f["sides"].update(sides or {})
    if fill:
        f["fill"], f["fill_opacity"] = fill, fo
    cuts = {k: min(v, C - 1.7) for k, v in (cuts or {}).items()}      # bevels must stay inside the corner pieces
    f["cuts"] = cuts
    for corner, col, bw in (bevel or []):
        f["accents"].append(ps.accent_bevel(corner, min(bw, 2.4), col, 1, cuts.get(corner, 0)))
    shapes = ps.frame_shapes(f, W, W)
    e = [0, C, C + M, W]
    y = pos[0]
    for name, (c, r) in PIECE.items():
        g = f'<rect x="{e[c]}" y="{y + e[r]}" width="{e[c + 1] - e[c]}" height="{e[r + 1] - e[r]}" fill="#000" fill-opacity="0"/>'
        for poly, col, op in shapes:
            cp = ps.clip(poly, e[c], e[r], e[c + 1], e[r + 1])
            if len(cp) >= 3:
                g += f'<path d="{ps.poly_d(cp, 0, y)}" fill="{col}" fill-opacity="{op}"/>'
        parts.append(f'<g id="{el}-{state}{"-" + name if name else ""}">{g}</g>')
    pos[0] += W + 6


def icon(name, size, body):
    """Single drawing in a size x size box."""
    y = pos[0]
    parts.append(f'<g id="{name}"><rect x="200" y="{y}" width="{size}" height="{size}" fill="#000" fill-opacity="0"/>'
                 f'<g transform="translate(200 {y})">{body}</g></g>')
    pos[0] += size + 6


def stroke(d, col, w=1.4, op=1):
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{w}"/>'


def area(d, col, op=1):
    return f'<path d="{d}" fill="{col}" fill-opacity="{op}"/>'


CUT = {"tl": 5, "br": 5}
OB = [("br", O, 2)]
STATE_COL = {"normal": TL, "focused": "#ffffff", "pressed": O, "toggled": O, "disabled": DIM}


def build():
    # ---- buttons, combo boxes
    for el in ("button", "combo"):
        frame(el, "normal", 6, RAISED, 1, T, 0.5, cuts=CUT, bevel=[("br", O, 1.6)])
        frame(el, "focused", 6, "#1c3a3d", 1, TL, 1, cuts=CUT, bevel=OB)
        frame(el, "pressed", 6, "#4a3320", 1, O, 1, cuts=CUT, bevel=[("tl", O, 2), ("br", O, 2)])
        frame(el, "toggled", 6, "#1d4648", 1, T, 1, cuts=CUT, bevel=[("tl", TL, 2), ("br", O, 2)], sides={"bottom": (2, O, 1)})
    icon("button-default-indicator", 10, area("M0 10L10 0V10Z", O))
    # ---- text fields
    frame("lineedit", "normal", 5, BASE, 1, LINE, 1, cuts={"br": 4}, sides={"bottom": (1, T, 0.7)})
    frame("lineedit", "focused", 5, BASE, 1, T, 1, cuts={"br": 4}, bevel=[("br", O, 2)], sides={"bottom": (1.6, TL, 1)})
    frame("common", "normal", 3, None, 1, LINE, 1)
    frame("common", "focused", 3, None, 1, T, 0.7)
    frame("focus", "normal", 4, None, 1, O, 0.6, cuts={"tl": 3, "br": 3})
    for p, (c, r) in PIECE.items():          # the focus frame has no state in its name
        if p:
            parts.append(f'<use id="focus-{p}" href="#focus-normal-{p}"/>')
    # ---- tabs
    for el in ("tab", "floating-tab"):
        frame(el, "normal", 5, RAISED, 0.7, LINE, 1, cuts={"tl": 4})
        frame(el, "focused", 5, "#1c3a3d", 1, T, 0.8, cuts={"tl": 4})
        frame(el, "toggled", 5, "#16282c", 1, T, 0.9, cuts={"tl": 4}, bevel=[("tl", TL, 2)], sides={"top": (2, O, 1)})
    frame("tabframe", "normal", 4, WIN, 1, LINE, 1, sides={"top": (1, T, 0.6)})
    for st in STATE_COL:
        if st != "toggled":
            icon(f"tab-close-{st}", 14, stroke("M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5", {"normal": DIM, "focused": O, "pressed": O, "disabled": LINE}[st], 1.6))
    icon("tab-tear", 8, stroke("M4 0V8", T))
    # ---- lists and headers
    frame("itemview", "focused", 4, T, 0.10, T, 0.45, cuts={"tl": 3, "br": 3})
    frame("itemview", "pressed", 4, T, 0.22, T, 0.8, cuts={"tl": 3, "br": 3}, bevel=OB)
    frame("itemview", "toggled", 4, T, 0.22, T, 0.8, cuts={"tl": 3, "br": 3}, bevel=OB)
    frame("header", "normal", 3, RAISED, 1, None, sides={"bottom": (1, T, 0.6)})
    frame("header", "focused", 3, "#1c3a3d", 1, None, sides={"bottom": (1.6, TL, 1)})
    frame("header", "pressed", 3, "#4a3320", 1, None, sides={"bottom": (1.6, O, 1)})
    frame("header", "toggled", 3, "#16282c", 1, None, sides={"bottom": (1.6, O, 1)})
    icon("header-separator", 4, area("M1 0H2V4H1Z", LINE))
    # ---- menus, tooltips, bars
    frame("menu", "normal", 10, "#0c1217", 1, T, 0.85, cuts={"tl": 9, "br": 9}, bevel=[("tl", TL, 2.4), ("br", O, 2.6)])
    for el in ("menuitem", "menubaritem"):
        frame(el, "pressed", 4, T, 0.28, T, 0.9, cuts={"tl": 3, "br": 3}, bevel=OB)
        frame(el, "toggled", 4, T, 0.20, T, 0.8, cuts={"tl": 3, "br": 3}, bevel=OB)
        frame(el, "focused", 4, T, 0.20, T, 0.8, cuts={"tl": 3, "br": 3}, bevel=OB)
        frame(el, "normal", 4, None)
    icon("menuitem-separator", 16, area("M0 7.5H16V8.5H0Z", T, 0.4))
    icon("menuitem-tearoff-normal", 8, area("M0 3H8V4H0Z", T)); icon("menuitem-tearoff-focused", 8, area("M0 3H8V4H0Z", O))
    frame("tooltip", "normal", 7, "#0c1217", 1, T, 0.85, cuts={"tl": 6, "br": 6}, bevel=[("br", O, 2)])
    frame("menubar", "normal", 3, WIN, 1, None)
    frame("toolbar", "normal", 3, WIN, 1, None, sides={"bottom": (1, T, 0.45)})
    frame("dock", "normal", 2, WIN, 1, LINE, 0.7)
    frame("dock", "focused", 2, "#1c3a3d", 1, T, 0.7)
    icon("toolbar-handle", 10, area("M4 1H5.5V9H4ZM6.5 1H8V9H6.5Z", T, 0.5))
    icon("toolbar-separator", 16, area("M7.5 1H8.5V15H7.5Z", LINE))
    frame("tbar", "normal", 2, WIN)
    icon("window-normal", 20, area("M0 0H20V20H0Z", WIN))
    icon("dialog-normal", 20, area("M0 0H20V20H0Z", WIN))
    frame("titlebar", "normal", 2, "#10171c"); frame("titlebar", "focused", 2, "#13222b")
    # ---- check boxes and radios (cut corners; radios are diamonds)
    box, dia = "M4.5 1.5H14.5V11.5L11.5 14.5H1.5V4.5Z", "M8 1L15 8L8 15L1 8Z"
    for pre in ("", "menu-"):
        for st in ("normal", "focused", "pressed", "disabled", "toggled"):
            col = {"normal": T, "focused": TL, "pressed": O, "toggled": T, "disabled": DIM}[st]
            bop = 1 if st in ("focused", "pressed") else 0.75
            b, d = area(box, BASE) + stroke(box, col, 1.2, bop), area(dia, BASE) + stroke(dia, col, 1.2, bop)
            mark = DIM if st == "disabled" else O
            icon(f"{pre}checkbox-{st}", 16, b)
            icon(f"{pre}checkbox-checked-{st}", 16, b + area("M5.5 4.5H11.5V10L10 11.5H4.5V5.5Z", mark))
            icon(f"{pre}checkbox-tristate-{st}", 16, b + area("M4.5 7H11.5V9H4.5Z", mark))
            icon(f"{pre}radio-{st}", 16, d)
            icon(f"{pre}radio-checked-{st}", 16, d + area("M8 4.6L11.4 8L8 11.4L4.6 8Z", mark))
    # ---- arrows, spin buttons, tree
    ARR = {"down": "M2.5 4.5L7 9L11.5 4.5", "up": "M2.5 9L7 4.5L11.5 9", "left": "M9 2.5L4.5 7L9 11.5", "right": "M4.5 2.5L9 7L4.5 11.5"}
    for st, col in STATE_COL.items():
        for d, path in ARR.items():
            icon(f"arrow-{d}-{st}", 14, stroke(path, col, 1.8))
            icon(f"flat-arrow-{d}-{st}", 14, stroke(path, TL if st == "normal" else col, 1.8))
        icon(f"carrow-{st}", 14, stroke(ARR["down"], O if st == "normal" else col, 1.8))
        icon(f"spin-up-{st}", 14, stroke(ARR["up"], col, 1.8)); icon(f"spin-down-{st}", 14, stroke(ARR["down"], col, 1.8))
        icon(f"spin-plus-{st}", 14, stroke("M7 2V12M2 7H12", col, 1.6)); icon(f"spin-minus-{st}", 14, stroke("M2 7H12", col, 1.6))
        icon(f"spin-separator-{st}", 4, area("M1 0H2V4H1Z", LINE))
        icon(f"tree-plus-{st}", 14, stroke(ARR["right"], col, 1.6)); icon(f"tree-minus-{st}", 14, stroke(ARR["down"], O if st == "normal" else col, 1.6))
        icon(f"splitter-grip-{st}", 16, "".join(area(f"M7 {y}H9V{y + 2}H7Z", col, 0.7) for y in (3, 7, 11)))
        icon(f"grip-{st}", 10, stroke("M3 2V8M5 2V8M7 2V8", "#0c1217", 1))
        icon(f"resize-grip-{st}", 14, stroke("M13 3L3 13M13 7L7 13M13 11L11 13", O, 1.4))
        for n, d in (("close", "M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5"), ("minimize", "M3 10H11"), ("maximize", "M3 3H11V11H3Z"),
                     ("restore", "M3 5H9V11H3ZM5 3H11V9"), ("shade", "M3 4H11M4 10L7 7L10 10"), ("menu", "M3 4H11M3 7H11M3 10H11")):
            icon(f"mdi-{n}-{st}", 14, stroke(d, O if n == "close" else col, 1.4))
    # ---- scrollbar, slider, progress
    sc = {"tl": 3, "br": 3}
    frame("scrollbarslider", "normal", 4, T, 0.35, cuts=sc)
    frame("scrollbarslider", "focused", 4, T, 0.85, cuts=sc, bevel=[("br", O, 2)])
    frame("scrollbarslider", "pressed", 4, O, 0.9, cuts=sc)
    frame("scrollbarslider", "disabled", 4, DIM, 0.2, cuts=sc)
    frame("scrollbargroove", "normal", 2, BASE, 1, None)
    frame("slider", "normal", 2, "#0c1217", 1, LINE, 1)
    frame("slider", "toggled", 2, T, 0.9)
    frame("slider", "focused", 2, "#0c1217", 1, T, 0.6)
    for st, (fl, ed) in {"normal": ("#1c3a3d", TL), "focused": ("#1d5a5a", "#ffffff"), "pressed": ("#4a3320", O), "disabled": (RAISED, DIM)}.items():
        icon(f"slidercursor-{st}", 18, area("M9 2L16 9L9 16L2 9Z", fl) + stroke("M9 2L16 9L9 16L2 9Z", ed, 1.6) + area("M9 7L11 9L9 11L7 9Z", O))
    icon("slider-tick-normal", 6, area("M2.5 0H3.5V6H2.5Z", T, 0.6))
    frame("progress", "normal", 3, "#0c1217", 1, LINE, 1)
    frame("progress-pattern", "normal", 3, T, 0.85, sides={"right": (2, O, 1)})
    frame("progress-pattern", "disabled", 3, DIM, 0.4)
    icon("dial", 64, stroke("M22 4H42L60 22V42L42 60H22L4 42V22Z", T, 2, 0.8) + area("M22 4H42L60 22V42L42 60H22L4 42V22Z", RAISED))
    icon("dial-handle", 12, area("M6 0L12 6L6 12L0 6Z", O))
    icon("dial-notches", 64, stroke("M32 2V6M2 32H6M58 32H62", T, 1.4, 0.6))


CONF = f"""[%General]
author=Rey Osman
comment=Tiberius sci-fi HUD style: cut corners, teal edges, orange accents
x11drag=menubar_and_primary_toolbar
alt_mnemonic=true
left_tabs=true
attach_active_tab=false
mirror_doc_tabs=true
group_toolbar_buttons=false
toolbar_item_spacing=2
toolbar_interior_spacing=3
spread_progressbar=true
composite=true
menu_shadow_depth=0
tooltip_shadow_depth=0
splitter_width=5
scroll_width=8
scroll_arrows=false
scroll_min_extent=40
slider_width=5
slider_handle_width=18
slider_handle_length=18
check_size=16
textless_progressbar=false
progressbar_thickness=0
menubar_mouse_tracking=true
toolbutton_style=0
click_behavior=0
translucent_windows=false
blurring=false
popup_blurring=false
vertical_spin_indicators=false
spin_button_width=18
fill_rubberband=true
merge_menubar_with_toolbar=false
small_icon_size=16
large_icon_size=32
button_icon_size=16
toolbar_icon_size=22
combo_as_lineedit=false
combo_menu=true
hide_combo_checkboxes=true
combo_focus_rect=false
groupbox_top_label=true
inline_spin_indicators=true
joined_inactive_tabs=false
layout_spacing=6
layout_margin=9
scrollbar_in_view=false
transient_scrollbar=false
animate_states=true
tree_branch_line=true
submenu_overlap=2
menu_separator_height=7

[GeneralColors]
window.color={WIN}
base.color={BASE}
alt.base.color={ALT}
button.color={RAISED}
light.color=#37474f
mid.light.color=#2b363c
dark.color=#080b0e
mid.color=#10161a
highlight.color=#178f86
inactive.highlight.color=#1d5a57
tooltip.base.color=#0c1217
text.color={TEXT}
window.text.color={TEXT}
button.text.color={TEXT}
disabled.text.color={DIM}
tooltip.text.color={TEXT}
highlight.text.color=#ffffff
link.color={TL}
link.visited.color={O}
progress.indicator.text.color=#ffffff

[Hacks]
transparent_ktitle_label=true
transparent_dolphin_view=false
blur_translucent=false
transparent_menutitle=true
respect_darkness=true
normal_default_pushbutton=false
iconless_pushbutton=false
iconless_menu=false
disabled_icon_opacity=60
single_top_toolbar=true
tint_on_mouseover=0

[PanelButtonCommand]
frame=true
frame.element=button
frame.top=6
frame.bottom=6
frame.left=6
frame.right=6
interior=true
interior.element=button
indicator.size=10
indicator.element=arrow
text.normal.color={TEXT}
text.focus.color=#ffffff
text.press.color=#ffffff
text.toggle.color=#ffffff
text.shadow=0
text.margin=1
text.iconspacing=5
text.margin.top=1
text.margin.bottom=1
text.margin.left=4
text.margin.right=4
min_width=+0.3font
min_height=+0.2font
frame.expansion=0
"""


def sect(name, el=None, fr=None, base="PanelButtonCommand", **kw):
    out = [f"\n[{name}]", f"inherits={base}"]
    if el:
        out += [f"frame.element={el}", f"interior.element={el}"]
    if fr is not None:
        out += [f"frame.{s}={fr}" for s in ("top", "bottom", "left", "right")]
    out += [f"{k.replace('__', '.')}={v}" for k, v in kw.items()]
    return "\n".join(out) + "\n"


def config():
    c = CONF
    c += sect("PanelButtonTool", "button", 5, text__margin__left=2, text__margin__right=2)
    c += sect("Dock", "dock", 2) + sect("DockTitle", frame="false", interior="false", text__bold="true", text__normal__color=TL)
    c += sect("IndicatorSpinBox", "lineedit", 5, indicator__element="spin", indicator__size=10, min_height="+0.2font")
    c += sect("RadioButton", frame="false", interior__element="radio") + sect("CheckBox", frame="false", interior__element="checkbox")
    c += sect("Focus", "focus", 4, interior="false")
    c += sect("GenericFrame", "common", 3, interior="false")
    c += sect("LineEdit", "lineedit", 5, text__margin__top=1, text__margin__bottom=1, text__margin__left=3, text__margin__right=3)
    c += sect("DropDownButton", indicator__element="arrow-down")
    c += "\n[IndicatorArrow]\nindicator.element=arrow\nindicator.size=10\n"
    c += sect("ToolboxTab", text__normal__color=TEXT)
    c += sect("Tab", "tab", 5, indicator__element="tab", indicator__size=14, text__margin__left=8, text__margin__right=8,
              text__margin__top=1, text__margin__bottom=1, text__normal__color="#9aa6ad", text__toggle__color="#ffffff")
    c += sect("TabFrame", "tabframe", 4) + sect("TabBarFrame", base="GenericFrame", frame="false", interior="false")
    c += sect("TreeExpander", indicator__element="tree", indicator__size=12)
    c += sect("HeaderSection", "header", 3, text__bold="true", text__normal__color=TL, text__margin__left=4, text__margin__right=4)
    c += "\n[SizeGrip]\nindicator.element=resize-grip\n"
    c += sect("Toolbar", "toolbar", 0, indicator__element="toolbar", indicator__size=5, text__margin=0, frame="true", frame__bottom=3)
    c += sect("Slider", "slider", 2) + sect("SliderCursor", frame="false", interior__element="slidercursor")
    c += sect("Progressbar", "progress", 3, text__margin=0, text__bold="true") + sect("ProgressbarContents", "progress-pattern", 3)
    c += sect("ItemView", "itemview", 4, text__margin=0, text__margin__top=1, text__margin__bottom=1, text__margin__left=3, text__margin__right=3,
              min_width="0", min_height="0")
    c += "\n[Splitter]\nindicator.size=16\n"
    c += sect("Scrollbar", indicator__element="arrow", indicator__size=8)
    c += sect("ScrollbarSlider", "scrollbarslider", 4, indicator__element="grip", indicator__size=0)
    c += sect("ScrollbarGroove", "scrollbargroove", 0, frame="false", interior="true")
    c += sect("MenuItem", "menuitem", 4, indicator__element="menuitem", text__margin__top=1, text__margin__bottom=1,
              text__margin__left=6, text__margin__right=6)
    c += sect("MenuBar", "menubar", 0, frame="false")
    c += sect("MenuBarItem", "menubaritem", 4, text__margin__left=4, text__margin__right=4, text__margin__top=0, text__margin__bottom=0)
    c += sect("TitleBar", frame="false", interior__element="titlebar", indicator__element="mdi", indicator__size=14, text__bold="true")
    c += sect("ComboBox", "combo", 6, indicator__element="carrow")
    c += sect("Menu", "menu", 10)
    c += sect("GroupBox", base="GenericFrame", frame="true", text__bold="true", text__normal__color=TL, text__margin=0)
    c += sect("ToolTip", "tooltip", 7, base="GenericFrame", interior="true", text__margin=0)
    c += sect("StatusBar", base="GenericFrame", frame="false", interior="false")
    c += sect("Window", interior="true", interior__element="window", frame="false")
    c += sect("Dialog", interior="true", interior__element="dialog", frame="false")
    return c


def main(dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    build()
    name = os.path.basename(dst.rstrip("/"))
    with open(os.path.join(dst, name + ".svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="{pos[0]}" viewBox="0 0 300 {pos[0]}">\n' + "\n".join(parts) + "\n</svg>\n")
    with open(os.path.join(dst, name + ".kvconfig"), "w") as f:
        f.write(config())
    print(len(parts), "pieces ->", dst)


if __name__ == "__main__":
    main(os.path.expanduser(sys.argv[1]))
