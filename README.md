# Tiberius

I've been a Linux user for quite a while and have always been a KDE fan. I wanted my desktop to feel
like the bridge of a starship, and Tiberius is the result: a sci-fi HUD theme for KDE Plasma 6 in teal and orange.

Yet another DAMN Project.

![Tiberius](media/tiberius-main.png)

There is a short [video](media/tiberius-desktop.mp4) too, to see the wallpaper moving.

## What you get

- Moving HUD wallpaper, plus a still one
- Window decoration with the cut corners
- Panel, start menu and popups to match
- Kvantum style for buttons, tabs, menus and so on
- Icons for folders, files and the system tray. Apps keep their own icons: I tried replacing them
  and couldn't tell which one was which
- Cursors
- Clock with a calendar, and a keyboard layout indicator

![Start menu](media/tiberius-1-start-menu.png)

![Windows](media/tiberius-2-windows.png)

![App style](media/app-style.png)

### Cursors

![Cursors](media/cursors.png)

## Installing

You need Plasma 6, Kvantum, Aurorae and Qt Multimedia (for the moving wallpaper).

Fedora:

    sudo dnf install kvantum aurorae qt6-qtmultimedia

Arch:

    sudo pacman -S kvantum aurorae qt6-multimedia qt6-multimedia-ffmpeg

Debian/Ubuntu:

    sudo apt install qt-style-kvantum qml6-module-qtmultimedia

Then download the repo (Code > Download ZIP), unpack it, open a terminal in the folder and run

    bash install.sh

Log out, log back in, done. The moving wallpaper is set up too: Plasma can't play video wallpapers
by itself, so the installer adds the [Smart Video Wallpaper Reborn](https://github.com/luisbocanegra/plasma-smart-video-wallpaper-reborn)
add-on and points it at the Tiberius video. The clock and menu logo take a few extra clicks,
see [INSTRUCTIONS.txt](INSTRUCTIONS.txt).

Don't like it? `bash install.sh --uninstall` puts your old settings back.

## Good to know

- So far it has only been tested on Fedora with Plasma 6.8. If it breaks on yours, open an issue and tell me what happened.
- The panel is made for a horizontal bar, 44 px or taller. Vertical panels aren't done yet.
- If windows look cut off at the bottom right, set the window border size to Very Large.
- Firefox, VSCode and a few others draw their own windows, so they won't change.

The scripts that generate everything are in [source/Tools](source/Tools).

## Licence

GPL 3 or later. The font is Oxanium (OFL 1.1), and the icon glyphs are Material Symbols by Google (Apache 2.0, modified).
The video wallpaper add-on is Smart Video Wallpaper Reborn by Luis Bocanegra (GPL 2 or later), included unchanged.

Rey Osman
