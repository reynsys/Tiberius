#!/bin/bash
# TIBERIUS theme installer for KDE Plasma 6. Installs for your user only: no password needed.
#   ./install.sh             install and switch the theme on
#   ./install.sh --uninstall switch back to your old settings and remove the theme
cd "$(dirname "$(readlink -f "$0")")" || exit 1
[ "$(id -u)" = 0 ] && { echo "Please run this as your normal user, not as root."; exit 1; }
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"; CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
BACKUP="$DATA/tiberius-backup"
FILES="kdeglobals kwinrc kcminputrc plasmarc ksplashrc klaunchrc"
QDBUS=$(command -v qdbus-qt6 || command -v qdbus6 || command -v qdbus)

reload() {
    [ -n "$QDBUS" ] && "$QDBUS" org.kde.KWin /KWin reconfigure >/dev/null 2>&1
}

if [ "$1" = "--uninstall" ]; then
    echo "Restoring your old settings..."
    plasma-apply-lookandfeel -a org.kde.breezedark.desktop >/dev/null 2>&1
    for f in $FILES; do
        if [ -f "$BACKUP/$f" ]; then cp "$BACKUP/$f" "$CONF/$f"
        elif [ -f "$BACKUP/.absent-$f" ]; then rm -f "$CONF/$f"; fi
    done
    [ -f "$BACKUP/kvantum.kvconfig" ] && cp "$BACKUP/kvantum.kvconfig" "$CONF/Kvantum/"
    [ -f "$BACKUP/.absent-kvantum.kvconfig" ] && rm -f "$CONF/Kvantum/kvantum.kvconfig"
    rm -rf "$DATA/icons/Tiberius" "$DATA/icons/Tiberius-cursors" "$HOME/.icons/Tiberius-cursors" \
        "$DATA/plasma/desktoptheme/Tiberius" "$DATA/plasma/look-and-feel/org.tiberius.desktop" \
        "$DATA/plasma/plasmoids/org.tiberius.clock" "$DATA/plasma/plasmoids/org.tiberius.keyboard" \
        "$DATA/aurorae/themes/Tiberius" "$CONF/Kvantum/Tiberius" "$DATA/color-schemes/Tiberius.colors" \
        "$DATA/wallpapers/Tiberius" "$BACKUP" "${XDG_CACHE_HOME:-$HOME/.cache}"/plasma_theme_Tiberius*.kcache
    reload
    echo "Done. Log out and back in to finish."
    exit 0
fi

command -v plasma-apply-lookandfeel >/dev/null || { echo "This needs KDE Plasma 6. Nothing was changed."; exit 1; }
VER=$(plasmashell --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
[ "${VER%%.*}" = 6 ] || { echo "This needs KDE Plasma 6 (found: ${VER:-none}). Nothing was changed."; exit 1; }

find_plugin() { find /usr/lib* /usr/local/lib* -path "*$1" -print -quit 2>/dev/null; }
KV=$(find_plugin "plugins/styles/libkvantum.so"); AU=$(find_plugin "org.kde.kdecoration3/org.kde.kwin.aurorae.v2.so")
MISSING=""
[ -z "$KV" ] && MISSING="$MISSING kvantum"
[ -z "$AU" ] && MISSING="$MISSING aurorae"
if [ -n "$MISSING" ]; then
    echo "These helper programs are not installed:$MISSING"
    echo "  Fedora:            sudo dnf install kvantum aurorae"
    echo "  Arch / CachyOS:    sudo pacman -S kvantum aurorae"
    echo "  Debian / Ubuntu:   sudo apt install qt-style-kvantum   (look for an aurorae package too)"
    read -r -p "Continue without those parts? [y/N] " a
    [ "$a" = y ] || [ "$a" = Y ] || { echo "Nothing was changed."; exit 1; }
fi

echo "1/4 Saving your current settings..."
if [ ! -d "$BACKUP" ]; then            # never overwrite the first backup
    mkdir -p "$BACKUP"
    for f in $FILES; do if [ -f "$CONF/$f" ]; then cp "$CONF/$f" "$BACKUP/$f"; else touch "$BACKUP/.absent-$f"; fi; done
    if [ -f "$CONF/Kvantum/kvantum.kvconfig" ]; then cp "$CONF/Kvantum/kvantum.kvconfig" "$BACKUP/"; else touch "$BACKUP/.absent-kvantum.kvconfig"; fi
fi

echo "2/4 Copying the theme..."
put() { mkdir -p "$2"; tar xzf "files/$1" -C "$2" || { echo "Could not unpack $1"; exit 1; }; }
put Tiberius-icons.tar.gz "$DATA/icons"
put Tiberius-cursors.tar.gz "$DATA/icons"
put Tiberius-plasma-style.tar.gz "$DATA/plasma/desktoptheme"
put Tiberius-global-theme.tar.gz "$DATA/plasma/look-and-feel"
put Tiberius-window-decoration.tar.gz "$DATA/aurorae/themes"
put Tiberius-kvantum.tar.gz "$CONF/Kvantum"
mkdir -p "$DATA/color-schemes" "$DATA/wallpapers/Tiberius" "$HOME/.icons"
cp files/Tiberius.colors "$DATA/color-schemes/"
cp files/Tiberius-wallpaper.png "$DATA/wallpapers/Tiberius/tiberius-hud.png"
cp files/Tiberius-wallpaper-video.webm "$DATA/wallpapers/Tiberius/tiberius-hud.webm"
ln -sfn "$DATA/icons/Tiberius-cursors" "$HOME/.icons/Tiberius-cursors"
for w in clock keyboard; do
    d="$DATA/plasma/plasmoids/org.tiberius.$w"; rm -rf "$d"; mkdir -p "$d"; tar xzf "files/org.tiberius.$w.tar.gz" -C "$d"
done

echo "3/4 Switching it on..."
[ -n "$KV" ] && printf '[General]\ntheme=Tiberius\n' > "$CONF/Kvantum/kvantum.kvconfig"
plasma-apply-lookandfeel -a org.tiberius.desktop >/dev/null 2>&1
plasma-apply-colorscheme Tiberius >/dev/null 2>&1
plasma-apply-desktoptheme Tiberius >/dev/null 2>&1
plasma-apply-cursortheme Tiberius-cursors >/dev/null 2>&1
kwriteconfig6 --file kdeglobals --group Icons --key Theme Tiberius
kwriteconfig6 --file klaunchrc --group FeedbackStyle --key BusyCursor --type bool false
STYLE=Breeze; [ -n "$KV" ] && STYLE=kvantum
kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle --notify "$STYLE"
if [ -n "$AU" ]; then
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae.v2
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__Tiberius
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSize VeryLarge
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSizeAuto --type bool false
else
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme Breeze
fi
reload

echo "4/4 Setting the wallpaper..."
plasma-apply-wallpaperimage "$DATA/wallpapers/Tiberius/tiberius-hud.png" >/dev/null 2>&1
echo
echo "Tiberius is installed. Now LOG OUT and back in."
echo "Then see INSTRUCTIONS.txt, step 4, for the clock, the menu logo and the moving wallpaper."
