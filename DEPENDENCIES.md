# GNOME AUR Manager - Dependency List

## Required Dependencies (depends)

### Core System
- **python>=3.10** - Python interpreter (minimum version 3.10)
- **python-gobject** - Python bindings for GObject (PyGObject)

### GTK/GNOME Stack
- **gtk4** - GTK 4 toolkit for the UI
- **libadwaita** - GNOME Libadwaita library for modern GNOME apps

### Package Management
- **yay** - AUR helper for searching, installing, and managing AUR packages
- **pacman** - Arch Linux package manager (for checking installed packages)

### Terminal
- **gnome-console** (kgx) - GNOME Console for interactive package operations

## Optional Dependencies (optdepends)

### Additional Features
- **gnome-software-packagekit-plugin** - Enables integration with GNOME Software Center for official Arch repositories

## Development/Build Dependencies (makedepends)
- None required (pure Python application)

## Runtime Python Modules
All required Python modules are part of PyGObject:
- **gi.repository.Gtk** (from python-gobject)
- **gi.repository.Adw** (from python-gobject + libadwaita)
- **gi.repository.GLib** (from python-gobject)

## System Requirements
- Arch Linux or Arch-based distribution
- GNOME desktop environment (recommended, but works on other DEs with GTK4 support)
- Active internet connection for AUR access

## Feature-Specific Dependencies

### Language Support
No additional dependencies - all 5 languages (de, en, es, fr, it) are built-in

### Terminal Operations
- Uses system's locale settings
- Requires bash shell for script execution

### Package Operations
All operations use `yay` and `pacman` CLI tools:
- Search: `yay -Ss`
- Info: `yay -Si`
- Install: `yay -S`
- Uninstall: `yay -Rns`
- Update: `yay -Syu --aur`
- Cache cleanup: `yay -Sc`
