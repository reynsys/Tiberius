#!/usr/bin/env python3
"""Build the "Tiberius" icon theme (part of the Tiberius KDE theme).

Style: sharp-cornered Material Symbols (weight 200, "sharp" variant, Apache-2.0)
inside a cut-corner HUD plate: teal outline, orange bevel bottom-right, orange
bar top-right, tick marks bottom-left. Small sizes (16/22/24 px) get the plain
glyph without the plate so they stay readable.

Covers: every folder/place, file type, device and category name that Breeze has,
plus tray/status icons and the Start menu's power buttons.
Applications and games are never touched: they keep their own icons.
Anything not covered falls back to Breeze Dark.

Usage: make-tiberius-icons.py <material-symbols-sharp-dir> <output-theme-dir>
"""
import os
import re
import shutil
import sys

TEAL, TEAL_L, ORANGE = "#22d3c5", "#3fe0d0", "#f28c38"
BREEZE = "/usr/share/icons/breeze-dark"

# ---------- rules for Breeze names (first match wins) ----------
PLACES = [
    (r"trash.*full|full.*trash", "auto_delete"), (r"trash", "delete"),
    (r"user-home|folder-home|^home", "home"), (r"desktop", "desktop_windows"),
    (r"download", "download"), (r"document", "description"),
    (r"picture|image|photo", "photo_library"), (r"music|sound|audio", "library_music"),
    (r"video|movie", "video_library"), (r"develop|code|git|script", "code"),
    (r"game|steam", "sports_esports"), (r"database", "database"), (r"build", "build"),
    (r"cloud|nextcloud|dropbox|onedrive|gdrive", "cloud"),
    (r"lock|encrypt|vault|private", "lock"), (r"public|share|remote|network|smb|nfs", "folder_shared"),
    (r"bookmark|favorite|important", "bookmark"), (r"recent|temp|history", "schedule"),
    (r"templat", "inventory_2"), (r"root|system|tar$", "folder_data"),
    (r"star|activit|tag", "folder_special"), (r"open|drag-accept", "folder_open"),
    (r"", "folder"),
]
MIMES = [
    (r"inode-directory|inode-folder", "folder"),
    (r"^image-|graphics|krita|gimp|svg", "image"), (r"^video-|vnd\.rn-real|matroska|webm", "movie"),
    (r"^audio-|x-mp3|ogg", "music_note"), (r"pdf|postscript|djvu|epub", "picture_as_pdf"),
    (r"html|xhtml", "html"),
    (r"zip|tar|compress|archive|rar|7z|bzip|gzip|xz|lzma|zstd|cpio|arj|lha|cab", "folder_zip"),
    (r"spreadsheet|calc|excel|csv|sheet", "table_chart"),
    (r"presentation|powerpoint|impress|slide", "slideshow"),
    (r"font", "font_download"), (r"iso|cd-image|disk-image|cdimage|dvd|raw-disk", "album"),
    (r"certificate|pgp|gpg|key|pkcs|x509|keystore", "key"),
    (r"executable|desktop|appimage|rpm|deb|package|flatpak|snap|msi|dosexec|sharedlib|object", "deployed_code"),
    (r"script|shell|python|perl|ruby|php|java|javascript|json|xml|yaml|toml|c\+\+|csrc|chdr|"
     r"x-c$|rust|go$|sql|makefile|cmake|qml|css|diff|patch|src|source|kotlin|lua|typescript", "code"),
    (r"document|word|writer|opendocument-text|rtf|abiword|text-x-tex", "article"),
    (r"mail|vcard|calendar|ical|contact", "mail"),
    (r"^text-|plain", "description"),
    (r"", "draft"),
]
DEVICES = [
    (r"brightness", "brightness_6"),
    (r"laptop", "laptop_windows"), (r"computer|pc|server", "computer"),
    (r"phone|pda|smartphone", "mobile_2"), (r"tablet", "tablet"),
    (r"mouse|touchpad", "mouse"), (r"keyboard", "keyboard"), (r"headphone|headset", "headphones"),
    (r"camera|webcam", "videocam"), (r"printer|print|scanner", "print"),
    (r"optical|cdrom|dvd|disc", "album"), (r"usb|removable|flash|thumb", "usb"),
    (r"sd|memory|media-flash|card", "sd_card"),
    (r"harddisk|drive|disk|nvme|ssd|storage", "hard_drive"),
    (r"microphone|audio-input", "mic"), (r"speaker|audio", "speaker"),
    (r"battery|ups", "battery_full"), (r"wireless|wifi", "wifi"),
    (r"network|wired|ethernet|modem", "lan"), (r"bluetooth", "bluetooth"), (r"tv|video-display|monitor|display", "tv"),
    (r"watch", "watch"), (r"joystick|gamepad|game", "sports_esports"), (r"", "devices"),
]

