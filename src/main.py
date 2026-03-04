import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
import os
import sys
import argparse

# Store language argument if provided
DEBUG_LANGUAGE = None


def main():
    global DEBUG_LANGUAGE

    parser = argparse.ArgumentParser(description='GNOME AUR Manager')
    parser.add_argument('-de', '--german', action='store_const', const='de', dest='language',
                        help='Benutze Deutsch (Debug)')
    parser.add_argument('-en', '--english', action='store_const', const='en', dest='language',
                        help='Use English (Debug)')
    parser.add_argument('-es', '--spanish', action='store_const', const='es', dest='language',
                        help='Usar Español (Debug)')
    parser.add_argument('-fr', '--french', action='store_const', const='fr', dest='language',
                        help='Utiliser Français (Debug)')
    parser.add_argument('-it', '--italian', action='store_const', const='it', dest='language',
                        help='Usa Italiano (Debug)')

    args = parser.parse_args()

    if args.language:
        DEBUG_LANGUAGE = args.language
        print(f"Debug: Language override - {DEBUG_LANGUAGE}")

    from window import MainWindow, load_translations
    load_translations()

    app = Adw.Application(application_id='org.gnome.AURManager')
    app.connect('activate', lambda app: on_activate(app, MainWindow))
    app.run()


def on_activate(app, MainWindowClass):
    # Register local icon theme path (for running from source)
    icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    local_icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
    if os.path.isdir(local_icons_dir):
        icon_theme.add_search_path(local_icons_dir)

    window = MainWindowClass()
    window.set_application(app)
    window.set_icon_name('gnome-aur-manager')
    window.present()


if __name__ == '__main__':
    main()
