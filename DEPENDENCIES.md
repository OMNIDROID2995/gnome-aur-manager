# GNOME AUR Manager - Dependency List

## Required Dependencies (depends)

### Core System
- **python>=3.10** - Python interpreter (minimum version 3.10)
- **python-gobject** - Python bindings for GObject (PyGObject)

### GTK/GNOME Stack
- **gtk4** - GTK 4 toolkit for the UI
- **libadwaita** - GNOME Libadwaita library for modern GNOME apps
- **vte4** - VTE terminal emulator library (GTK4 version) for the embedded terminal

### Package Management
- **yay** - AUR helper for searching, installing, and managing AUR packages
- **pacman** - Arch Linux package manager (for checking installed packages)

## Optional Dependencies (optdepends)

- **gnome-console** (kgx) - Only needed for the one-click AppStream PackageKit setup in the disclaimer dialog
- **gnome-software-packagekit-plugin** - Enables integration with GNOME Software Center for official Arch repositories

## Development/Build Dependencies (makedepends)
- None required (pure Python application)

## Runtime Python Modules
All required Python modules are part of PyGObject:
- **gi.repository.Gtk** (from python-gobject)
- **gi.repository.Adw** (from python-gobject + libadwaita)
- **gi.repository.GLib** (from python-gobject)
- **gi.repository.Vte** (from vte4) - Embedded terminal widget

## System Requirements
- Arch Linux or Arch-based distribution
- GNOME desktop environment (recommended, but works on other DEs with GTK4 support)
- Active internet connection for AUR access

## Feature-Specific Dependencies

### Language Support
No additional dependencies - all 5 languages (de, en, es, fr, it) are built-in

### Embedded Terminal (v2)
- All package operations (install, uninstall, update, cache cleanup) run in an embedded VTE terminal
- Automatic mode with `--noconfirm` flags; on failure, an interactive retry dialog is offered
- Requires `vte4` (VTE 3.91 / GTK4)

### Package Operations
All operations use `yay` and `pacman` CLI tools:
- Search: `yay -Ss`
- Info: `yay -Si`
- Install: `yay -S --noconfirm --answerdiff None --answerclean None` (auto), `yay -S` (interactive retry)
- Uninstall: `yay -Rns --noconfirm` (auto), `yay -Rns` (interactive retry)
- Update: `yay -Syua --noconfirm --answerdiff None --answerclean None` (auto), `yay -Syua` (interactive retry)
- Cache cleanup: `yay -Sc --noconfirm` (auto), `yay -Sc` (interactive retry)