CATEGORIES = [
    (r"accessories", "construction"), (r"applications-all", "apps"), (r"development", "code"),
    (r"language", "translate"), (r"mathematics", "function"), (r"science", "science"),
    (r"education", "school"), (r"engineering", "engineering"), (r"games", "sports_esports"),
    (r"graphics", "palette"), (r"internet|network", "public"), (r"multimedia", "perm_media"),
    (r"office", "work"), (r"electronics", "memory"), (r"system", "settings_applications"), (r"utilities", "handyman"),
    (r"other", "category"), (r"", None),
]


def _wifi(n):
    if re.search(r"disconnect|offline|unavailable|disabled|deactivated", n):
        return "signal_wifi_off"
    m = re.search(r"-(\d{1,3})(?=-|$)", n)
    if not m:
        return "wifi"
    v = int(m.group(1))
    return ("signal_wifi_0_bar" if v < 20 else "network_wifi_1_bar" if v < 40 else
            "network_wifi_2_bar" if v < 60 else "network_wifi_3_bar" if v < 80 else "signal_wifi_4_bar")


def _battery(n):
    m = re.search(r"battery-(\d{3})", n)
    if "missing" in n or "error" in n:
        return "battery_error"
    if not m:
        return "battery_charging_full" if "charg" in n else ("battery_full" if "full" in n else None)
    v = int(m.group(1))
    if "charging" in n:
        for lim, g in ((20, "battery_charging_20"), (30, "battery_charging_30"), (50, "battery_charging_50"),
                       (60, "battery_charging_60"), (80, "battery_charging_80"), (90, "battery_charging_90")):
            if v <= lim:
                return g
        return "battery_charging_full"
    return "battery_full" if v >= 100 else f"battery_{min(6, v * 7 // 100)}_bar"


STATUS = [
    (r"^network-wireless|wifi|hotspot", _wifi),
    (r"^network-(wired|connect)|ethernet", "lan"), (r"^network-vpn", "vpn_lock"),
    (r"^network-mobile|cellular|modem", "signal_cellular_alt"),
    (r"^network-(offline|disconnect)|^network-limited", "link_off"), (r"airplane", "flight"),
    (r"^battery|^laptop-battery", _battery),
    (r"audio-volume-muted|audio-off", "volume_off"), (r"audio-volume-high", "volume_up"),
    (r"audio-volume-(medium|low)", "volume_down"), (r"audio-volume", "volume_mute"),
    (r"microphone-sensitivity-muted|mic-off|microphone-disabled", "mic_off"), (r"microphone", "mic"),
    (r"keyboard-brightness", "keyboard"), (r"night-light|redshift", "nightlight"),
    (r"brightness-low|low-brightness", "brightness_5"), (r"brightness", "brightness_7"),
    (r"klipper|clipboard", "content_paste"),
    (r"notification.*(disabled|inactive)", "notifications_off"), (r"notification", "notifications"),
    (r"bluetooth.*(disabled|inactive|offline)", "bluetooth_disabled"),
    (r"bluetooth.*(active|online|connected)", "bluetooth_connected"), (r"bluetooth", "bluetooth"),
    (r"update", "browser_updated"),
    (r"dialog-information|state-information", "info"), (r"dialog-warning|state-warning", "warning"),
    (r"dialog-error|state-error", "error"), (r"dialog-question", "help"),
    (r"media-playback-playing", "play_arrow"), (r"media-playback-paused", "pause"),
    (r"", None),
]

