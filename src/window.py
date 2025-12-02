import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import subprocess
import threading
import webbrowser
import os
import json
import time
import locale
from pathlib import Path


# Global variables
STRINGS = {}
CURRENT_LANGUAGE = None


def load_translations(language=None):
    """Load translations from language-specific .t                    'yay -Sc; echo ""; echo -e "\\033[32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\033[0m"; echo -e "\\033[32mCache geleert - Du kannst das Terminal jetzt schließen!\\033[0m"; echo -e"\\033[32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\033[0m"; echo ""'xt files."""
    global STRINGS, CURRENT_LANGUAGE
    
    if language is None:
        # First priority: Debug language override from command line
        try:
            import sys
            if hasattr(sys.modules['__main__'], 'DEBUG_LANGUAGE'):
                debug_lang = sys.modules['__main__'].DEBUG_LANGUAGE
                if debug_lang:
                    language = debug_lang
                    print(f"Debug: Using language override - {language}")
                else:
                    raise Exception("No debug language set")
            else:
                raise Exception("No debug language available")
        except:
            # Second priority: GNOME GUI language setting
            try:
                # Language detection via LANG environment variable
                lang_env = os.environ.get("LANG", "")
                if lang_env and lang_env != "":
                    language = lang_env.split('_')[0].lower()
                else:
                    raise Exception("No GUI locale set")
            except:
                # Third priority: System locale
                try:
                    locale_str = locale.getlocale()[0]
                    if locale_str:
                        language = locale_str.split('_')[0].lower()
                    else:
                        language = 'en'
                except:
                    language = 'en'
    
    supported_languages = ['de', 'en', 'es', 'fr', 'it']
    if language not in supported_languages:
        language = 'en'
    
    CURRENT_LANGUAGE = language
    
    strings_dict = {}
    try:
        strings_dir = os.path.join(os.path.dirname(__file__), 'strings')
        strings_file = os.path.join(strings_dir, f'{language}.txt')
        
        if os.path.exists(strings_file):
            with open(strings_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        strings_dict[key] = value
        else:
            if language != 'en':
                fallback_file = os.path.join(strings_dir, 'en.txt')
                if os.path.exists(fallback_file):
                    with open(fallback_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and '=' in line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                strings_dict[key] = value
    except Exception as e:
        print(f"Error loading translations: {e}")
    
    STRINGS.clear()
    STRINGS.update(strings_dict)
    return strings_dict


def _(key, **kwargs):
    """Translate string with optional parameter substitution."""
    text = STRINGS.get(key, key)
    for param, value in kwargs.items():
        text = text.replace('{' + param + '}', str(value))
    return text


def get_terminal_notification(success=True, operation='install'):
    """Generate terminal notification box with translated messages."""
    # Get current language
    lang = CURRENT_LANGUAGE or 'en'
    
    # Messages for success
    success_messages = {
        'de': 'FERTIG! Du kannst das Terminal jetzt schließen',
        'en': 'DONE! You can close the terminal now',
        'es': '¡HECHO! Puedes cerrar el terminal ahora',
        'fr': 'TERMINÉ! Vous pouvez fermer le terminal maintenant',
        'it': 'FATTO! Puoi chiudere il terminale adesso'
    }
    
    # Error messages with operation context
    error_messages = {
        'install': {
            'de': ('FEHLER! Installation fehlgeschlagen', 'Bitte den Output oben überprüfen'),
            'en': ('ERROR! Installation failed', 'Please check the output above'),
            'es': ('¡ERROR! La instalación falló', 'Por favor verifica el resultado anterior'),
            'fr': ("ERREUR! L'installation a échoué", 'Veuillez vérifier le résultat ci-dessus'),
            'it': ("ERRORE! L'installazione è fallita", 'Verifica il risultato sopra')
        },
        'uninstall': {
            'de': ('FEHLER! Deinstallation fehlgeschlagen', 'Bitte den Output oben überprüfen'),
            'en': ('ERROR! Uninstallation failed', 'Please check the output above'),
            'es': ('¡ERROR! La desinstalación falló', 'Por favor verifica el resultado anterior'),
            'fr': ('ERREUR! La désinstallation a échoué', 'Veuillez vérifier le résultat ci-dessus'),
            'it': ('ERRORE! La disinstallazione è fallita', 'Verifica il risultato sopra')
        },
        'update': {
            'de': ('FEHLER! Update fehlgeschlagen', 'Bitte den Output oben überprüfen'),
            'en': ('ERROR! Update failed', 'Please check the output above'),
            'es': ('¡ERROR! La actualización falló', 'Por favor verifica el resultado anterior'),
            'fr': ('ERREUR! La mise à jour a échoué', 'Veuillez vérifier le résultat ci-dessus'),
            'it': ("ERRORE! L'aggiornamento è fallito", 'Verifica il risultato sopra')
        },
        'cleanup': {
            'de': ('FEHLER! Cache-Bereinigung fehlgeschlagen', 'Bitte den Output oben überprüfen'),
            'en': ('ERROR! Cache cleanup failed', 'Please check the output above'),
            'es': ('¡ERROR! La limpieza de caché falló', 'Por favor verifica el resultado anterior'),
            'fr': ('ERREUR! Le nettoyage du cache a échoué', 'Veuillez vérifier le résultat ci-dessus'),
            'it': ('ERRORE! La pulizia della cache è fallita', 'Verifica il risultato sopra')
        }
    }
    
    color = '32' if success else '31'  # Green for success, red for error
    
    if success:
        message = success_messages.get(lang, success_messages['en'])
        return f'''
echo ""
echo ""
echo -e "\\033[1;{color}m╔════════════════════════════════════════════════════════╗\\033[0m"
echo -e "\\033[1;{color}m║                                                        ║\\033[0m"
echo -e "\\033[1;{color}m║  {message:^52}  ║\\033[0m"
echo -e "\\033[1;{color}m║                                                        ║\\033[0m"
echo -e "\\033[1;{color}m╚════════════════════════════════════════════════════════╝\\033[0m"
echo ""
'''
    else:
        error_data = error_messages.get(operation, error_messages['install'])
        line1, line2 = error_data.get(lang, error_data['en'])
        return f'''
echo ""
echo ""
echo -e "\\033[1;{color}m╔════════════════════════════════════════════════════════╗\\033[0m"
echo -e "\\033[1;{color}m║                                                        ║\\033[0m"
echo -e "\\033[1;{color}m║  {line1:^52}  ║\\033[0m"
echo -e "\\033[1;{color}m║  {line2:^52}  ║\\033[0m"
echo -e "\\033[1;{color}m║                                                        ║\\033[0m"
echo -e "\\033[1;{color}m╚════════════════════════════════════════════════════════╝\\033[0m"
echo ""
'''


class DisclaimerDialog(Gtk.Dialog):
    def __init__(self, parent, accent_hex):
        super().__init__(transient_for=parent, modal=True)
        
        lang = CURRENT_LANGUAGE or 'en'
        
        title_map = {
            'de': 'Warnung',
            'en': 'Warning',
            'es': 'Advertencia',
            'fr': 'Avertissement',
            'it': 'Avvertenza'
        }
        self.set_title(title_map.get(lang, 'Warning'))
        self.set_default_size(1000, 650)
        self.accent_hex = accent_hex
        self.dialog_accepted = False
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        
        title = Gtk.Label(label=STRINGS.get('STRING_DISCLAIMER_TITLE', '⚠️ ACHTUNG'))
        title.add_css_class("title-2")
        content.append(title)
        
        disclaimer_text = "Please accept the disclaimer to continue."
        try:
            disclaimer_file = os.path.join(os.path.dirname(__file__), f'disclaimer-{lang}.txt')
            if not os.path.exists(disclaimer_file):
                disclaimer_file = os.path.join(os.path.dirname(__file__), 'disclaimer-en.txt')
            
            if os.path.exists(disclaimer_file):
                with open(disclaimer_file, 'r', encoding='utf-8') as f:
                    disclaimer_text = f.read().strip()
        except:
            pass
        
        desc = Gtk.Label(label=disclaimer_text)
        desc.set_wrap(True)
        desc.set_wrap_mode(Gtk.WrapMode.WORD)
        desc.set_halign(Gtk.Align.START)
        desc.set_justify(Gtk.Justification.LEFT)
        desc.set_hexpand(True)
        content.append(desc)
        
        self.connect("close-request", self.on_dialog_close_request)
        
        switch_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label1 = Gtk.Label(label=STRINGS.get('STRING_UNDERSTAND', 'I understand'))
        label1.set_halign(Gtk.Align.START)
        label1.set_hexpand(True)
        self.switch1 = Gtk.Switch()
        switch_box1.append(label1)
        switch_box1.append(self.switch1)
        
        box1_button = Gtk.Button()
        box1_button.set_child(switch_box1)
        box1_button.add_css_class("flat")
        box1_button.set_hexpand(True)
        box1_button.connect("clicked", lambda b: self.switch1.set_active(not self.switch1.get_active()))
        
        switch_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label2 = Gtk.Label(label=STRINGS.get('STRING_DONT_SHOW_AGAIN', 'Do not show this message again'))
        label2.set_halign(Gtk.Align.START)
        label2.set_hexpand(True)
        self.switch2 = Gtk.Switch()
        switch_box2.append(label2)
        switch_box2.append(self.switch2)
        
        box2_button = Gtk.Button()
        box2_button.set_child(switch_box2)
        box2_button.add_css_class("flat")
        box2_button.set_hexpand(True)
        box2_button.connect("clicked", lambda b: self.switch2.set_active(not self.switch2.get_active()))
        
        switches_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        switches_box.append(box1_button)
        switches_box.append(box2_button)
        
        content.append(switches_box)
        vbox.append(content)
        
        self.accept_button = self.add_button(STRINGS.get('STRING_ACCEPT_BUTTON', 'Akzeptieren'), Gtk.ResponseType.OK)
        self.accept_button.set_margin_top(12)
        self.accept_button.set_margin_bottom(12)
        self.accept_button.set_margin_start(12)
        self.accept_button.set_margin_end(12)
        self.accept_button.add_css_class("accent-colored")
        
        self.setup_dialog_css()
        
        content_area = self.get_content_area()
        content_area.append(vbox)
        self.connect("response", self.on_response)
    
    def setup_dialog_css(self):
        """Setup CSS for switches and button with accent color"""
        css_provider = Gtk.CssProvider()
        css_data = f"""
        switch {{
            background-color: #888;
            border-radius: 10px;
            margin: 6px;
        }}
        
        switch:checked {{
            background-color: {self.accent_hex};
        }}
        
        switch slider {{
            background-color: white;
            border-radius: 50%;
            margin: 2px;
        }}
        
        .accent-colored {{
            background: {self.accent_hex};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
        }}
        
        .accent-colored:hover {{
            background: {self.lighten_color(self.accent_hex)};
        }}
        """
        css_provider.load_from_data(css_data)
        for switch in [self.switch1, self.switch2]:
            switch.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        if hasattr(self, 'accept_button'):
            self.accept_button.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    @staticmethod
    def lighten_color(hex_color):
        """Lighten a hex color by 15%"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lighter = tuple(int(min(255, c * 1.15)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*lighter)
    
    def on_dialog_close_request(self, dialog):
        """Exit app if dialog is closed with X button without accepting"""
        if not self.dialog_accepted:
            import sys
            sys.exit(0)
        return False
    
    def on_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            if self.switch1.get_active():
                self.dialog_accepted = True
                if self.switch2.get_active():
                    self.save_preference()
                self.close()
            else:
                error_dialog = Gtk.AlertDialog()
                error_dialog.set_message(STRINGS.get('STRING_CONFIRM_UNDERSTAND', 'Bitte bestätigen Sie, dass Sie verstanden haben'))
                error_dialog.show(self)
    
    def save_preference(self):
        config_dir = os.path.expanduser("~/.config/gnome-aur-manager")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "disclaimer.json")
        with open(config_file, 'w') as f:
            json.dump({"show_disclaimer": False}, f)
    
    @staticmethod
    def should_show():
        config_file = os.path.expanduser("~/.config/gnome-aur-manager/disclaimer.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get("show_disclaimer", True)
            except:
                return True
        return True


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, force_dialog=False):
        super().__init__()
        
        self.force_dialog = force_dialog
        load_translations()
        
        self.set_title(STRINGS.get('STRING_APP_TITLE', 'GNOME Arch User Repository Manager'))
        self.set_default_size(1000, 700)
        
        header_bar = Adw.HeaderBar()
        self.set_titlebar(header_bar)

        self.accent_hex = self.get_accent_color_hex()
        self.setup_base_css()
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(0)
        main_box.set_margin_bottom(15)
        main_box.set_margin_start(15)
        main_box.set_margin_end(15)

        header = self.create_header()
        main_box.append(header)

        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text(STRINGS.get('STRING_SEARCH_PLACEHOLDER', 'Suchbegriff eingeben...'))
        self.search_entry.set_size_request(300, -1)
        self.search_entry.connect("activate", self.on_search)

        search_button = Gtk.Button(label=STRINGS.get('STRING_SEARCH_BUTTON', 'Suchen'))
        search_button.set_name("search-button")
        search_button.add_css_class("suggested-action")
        search_button.connect("clicked", self.on_search)
        self.style_accent_button(search_button)

        search_box.append(self.search_entry)
        search_box.append(search_button)
        search_box.set_halign(Gtk.Align.START)
        search_box.set_hexpand(True)

        # Buttons für Cache/Update rechtsbündig
        top_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_buttons_box.set_halign(Gtk.Align.END)
        
        self.cleanup_button = Gtk.Button(label=STRINGS.get('STRING_CLEAN_CACHE', 'Cache leeren'))
        self.cleanup_button.set_name("cleanup-button")
        self.cleanup_button.add_css_class("suggested-action")
        self.cleanup_button.connect("clicked", self.on_cleanup_clicked)
        self.style_accent_button(self.cleanup_button)
        
        self.update_button = Gtk.Button(label=STRINGS.get('STRING_UPDATE_BUTTON', 'Installierte AUR Pakete aktualisieren'))
        self.update_button.set_name("update-button")
        self.update_button.add_css_class("suggested-action")
        self.update_button.connect("clicked", self.on_update_aur_clicked)
        self.style_accent_button(self.update_button)
        
        top_buttons_box.append(self.cleanup_button)
        top_buttons_box.append(self.update_button)
        
        # Kombiniere Suchbox und Top-Buttons in einer Zeile
        search_and_buttons_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_and_buttons_row.append(search_box)
        search_and_buttons_row.append(top_buttons_box)
        
        main_box.append(search_and_buttons_row)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)
        paned.set_hexpand(True)

        scrolled_results = Gtk.ScrolledWindow()
        scrolled_results.set_vexpand(True)
        scrolled_results.set_hexpand(True)
        scrolled_results.add_css_class("card")

        self.results_list = Gtk.ListBox()
        self.results_list.add_css_class("navigation-sidebar")
        self.results_list.connect("row-selected", self.on_package_selected)
        scrolled_results.set_child(self.results_list)

        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        details_box.add_css_class("card")

        details_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        details_header_box.set_halign(Gtk.Align.FILL)
        details_header_box.set_margin_top(12)
        details_header_box.set_margin_start(12)
        details_header_box.set_margin_end(12)
        
        details_header = Gtk.Label(label=STRINGS.get('STRING_DETAILS_HEADER', 'Paketdetails'))
        details_header.add_css_class("title-2")
        details_header.set_halign(Gtk.Align.START)
        details_header.set_hexpand(True)
        
        details_header_box.append(details_header)

        scrolled_details = Gtk.ScrolledWindow()
        scrolled_details.set_vexpand(True)
        scrolled_details.set_hexpand(True)

        self.details_grid = Gtk.Grid()
        self.details_grid.set_column_spacing(10)
        self.details_grid.set_row_spacing(8)
        self.details_grid.set_margin_top(10)
        self.details_grid.set_margin_bottom(10)
        self.details_grid.set_margin_start(10)
        self.details_grid.set_margin_end(10)
        
        scrolled_details.set_child(self.details_grid)
        
        self.details_label = Gtk.Label(label=STRINGS.get('STRING_SELECT_PACKAGE', 'Wählen Sie ein Paket aus der Liste'))
        self.details_label.set_wrap(True)
        self.details_label.set_halign(Gtk.Align.START)
        self.details_label.set_valign(Gtk.Align.START)
        self.details_grid.attach(self.details_label, 0, 0, 2, 1)

        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        action_box.set_margin_top(12)
        action_box.set_margin_bottom(12)
        action_box.set_margin_start(12)
        action_box.set_margin_end(12)

        self.status_button = Gtk.Label(label="")
        self.status_button.set_wrap(True)
        self.status_button.set_halign(Gtk.Align.START)

        button_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_row.set_margin_top(12)
        button_row.set_margin_start(12)
        button_row.set_margin_end(12)

        self.install_button = Gtk.Button(label=STRINGS.get('STRING_INSTALL_BUTTON', 'Installieren'))
        self.install_button.set_name("install-button")
        self.install_button.add_css_class("suggested-action")
        self.install_button.connect("clicked", self.on_install_clicked)
        self.install_button.set_sensitive(False)
        self.style_accent_button(self.install_button)

        self.uninstall_button = Gtk.Button(label=STRINGS.get('STRING_UNINSTALL_BUTTON', 'Deinstallieren'))
        self.uninstall_button.set_name("uninstall-button")
        self.uninstall_button.add_css_class("destructive-action")
        self.uninstall_button.connect("clicked", self.on_uninstall_clicked)
        self.uninstall_button.set_sensitive(False)
        self.style_destructive_button(self.uninstall_button)

        self.aur_button = Gtk.Button(label=STRINGS.get('STRING_OPEN_IN_BROWSER', 'Im Browser öffnen'))
        self.aur_button.set_name("aur-button")
        self.aur_button.connect("clicked", self.on_aur_clicked)
        self.aur_button.set_sensitive(False)
        self.style_accent_button(self.aur_button)

        button_row.append(self.install_button)
        button_row.append(self.uninstall_button)
        button_row.append(self.aur_button)
        button_row.set_halign(Gtk.Align.START)

        action_box.append(self.status_button)
        action_box.append(button_row)

        details_box.append(details_header_box)
        details_box.append(scrolled_details)
        details_box.append(action_box)

        paned.set_start_child(scrolled_results)
        paned.set_resize_start_child(False)
        paned.set_end_child(details_box)
        paned.set_position(320)

        main_box.append(paned)

        self.status_label = Gtk.Label(label=STRINGS.get('STRING_READY_STATUS', 'Bereit zur Suche'))
        self.status_label.set_wrap(True)
        self.status_label.add_css_class("dim-label")
        main_box.append(self.status_label)

        self.set_child(main_box)
        self.selected_package = None
        self.selected_package_full = None
        
        if DisclaimerDialog.should_show():
            GLib.idle_add(self.show_disclaimer_dialog)

    def show_disclaimer_dialog(self):
        """Show the disclaimer dialog"""
        dialog = DisclaimerDialog(self, self.accent_hex)
        dialog.show()
        return False

    def get_accent_color_hex(self):
        """Get GNOME accent color as hex"""
        try:
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            accent_name = settings.get_string("accent-color")
            
            accent_colors = {
                "blue": "#1f71c6",
                "red": "#d62828",
                "green": "#26a269",
                "yellow": "#f5c211",
                "orange": "#ff8c00",
                "purple": "#9b59b6",
                "pink": "#d74590",
                "cyan": "#0099cc",
                "teal": "#17a697",
                "gray": "#7a8793",
                "slate": "#7a8793",
            }
            return accent_colors.get(accent_name, "#1f71c6")
        except:
            return "#1f71c6"
    
    def lighten_color(self, hex_color):
        """Lighten a color by 15%"""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r * 1.15))
        g = min(255, int(g * 1.15))
        b = min(255, int(b * 1.15))
        return f"#{r:02x}{g:02x}{b:02x}"

    def setup_base_css(self):
        """Setup CSS for cards and elements"""
        css_provider = Gtk.CssProvider()
        css_data = f"""
        * {{
            font-family: system-ui;
        }}

        headerbar {{
            background: transparent;
            box-shadow: none;
            border: none;
        }}

        .card {{
            border: 1px solid @borders;
            border-radius: 12px;
            background-color: @theme_base_color;
        }}

        .title-2 {{
            font-size: 16pt;
            font-weight: bold;
        }}

        button {{
            border-radius: 8px;
            transition: all 150ms ease-in-out;
        }}

        button:hover {{
            transition: all 150ms ease-in-out;
        }}

        .accent-colored {{
            background: {self.accent_hex};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
        }}

        .accent-colored:hover {{
            background: {self.lighten_color(self.accent_hex)};
        }}

        .destructive-styled {{
            background: #c01c28;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
        }}

        .destructive-styled:hover {{
            background: #e01b24;
        }}

        .destructive-styled:focus {{
            outline: none;
        }}

        .flat {{
            background-color: rgba(0, 0, 0, 0.05);
            border-radius: 8px;
        }}

        .flat:hover {{
            background-color: rgba(0, 0, 0, 0.1);
        }}

        listbox row {{
            padding: 8px;
        }}

        listbox row:selected {{
            background-color: @theme_selected_bg_color;
        }}

        scrolledwindow {{
            border-radius: 12px;
            border: none;
            background: transparent;
        }}

        listbox {{
            border: none;
            background: transparent;
        }}

        entry {{
            border-radius: 6px;
        }}

        paned {{
            background: transparent;
            border: none;
            box-shadow: none;
        }}

        paned separator {{
            background: transparent;
            border: none;
            margin: 0;
            padding: 0;
            box-shadow: none;
            min-width: 0px;
            min-height: 0px;
        }}
        """
        css_provider.load_from_data(css_data)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def style_accent_button(self, button):
        """Style button with accent color"""
        button.remove_css_class("suggested-action")
        button.add_css_class("accent-colored")

    def style_destructive_button(self, button):
        """Style delete button in red"""
        button.remove_css_class("destructive-action")
        button.add_css_class("destructive-styled")

    def create_header(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(12)
        header_box.set_margin_start(15)
        header_box.set_margin_end(15)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        title_box.set_halign(Gtk.Align.START)
        
        # Use icon name from system theme
        icon_image = Gtk.Image.new_from_icon_name("gnome-aur-manager")
        icon_image.set_pixel_size(48)
        title_box.append(icon_image)
        
        title = Gtk.Label(label=STRINGS.get('STRING_APP_WINDOW_TITLE', 'Package Browser'))
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        title_box.append(title)

        subtitle = Gtk.Label(label=STRINGS.get('STRING_HEADER_SUBTITLE', 'Durchsuchen und verwalten Sie AUR Pakete'))
        subtitle.add_css_class("subtitle")
        subtitle.set_halign(Gtk.Align.START)

        header_box.append(title_box)
        header_box.append(subtitle)
        return header_box

    def on_search(self, widget):
        query = self.search_entry.get_text()
        if not query.strip():
            self.status_label.set_text(STRINGS.get('STRING_ENTER_SEARCH', 'Bitte einen Suchbegriff eingeben'))
            return

        self.status_label.set_text(STRINGS.get('STRING_SEARCHING', 'Suche läuft...'))
        self.results_list.remove_all()
        self.details_label.set_text(STRINGS.get('STRING_SELECT_PACKAGE', 'Wählen Sie ein Paket aus der Liste'))

        self.install_button.set_sensitive(False)
        self.uninstall_button.set_sensitive(False)
        self.aur_button.set_sensitive(False)

        thread = threading.Thread(target=self.search_aur, args=(query,))
        thread.daemon = True
        thread.start()

    def search_aur(self, query):
        try:
            result = subprocess.run(
                ['yay', '-Ss', query],
                capture_output=True,
                text=True,
                timeout=10
            )

            packages = self.parse_yay_output(result.stdout)

            GLib.idle_add(self.display_results, packages, query)
        except subprocess.TimeoutExpired:
            GLib.idle_add(self.set_status, STRINGS.get('STRING_SEARCH_TIMEOUT', 'Suche hat zu lange gedauert'))
        except Exception as e:
            GLib.idle_add(self.set_status, f"Fehler: {str(e)}")

    def parse_yay_output(self, output):
        packages = []
        lines = output.strip().split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            if line.startswith("aur/"):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].replace("aur/", "")
                    version = parts[1] if len(parts) > 1 else ""

                    description = ""
                    if i + 1 < len(lines) and lines[i + 1].startswith("    "):
                        description = lines[i + 1].strip()
                        i += 1

                    packages.append({
                        'name': name,
                        'version': version,
                        'description': description
                    })
            elif line.startswith("    ") and not line.strip().startswith("("):
                stripped = line.strip()
                parts = stripped.split()
                
                if len(parts) >= 2:
                    potential_version = parts[1]
                    is_version = any(c.isdigit() for c in potential_version) or potential_version.startswith('r')
                    
                    if is_version:
                        name = parts[0]
                        version = potential_version
                        
                        description = ""
                        if i + 1 < len(lines) and lines[i + 1].startswith("    "):
                            next_line = lines[i + 1].strip()
                            next_parts = next_line.split()
                            if len(next_parts) > 0:
                                is_next_package = (len(next_parts) > 1 and 
                                                 any(c.isdigit() for c in next_parts[1]))
                                if not is_next_package:
                                    description = next_line
                                    i += 1
                        
                        packages.append({
                            'name': name,
                            'version': version,
                            'description': description
                        })

            i += 1

        return packages
    
    def sort_packages_by_relevance(self, packages, query):
        """Sort packages by relevance to the query"""
        query_lower = query.lower()
        
        def relevance_score(pkg):
            name_lower = pkg['name'].lower()
            
            if name_lower == query_lower:
                return (0, pkg['name'])
            
            if name_lower.startswith(query_lower):
                return (1, pkg['name'])
            
            if query_lower in name_lower:
                pos = name_lower.find(query_lower)
                return (2 + pos/1000, pkg['name'])
            
            desc_lower = pkg['description'].lower()
            if query_lower in desc_lower:
                pos = desc_lower.find(query_lower)
                return (100 + pos/1000, pkg['name'])
            
            return (1000, pkg['name'])
        
        return sorted(packages, key=relevance_score)

    def display_results(self, packages, query):
        if not packages:
            row = Gtk.ListBoxRow()
            row.set_selectable(False)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
            box.set_margin_top(40)
            box.set_margin_bottom(40)
            box.set_margin_start(20)
            box.set_margin_end(20)
            box.set_halign(Gtk.Align.CENTER)
            box.set_valign(Gtk.Align.CENTER)
            
            icon_label = Gtk.Label(label="")
            icon_label.add_css_class("title-1")
            box.append(icon_label)
            
            message = Gtk.Label(label=STRINGS.get('STRING_NO_RESULTS', 'Keine Ergebnisse gefunden'))
            message.add_css_class("title-3")
            message.set_wrap(True)
            box.append(message)
            
            detail = Gtk.Label(label=STRINGS.get('STRING_NO_RESULTS_DETAIL', 'Keine Pakete gefunden. Versuche einen anderen Suchbegriff.'))
            detail.set_wrap(True)
            detail.set_halign(Gtk.Align.CENTER)
            detail.add_css_class("dim-label")
            box.append(detail)
            
            row.set_child(box)
            self.results_list.append(row)
            self.status_label.set_text(STRINGS.get('STRING_SEARCH_COMPLETE_EMPTY', 'Suche abgeschlossen - keine Ergebnisse'))
            return

        sorted_packages = self.sort_packages_by_relevance(packages, query)

        for pkg in sorted_packages:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(10)
            box.set_margin_end(10)

            name_label = Gtk.Label()
            name_label.set_markup(f"<b>{pkg['name']}</b> ({pkg['version']})")
            name_label.set_wrap(True)
            name_label.set_halign(Gtk.Align.START)

            desc_label = Gtk.Label(label=pkg['description'])
            desc_label.set_wrap(True)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.add_css_class("dim-label")

            box.append(name_label)
            box.append(desc_label)
            row.set_child(box)
            self.results_list.append(row)

        self.status_label.set_text(_('STRING_SEARCH_RESULTS', count=len(packages)))

    def on_package_selected(self, listbox, row):
        if row is None:
            self.selected_package = None
            self.install_button.set_sensitive(False)
            self.uninstall_button.set_sensitive(False)
            self.aur_button.set_sensitive(False)
            return

        child = row.get_child()
        labels = []
        for widget in child:
            if isinstance(widget, Gtk.Label):
                labels.append(widget.get_text())

        if labels:
            name_with_version = labels[0]
            package_name = name_with_version.split(' ')[0]

            self.selected_package = package_name

            thread = threading.Thread(target=self.fetch_package_details, args=(package_name,))
            thread.daemon = True
            thread.start()

    def fetch_package_details(self, package_name):
        try:
            result = subprocess.run(
                ['yay', '-Si', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )

            details = result.stdout
            self.selected_package_full = details

            installed = self.is_package_installed(package_name.split('/')[-1])

            GLib.idle_add(self.display_package_details, details, installed, package_name)
        except Exception as e:
            GLib.idle_add(self.details_label.set_text, f"{STRINGS.get('STRING_ERROR_PREFIX', 'Fehler:')} {str(e)}")

    def is_package_installed(self, package_name):
        try:
            result = subprocess.run(
                ['pacman', '-Q', package_name],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def display_package_details(self, details, installed, package_name):
        child = self.details_grid.get_first_child()
        while child:
            self.details_grid.remove(child)
            child = self.details_grid.get_first_child()
        
        formatted_data = self._parse_package_details(details)
        
        row = 0
        for key, value in formatted_data.items():
            key_label = Gtk.Label(label=key)
            key_label.add_css_class("monospace")
            key_label.set_halign(Gtk.Align.END)
            key_label.set_markup(f"<b>{key}</b>")
            
            value_label = Gtk.Label(label=value)
            value_label.set_wrap(True)
            value_label.set_selectable(True)
            value_label.set_halign(Gtk.Align.START)
            value_label.set_hexpand(True)
            
            self.details_grid.attach(key_label, 0, row, 1, 1)
            self.details_grid.attach(value_label, 1, row, 1, 1)
            row += 1
        
        self.update_button_state(installed)
        self.aur_button.set_sensitive(True)

    def _parse_package_details(self, details):
        """Parse package details"""
        lines = details.split('\n')
        
        # yay outputs localized field names based on system language
        # We need to match both English and German field names
        field_mappings = {
            'Name': 'Name',
            'Version': STRINGS.get('STRING_DETAIL_VERSION', 'Version'),
            'Beschreibung': STRINGS.get('STRING_DETAIL_DESCRIPTION', 'Description'),
            'Description': STRINGS.get('STRING_DETAIL_DESCRIPTION', 'Description'),
            'URL': STRINGS.get('STRING_DETAIL_URL', 'URL'),
            'Lizenzen': STRINGS.get('STRING_DETAIL_LICENSES', 'Licenses'),
            'Licenses': STRINGS.get('STRING_DETAIL_LICENSES', 'Licenses'),
            'Gruppen': STRINGS.get('STRING_DETAIL_GROUPS', 'Groups'),
            'Groups': STRINGS.get('STRING_DETAIL_GROUPS', 'Groups'),
        }
        
        # Values that indicate "none/empty" in different languages
        empty_values = ['keine', 'nichts', 'none', 'nothing', 'aucun', 'aucune', 'ninguno', 'ninguna', 'nessuno', 'nessuna']
        
        formatted_data = {}
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            for yay_key, display_key in field_mappings.items():
                if line.startswith(yay_key):
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        # Skip empty/none values
                        if value.lower() not in empty_values:
                            formatted_data[display_key] = value
                    break
        
        return formatted_data

    def update_button_state(self, installed):
        """Update button states based on installation status"""
        if installed:
            self.status_button.set_text(STRINGS.get('STRING_ALREADY_INSTALLED', 'Paket ist bereits installiert'))
            self.status_button.add_css_class("success")
            self.install_button.set_sensitive(False)
            self.install_button.set_label(STRINGS.get('STRING_INSTALLED_LABEL', 'Bereits installiert'))
            self.uninstall_button.set_sensitive(True)
        else:
            self.status_button.set_text(STRINGS.get('STRING_NOT_INSTALLED', 'Paket ist nicht installiert'))
            if "success" in self.status_button.get_css_classes():
                self.status_button.remove_css_class("success")
            self.install_button.set_sensitive(True)
            self.install_button.set_label(STRINGS.get('STRING_INSTALL_BUTTON', 'Installieren'))
            self.uninstall_button.set_sensitive(False)

    def on_install_clicked(self, button):
        if not self.selected_package:
            return

        package_name = self.selected_package.split('/')[-1]
        self.install_button.set_sensitive(False)
        self.uninstall_button.set_sensitive(False)
        self.status_label.set_text(_('STRING_INSTALLING_LOADING', package=package_name))

        thread = threading.Thread(target=self.install_package, args=(package_name,))
        thread.daemon = True
        thread.start()

    def on_uninstall_clicked(self, button):
        if not self.selected_package:
            return

        package_name = self.selected_package.split('/')[-1]
        self.install_button.set_sensitive(False)
        self.uninstall_button.set_sensitive(False)
        self.status_label.set_text(_('STRING_UNINSTALLING_LOADING', package=package_name))

        thread = threading.Thread(target=self.uninstall_package, args=(package_name,))
        thread.daemon = True
        thread.start()

    def on_aur_clicked(self, button):
        if not self.selected_package:
            return

        package_name = self.selected_package.split('/')[-1]
        aur_url = f"https://aur.archlinux.org/packages/{package_name}"

        try:
            webbrowser.open(aur_url)
        except:
            self.status_label.set_text(STRINGS.get('STRING_BROWSER_ERROR', 'Fehler: Konnte Browser nicht öffnen'))

    def on_cleanup_clicked(self, button):
        """Clear yay cache and build artifacts"""
        def run_cleanup():
            try:
                GLib.idle_add(self.set_status, STRINGS.get("STRING_CLEARING_CACHE", "Leere Cache..."))
                
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    script_path = f.name
                    success_msg = get_terminal_notification(success=True, operation='cleanup')
                    error_msg = get_terminal_notification(success=False, operation='cleanup')
                    f.write(f'''#!/bin/bash
yay -Sc
CLEANUP_STATUS=$?

if [ $CLEANUP_STATUS -eq 0 ]; then{success_msg}else{error_msg}fi
''')
                
                process = subprocess.Popen([
                    'kgx', '--',
                    'bash', script_path
                ])
                
                process.wait()
                
                try:
                    os.unlink(script_path)
                except:
                    pass
                
                GLib.idle_add(self.set_status, STRINGS.get("STRING_CACHE_CLEARED", "Cache geleert"))
                    
            except Exception as e:
                GLib.idle_add(self.set_status, f"{STRINGS.get('STRING_ERROR_PREFIX', 'Fehler:')} {str(e)}")
        
        threading.Thread(target=run_cleanup, daemon=True).start()

    def on_update_aur_clicked(self, button):
        """Update all installed AUR packages"""
        def run_update():
            try:
                GLib.idle_add(self.set_status, STRINGS.get("STRING_UPDATING_AUR", "⬆Aktualisiere alle AUR Pakete..."))
                
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    script_path = f.name
                    success_msg = get_terminal_notification(success=True, operation='update')
                    error_msg = get_terminal_notification(success=False, operation='update')
                    f.write(f'''#!/bin/bash
yay -Syua
UPDATE_STATUS=$?

if [ $UPDATE_STATUS -eq 0 ]; then{success_msg}else{error_msg}fi
''')
                
                process = subprocess.Popen([
                    'kgx', '--',
                    'bash', script_path
                ])
                
                process.wait()
                
                try:
                    os.unlink(script_path)
                except:
                    pass
                
                GLib.idle_add(self.set_status, STRINGS.get("STRING_UPDATE_COMPLETE", "AUR Pakete aktualisiert"))
                    
            except Exception as e:
                GLib.idle_add(self.set_status, f"{STRINGS.get('STRING_ERROR_PREFIX', 'Fehler:')} {str(e)}")
        
        threading.Thread(target=run_update, daemon=True).start()

    def install_package(self, package_name):
        """Install package using yay in kgx terminal"""
        def run_install():
            try:
                GLib.idle_add(self.set_status, _("STRING_INSTALLING", package=package_name))
                
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    script_path = f.name
                    success_msg = get_terminal_notification(success=True, operation='install')
                    error_msg = get_terminal_notification(success=False, operation='install')
                    f.write(f'''#!/bin/bash
yay -S {package_name}
INSTALL_STATUS=$?

if [ $INSTALL_STATUS -eq 0 ]; then{success_msg}else{error_msg}fi
''')
                
                process = subprocess.Popen([
                    'kgx', '--',
                    'bash', script_path
                ])
                
                process.wait()
                
                import os
                try:
                    os.unlink(script_path)
                except:
                    pass
                
                for attempt in range(120):
                    time.sleep(1)
                    if self.is_package_installed(package_name):
                        GLib.idle_add(self.set_status, _("STRING_INSTALL_SUCCESS", package=package_name))
                        GLib.idle_add(lambda: self.update_button_state(True))
                        return
                
                installed = self.is_package_installed(package_name)
                GLib.idle_add(lambda: self.update_button_state(installed))
                if not installed:
                    GLib.idle_add(self.set_status, STRINGS.get('STRING_INSTALL_ABORTED', '⚠ Installation abgebrochen oder fehlgeschlagen'))
                    
            except Exception as e:
                GLib.idle_add(self.set_status, f"{STRINGS.get('STRING_ERROR_PREFIX', 'Fehler:')} {str(e)}")
        
        threading.Thread(target=run_install, daemon=True).start()

    def uninstall_package(self, package_name):
        """Uninstall package using yay in kgx terminal"""
        def run_uninstall():
            try:
                GLib.idle_add(self.set_status, _("STRING_UNINSTALLING", package=package_name))
                
                # Check if debug package exists and add it to removal list
                packages_to_remove = [package_name]
                debug_package = f"{package_name}-debug"
                
                if self.is_package_installed(debug_package):
                    packages_to_remove.append(debug_package)
                
                remove_list = " ".join(packages_to_remove)
                
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    script_path = f.name
                    success_msg = get_terminal_notification(success=True, operation='uninstall')
                    error_msg = get_terminal_notification(success=False, operation='uninstall')
                    f.write(f'''#!/bin/bash
yay -Rns {remove_list}
UNINSTALL_STATUS=$?

if [ $UNINSTALL_STATUS -eq 0 ]; then{success_msg}else{error_msg}fi
''')
                
                process = subprocess.Popen([
                    'kgx', '--',
                    'bash', script_path
                ])
                
                process.wait()
                
                try:
                    os.unlink(script_path)
                except:
                    pass
                
                for attempt in range(120):
                    time.sleep(1)
                    if not self.is_package_installed(package_name):
                        GLib.idle_add(self.set_status, _("STRING_UNINSTALL_SUCCESS", package=package_name))
                        GLib.idle_add(lambda: self.update_button_state(False))
                        return
                
                installed = self.is_package_installed(package_name)
                GLib.idle_add(lambda: self.update_button_state(installed))
                if installed:
                    GLib.idle_add(self.set_status, STRINGS.get('STRING_UNINSTALL_ABORTED', 'Deinstallation abgebrochen oder fehlgeschlagen'))
                    
            except Exception as e:
                GLib.idle_add(self.set_status, f"{STRINGS.get('STRING_ERROR_PREFIX', 'Fehler:')} {str(e)}")
        
        threading.Thread(target=run_uninstall, daemon=True).start()

    def set_status(self, text):
        self.status_label.set_text(text)
