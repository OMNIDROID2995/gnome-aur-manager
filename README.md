# gnome-aur-manager

A GTK4/Adwaita-based application for GNOME that provides a graphical interface to search, install, and manage AUR packages directly from your desktop.

## Features

- Modern GTK4/Adwaita interface that integrates seamlessly with GNOME
- Search and browse AUR packages
- Install and manage AUR packages with a graphical interface
- Built specifically for the Arch Linux ecosystem

## Installation

### From AUR

This package is available on the Arch User Repository (AUR). You can install it using an AUR helper or manually:

#### Using an AUR helper (e.g., yay, paru)

```bash
yay -S gnome-aur-manager
```

or

```bash
paru -S gnome-aur-manager
```

#### Manual installation

```bash
git clone https://aur.archlinux.org/gnome-aur-manager.git
cd gnome-aur-manager
makepkg -si
```

### From source

To build from source, you'll need the following dependencies:

- GTK4
- libadwaita
- Python
- python-gobject
- meson
- ninja
- git
- base-devel

```bash
git clone https://github.com/OMNIDROID2995/gnome-aur-manager.git
cd gnome-aur-manager
meson setup build
meson compile -C build
meson install -C build
```

## Dependencies

- `gtk4` - GTK4 toolkit
- `libadwaita` - GNOME's Adwaita library
- `python` - Python runtime
- `python-gobject` - Python bindings for GObject
- `git` - Required for AUR operations
- `base-devel` - Build tools for compiling AUR packages

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the GNU General Public License v3.0 or later. See the [LICENSE](LICENSE) file for details.

## Maintainer

- OMNIDROID2995