# only these few action icons (Start menu tabs and power buttons) get the HUD look;
# the rest of the toolbar icons stay Breeze for now
ACTIONS = [
    (r"^system-suspend|^system-hibernate", "bedtime"), (r"^system-reboot", "restart_alt"),
    (r"^system-shutdown", "power_settings_new"), (r"^system-log-out", "logout"),
    (r"^system-lock-screen", "lock"), (r"^system-switch-user", "switch_account"),
    (r"^bookmarks$|^bookmarks-symbolic|^favorite", "star"), (r"^help-about|^help-contents", "help"),
    (r"^compass", "explore"), (r"", None),
]

# folders keep a folder outline; the place's own glyph becomes a small emblem
FOLDERISH = r"^folder|^user-(home|desktop)|^stock_folder|^desktop$|^favorites$|^library-music"
OWN_FOLDER_GLYPHS = {"folder", "folder_open", "folder_zip", "folder_shared", "folder_special", "folder_data"}


def glyph_paths(gdir, name):
    with open(os.path.join(gdir, name + ".svg"), encoding="utf-8") as f:
        return re.findall(r'<path d="([^"]+)"', f.read())


def glyph(paths, x, y, size, colour):
    k = size / 960
    ds = "".join(f'<path d="{d}"/>' for d in paths)
    return f'<g transform="translate({x} {y + size}) scale({k})" fill="{colour}">{ds}</g>'


def plate_icon(paths):
    plate = "M14 3H61V48L48 61H3V16Z"
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            f'<path d="{plate}" fill="{TEAL}" fill-opacity="0.08" stroke="{TEAL}" stroke-width="1.6" stroke-linejoin="miter"/>'
            f'<path d="M61 48L48 61" stroke="{ORANGE}" stroke-width="3.2"/>'
            f'<path d="M3 16L14 3" stroke="{TEAL_L}" stroke-width="3.2"/>'
            f'<path d="M40 7H56" stroke="{ORANGE}" stroke-width="1.6"/>'
            f'<path d="M8 57H12M15 57H19M22 57H26" stroke="{TEAL}" stroke-width="1.6" stroke-opacity="0.7"/>'
            + glyph(paths, 11, 11, 42, TEAL_L) + "</svg>")


FOLDER_DOT = f'<rect x="3" y="3" width="3.4" height="3.4" fill="{ORANGE}"/>'   # marks folders (top-left, outside the cut)


def folder_icon(folder, badge):
    # big folder outline in the plate, the place glyph as an orange emblem inside it
    body = plate_icon(folder).replace("</svg>", "")
    return body + glyph(badge, 24, 27, 16, ORANGE) + FOLDER_DOT + "</svg>"


def small_icon(paths, px):
    # plain glyph + Tiberius accents: orange ticks on all four corners
    a, lo, hi = px / 8 * 1.6, 0.5, px - 0.5
    b = px - a
    ticks = f"M{lo} {a}V{lo}H{a}M{b} {lo}H{hi}V{a}M{hi} {b}V{hi}H{b}M{a} {hi}H{lo}V{b}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {px} {px}">'
            + glyph(paths, 0, 0, px, TEAL_L)
            + f'<path d="{ticks}" fill="none" stroke="{ORANGE}" stroke-width="1"/></svg>')


def breeze_names(context, symbolic=False):
    names = set()
    for root, _, files in os.walk(os.path.join(BREEZE, context)):
        for f in files:
            if f.endswith(".svg") and (symbolic or "-symbolic" not in f):
                names.add(f[:-4])
    return names


def pick(name, rules):
    for pat, g in rules:
        if re.search(pat, name):
            return g(name) if callable(g) else g
    return None


