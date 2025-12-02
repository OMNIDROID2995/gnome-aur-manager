import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import os
import sys
import argparse

# Store language argument if provided
DEBUG_LANGUAGE = None

def main():
    global DEBUG_LANGUAGE
    
    # Parse command-line arguments for language override
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
    
    # Import after setting DEBUG_LANGUAGE
    from window import MainWindow
    
    app = Adw.Application(application_id='com.github.gnome-aur-manager')
    app.connect('activate', lambda app: on_activate(app, MainWindow))
    app.run()

def on_activate(app, MainWindowClass):
    window = MainWindowClass()
    window.set_application(app)
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
    if os.path.exists(icon_path):
        icon = Gtk.Picture.new_for_filename(icon_path)
        window.set_icon_name(icon_path)
    
    window.present()

if __name__ == '__main__':
    main()