def main(gdir, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    # Applications keep their own icons, so each one is recognisable at a glance.
    # The apps folder only holds the Start-button logo.
    table = {"apps": {}}
    # start-here* are app/launcher logos, not folders
    table["places"] = {n: pick(n, PLACES) for n in breeze_names("places") if not n.startswith("start-here")}
    table["places"].update({n: pick(n, PLACES) for n in ("folder", "user-home", "user-desktop",
                                                          "user-trash", "user-trash-full", "folder-open")})
    table["mimetypes"] = {n: pick(n, MIMES) for n in breeze_names("mimetypes")}
    table["devices"] = {n: pick(n, DEVICES) for n in breeze_names("devices")}
    table["categories"] = {n: pick(n, CATEGORIES) for n in breeze_names("categories", True)}
    table["status"] = {n: pick(n, STATUS) for n in breeze_names("status", True)}
    table["actions"] = {n: pick(n, ACTIONS) for n in breeze_names("actions", True)}
    table["categories"]["applications-electronics"] = "memory"
    for c in ("preferences", "actions", "devices"):
        table["status"].update({n: pick(n, STATUS) for n in breeze_names(c, True)
                                if re.search(r"brightness|night-light|redshift", n)})
    # panel applets often ask for "<name>-symbolic" even where Breeze has no such file
    for n in list(table["status"]):
        if not n.endswith("-symbolic"):
            table["status"].setdefault(n + "-symbolic", table["status"][n])

    cache, written = {}, 0
    small_sizes = (16, 22, 24)
    dirs = []
    for ctx, mapping in table.items():
        for size in small_sizes:
            dirs.append((f"{size}/{ctx}", ctx, size))
        dirs.append((f"scalable/{ctx}", ctx, None))
        for d, _, _ in dirs[-4:]:
            os.makedirs(os.path.join(dst, d), exist_ok=True)
        for name, g in mapping.items():
            if not g or name.startswith("steam_icon_"):
                continue
            if g not in cache:
                if not os.path.exists(os.path.join(gdir, g + ".svg")):
                    print("missing glyph", g, "for", name)
                    continue
                cache[g] = glyph_paths(gdir, g)
            p = cache[g]
            big = plate_icon(p)
            if ctx == "places" and re.search(FOLDERISH, name) and g not in OWN_FOLDER_GLYPHS:
                big = folder_icon(cache.setdefault("folder", glyph_paths(gdir, "folder")), p)
            elif (ctx == "places" and re.search(FOLDERISH, name)) or (ctx == "mimetypes" and g == "folder"):
                big = big.replace("</svg>", FOLDER_DOT + "</svg>")
            with open(os.path.join(dst, "scalable", ctx, name + ".svg"), "w") as f:
                f.write(big)
            for size in small_sizes:
                with open(os.path.join(dst, str(size), ctx, name + ".svg"), "w") as f:
                    f.write(small_icon(p, size))
            written += 1

    ctxname = {"apps": "Applications", "places": "Places", "mimetypes": "MimeTypes", "devices": "Devices",
               "categories": "Categories", "status": "Status",
               "actions": "Actions"}
    lines = ["[Icon Theme]", "Name=Tiberius",
             "Comment=Sharp HUD icons in Tiberius teal and orange (glyphs: Material Symbols Sharp, Apache-2.0)",
             "Inherits=breeze-dark,breeze,hicolor", "Example=folder", "FollowsColorScheme=false",
             "DesktopDefault=48", "PanelDefault=32",
             "Directories=" + ",".join(d for d, _, _ in dirs), ""]
    for d, ctx, size in dirs:
        lines.append(f"[{d}]")
        lines.append(f"Context={ctxname[ctx]}")
        if size:
            lines += [f"Size={size}", "Type=Fixed"]
        else:
            lines += ["Size=64", "MinSize=32", "MaxSize=512", "Type=Scalable"]
        lines.append("")
    logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Icons", "tiberius-logo.svg")
    if os.path.exists(logo):                     # Start-button logo travels with the icon theme
        shutil.copy(logo, os.path.join(dst, "scalable", "apps", "tiberius-logo.svg"))
    with open(os.path.join(dst, "index.theme"), "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {written} icons ({len(cache)} distinct glyphs) -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
