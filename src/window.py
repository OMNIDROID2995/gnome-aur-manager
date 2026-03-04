import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Vte', '3.91')
from gi.repository import Gtk, Adw, GLib, Vte
import subprocess
import threading
import webbrowser
import os
import json
import locale


# --- Global translation state ---

STRINGS = {}
CURRENT_LANGUAGE = None


def load_translations(language=None):
    """Load translations from language-specific text files.
    Priority: debug override > LANG env > system locale > English fallback."""
    global STRINGS, CURRENT_LANGUAGE

    if language is None:
        # Debug language override from command line
        try:
            import sys
            language = getattr(sys.modules.get('__main__'), 'DEBUG_LANGUAGE', None)
            if language:
                print(f"Debug: Using language override - {language}")
        except:
            pass

        if not language:
            lang_env = os.environ.get("LANG", "")
            if lang_env:
                language = lang_env.split('_')[0].lower()
            else:
                try:
                    loc = locale.getlocale()[0]
                    language = loc.split('_')[0].lower() if loc else 'en'
                except:
                    language = 'en'

    if language not in ('de', 'en', 'es', 'fr', 'it'):
        language = 'en'

    CURRENT_LANGUAGE = language
    strings_dir = os.path.join(os.path.dirname(__file__), 'strings')

    candidates = [language] if language == 'en' else [language, 'en']
    for lang_code in candidates:
        path = os.path.join(strings_dir, f'{lang_code}.txt')
        if not os.path.exists(path):
            continue
        try:
            strings_dict = {}
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        strings_dict[key] = value
            STRINGS.clear()
            STRINGS.update(strings_dict)
            return strings_dict
        except Exception as e:
            print(f"Error loading translations: {e}")

    STRINGS.clear()
    return {}


def _(key, **kwargs):
    """Translate string with optional parameter substitution."""
    text = STRINGS.get(key, key)
    for param, value in kwargs.items():
        text = text.replace('{' + param + '}', str(value))
    return text


# --- Terminal notification helpers ---

def _terminal_box(lines, color_code):
    """Generate a colored ASCII notification box for the embedded terminal."""
    parts = [
        '\necho ""', 'echo ""',
        f'echo -e "\\033[1;{color_code}m╔════════════════════════════════════════════════════════╗\\033[0m"',
        f'echo -e "\\033[1;{color_code}m║                                                        ║\\033[0m"'
    ]
    for line in lines:
        parts.append(f'echo -e "\\033[1;{color_code}m║  {line:^52}  ║\\033[0m"')
    parts.extend([
        f'echo -e "\\033[1;{color_code}m║                                                        ║\\033[0m"',
        f'echo -e "\\033[1;{color_code}m╚════════════════════════════════════════════════════════╝\\033[0m"',
        'echo ""'
    ])
    return '\n'.join(parts) + '\n'


def get_terminal_notification(success=True, operation='install'):
    """Generate terminal notification with translated messages."""
    lang = CURRENT_LANGUAGE or 'en'

    if success:
        msgs = {
            'de': 'FERTIG! Du kannst das Terminal jetzt schließen',
            'en': 'DONE! You can close the terminal now',
            'es': '¡HECHO! Puedes cerrar el terminal ahora',
            'fr': 'TERMINÉ! Vous pouvez fermer le terminal maintenant',
            'it': 'FATTO! Puoi chiudere il terminale adesso'
        }
        return _terminal_box([msgs.get(lang, msgs['en'])], '32')

    # Operation names per language
    op_names = {
        'install':   {'de': 'Installation', 'en': 'Installation', 'es': 'instalación',
                      'fr': "installation", 'it': "installazione"},
        'uninstall': {'de': 'Deinstallation', 'en': 'Uninstallation', 'es': 'desinstalación',
                      'fr': 'désinstallation', 'it': 'disinstallazione'},
        'update':    {'de': 'Update', 'en': 'Update', 'es': 'actualización',
                      'fr': 'mise à jour', 'it': 'aggiornamento'},
        'cleanup':   {'de': 'Cache-Bereinigung', 'en': 'Cache cleanup', 'es': 'limpieza de caché',
                      'fr': 'nettoyage du cache', 'it': 'pulizia della cache'},
    }
    check_msgs = {
        'de': 'Bitte den Output oben überprüfen',
        'en': 'Please check the output above',
        'es': 'Por favor verifica el resultado anterior',
        'fr': 'Veuillez vérifier le résultat ci-dessus',
        'it': 'Verifica il risultato sopra'
    }

    op = op_names.get(operation, op_names['install'])
    name = op.get(lang, op['en'])

    error_lines = {
        'de': f'FEHLER! {name} fehlgeschlagen',
        'en': f'ERROR! {name} failed',
        'es': f'¡ERROR! La {name} falló',
        'fr': f"ERREUR! L'{name} a échoué",
        'it': f"ERRORE! L'{name} è fallita"
    }

    return _terminal_box([
        error_lines.get(lang, error_lines['en']),
        check_msgs.get(lang, check_msgs['en'])
    ], '31')


# --- Disclaimer Dialog ---

class DisclaimerDialog(Adw.Window):
    def __init__(self, parent):
        super().__init__(transient_for=parent, modal=True)

        lang = CURRENT_LANGUAGE or 'en'
        title_map = {
            'de': 'Warnung', 'en': 'Warning', 'es': 'Advertencia',
            'fr': 'Avertissement', 'it': 'Avvertenza'
        }
        self.set_title(title_map.get(lang, 'Warning'))
        self.set_default_size(900, -1)
        self.dialog_accepted = False

        # Adwaita ToolbarView with HeaderBar
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar())

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Warning title
        title = Gtk.Label(label=STRINGS.get('STRING_DISCLAIMER_TITLE', '⚠️ ACHTUNG'))
        title.add_css_class("title-2")
        main_box.append(title)

        # Disclaimer text
        desc = Gtk.Label(label=self._load_disclaimer_text(lang))
        desc.set_wrap(True)
        desc.set_wrap_mode(Gtk.WrapMode.WORD)
        desc.set_halign(Gtk.Align.START)
        desc.set_justify(Gtk.Justification.LEFT)
        desc.set_hexpand(True)
        main_box.append(desc)

        # Native Adwaita SwitchRows
        prefs_group = Adw.PreferencesGroup()
        self.switch_row1 = Adw.SwitchRow(title=STRINGS.get('STRING_UNDERSTAND', 'I understand'))
        prefs_group.add(self.switch_row1)
        self.switch_row2 = Adw.SwitchRow(title=STRINGS.get('STRING_DONT_SHOW_AGAIN', 'Do not show this message again'))
        prefs_group.add(self.switch_row2)
        main_box.append(prefs_group)

        # AppStream PackageKit install group
        appstream_group = Adw.PreferencesGroup()
        if self._is_appstream_installed():
            row = Adw.ActionRow(
                title=STRINGS.get('STRING_APPSTREAM_ALREADY_INSTALLED',
                                  'AppStream PackageKit is already installed ✓'))
            row.set_sensitive(False)
            appstream_group.add(row)
        else:
            self.appstream_row = Adw.ActionRow(
                title=STRINGS.get('STRING_APPSTREAM_INSTALL_BUTTON',
                                  'Install AppStream PackageKit Integration'),
                subtitle=STRINGS.get('STRING_APPSTREAM_INSTALL_SUBTITLE',
                                     'Installs adw-gtk-theme and gnome-software-packagekit-plugin-appstream-git with all dependencies'))
            self.appstream_install_btn = Gtk.Button(
                label=STRINGS.get('STRING_PACKAGEKIT_INSTALL', 'Install Now'))
            self.appstream_install_btn.add_css_class("suggested-action")
            self.appstream_install_btn.set_valign(Gtk.Align.CENTER)
            self.appstream_install_btn.connect("clicked", self.on_appstream_install_clicked)
            self.appstream_row.add_suffix(self.appstream_install_btn)
            self.appstream_row.set_activatable_widget(self.appstream_install_btn)
            appstream_group.add(self.appstream_row)
        main_box.append(appstream_group)

        # Accept button
        accept_btn = Gtk.Button(label=STRINGS.get('STRING_ACCEPT_BUTTON', 'Akzeptieren'))
        accept_btn.add_css_class("suggested-action")
        accept_btn.add_css_class("pill")
        accept_btn.set_halign(Gtk.Align.CENTER)
        accept_btn.connect("clicked", self.on_accept_clicked)
        main_box.append(accept_btn)

        toolbar_view.set_content(main_box)
        self.set_content(toolbar_view)
        self.connect("close-request", self.on_dialog_close_request)

    @staticmethod
    def _load_disclaimer_text(lang):
        """Load disclaimer text for the given language with English fallback."""
        for code in (lang, 'en'):
            path = os.path.join(os.path.dirname(__file__), f'disclaimer-{code}.txt')
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read().strip()
                except:
                    continue
        return "Please accept the disclaimer to continue."

    def on_dialog_close_request(self, dialog):
        """Exit app if dialog is closed without accepting."""
        if not self.dialog_accepted:
            import sys
            sys.exit(0)
        return False

    def on_accept_clicked(self, button):
        if self.switch_row1.get_active():
            self.dialog_accepted = True
            if self.switch_row2.get_active():
                self._save_preference()
            self.close()
        else:
            dialog = Adw.AlertDialog()
            dialog.set_heading(STRINGS.get('STRING_CONFIRM_UNDERSTAND',
                                           'Bitte bestätigen Sie, dass Sie verstanden haben'))
            dialog.add_response("ok", "OK")
            dialog.present(self)

    @staticmethod
    def _is_appstream_installed():
        """Check if gnome-software-packagekit-plugin-appstream-git is installed."""
        try:
            return subprocess.run(
                ['pacman', '-Q', 'gnome-software-packagekit-plugin-appstream-git'],
                capture_output=True, timeout=5
            ).returncode == 0
        except:
            return False

    def on_appstream_install_clicked(self, button):
        """Launch fully automatic AppStream PackageKit installation in kgx terminal."""
        self.appstream_install_btn.set_sensitive(False)
        self.appstream_install_btn.set_label(
            STRINGS.get('STRING_APPSTREAM_INSTALLING', 'Installing AppStream integration...'))
        threading.Thread(target=self._run_appstream_install, daemon=True).start()

    def _run_appstream_install(self):
        """Run the full automatic installation in kgx terminal."""
        try:
            import tempfile

            success_msg = get_terminal_notification(success=True, operation='install')
            error_msg = get_terminal_notification(success=False, operation='install')

            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                script_path = f.name
                f.write(f'''#!/bin/bash
echo ""
echo -e "\\033[1;34m══════════════════════════════════════════════════════════\\033[0m"
echo -e "\\033[1;34m  AppStream PackageKit Integration - Automatic Setup\\033[0m"
echo -e "\\033[1;34m══════════════════════════════════════════════════════════\\033[0m"
echo ""

echo -e "\\033[1;33m[1/2]\\033[0m Installing adw-gtk-theme..."
echo ""
yay -S --noconfirm --needed adw-gtk-theme
STEP1_STATUS=$?

if [ $STEP1_STATUS -ne 0 ]; then
    echo ""
    echo -e "\\033[1;31mWarning: adw-gtk-theme installation had issues (may already be installed)\\033[0m"
    echo ""
fi

echo ""
echo -e "\\033[1;33m[2/2]\\033[0m Building & installing gnome-software-packagekit-plugin-appstream-git..."
echo -e "       This may take several minutes (compiling from source)..."
echo ""
yay -S --noconfirm --needed --answerdiff None --answerclean None --removemake gnome-software-packagekit-plugin-appstream-git
STEP2_STATUS=$?

if [ $STEP2_STATUS -eq 0 ]; then{success_msg}else{error_msg}fi
''')

            process = subprocess.Popen(['kgx', '--', 'bash', script_path])
            process.wait()

            try:
                os.unlink(script_path)
            except:
                pass

            installed = self._is_appstream_installed()
            GLib.idle_add(self._on_appstream_result, installed)
        except:
            GLib.idle_add(self._on_appstream_result, False)

    def _on_appstream_result(self, success):
        """Update UI after AppStream installation attempt."""
        if success:
            self.appstream_install_btn.set_label(
                STRINGS.get('STRING_APPSTREAM_INSTALL_SUCCESS',
                           'AppStream integration successfully installed!'))
            self.appstream_row.set_subtitle("")
        else:
            self.appstream_install_btn.set_label(
                STRINGS.get('STRING_APPSTREAM_INSTALL_FAILED',
                           'Installation failed - Please try manually via terminal'))
            self.appstream_install_btn.add_css_class("destructive-action")
        self.appstream_install_btn.remove_css_class("suggested-action")
        self.appstream_install_btn.set_sensitive(False)

    @staticmethod
    def _save_preference():
        config_dir = os.path.expanduser("~/.config/gnome-aur-manager")
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "disclaimer.json"), 'w') as f:
            json.dump({"show_disclaimer": False}, f)

    @staticmethod
    def should_show():
        config_file = os.path.expanduser("~/.config/gnome-aur-manager/disclaimer.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f).get("show_disclaimer", True)
            except:
                return True
        return True


# --- Main Window ---

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self):
        super().__init__()

        self.set_title(STRINGS.get('STRING_APP_TITLE', 'GNOME Arch User Repository Manager'))
        self.set_default_size(1000, 700)

        header_bar = Adw.HeaderBar()
        self.set_titlebar(header_bar)
        self._setup_css()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(0)
        main_box.set_margin_bottom(15)
        main_box.set_margin_start(15)
        main_box.set_margin_end(15)

        main_box.append(self._create_header())

        # Search row
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text(STRINGS.get('STRING_SEARCH_PLACEHOLDER', 'Suchbegriff eingeben...'))
        self.search_entry.set_size_request(300, -1)
        self.search_entry.connect("activate", self.on_search)

        search_btn = Gtk.Button(label=STRINGS.get('STRING_SEARCH_BUTTON', 'Suchen'))
        search_btn.add_css_class("suggested-action")
        search_btn.connect("clicked", self.on_search)

        search_box.append(self.search_entry)
        search_box.append(search_btn)
        search_box.set_halign(Gtk.Align.START)
        search_box.set_hexpand(True)

        # Cache/Update buttons (right-aligned)
        top_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_buttons.set_halign(Gtk.Align.END)

        self.cleanup_button = Gtk.Button(label=STRINGS.get('STRING_CLEAN_CACHE', 'Cache leeren'))
        self.cleanup_button.add_css_class("suggested-action")
        self.cleanup_button.connect("clicked", self.on_cleanup_clicked)

        self.update_button = Gtk.Button(label=STRINGS.get('STRING_UPDATE_BUTTON', 'Installierte AUR Pakete aktualisieren'))
        self.update_button.add_css_class("suggested-action")
        self.update_button.connect("clicked", self.on_update_aur_clicked)

        top_buttons.append(self.cleanup_button)
        top_buttons.append(self.update_button)

        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_row.append(search_box)
        search_row.append(top_buttons)
        main_box.append(search_row)

        # Paned: results list | detail panel
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

        # Details header with view toggle
        details_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        details_header_box.set_halign(Gtk.Align.FILL)
        details_header_box.set_margin_top(12)
        details_header_box.set_margin_start(12)
        details_header_box.set_margin_end(12)

        details_header = Gtk.Label(label=STRINGS.get('STRING_DETAILS_HEADER', 'Paketdetails'))
        details_header.add_css_class("title-2")
        details_header.set_halign(Gtk.Align.START)
        details_header.set_hexpand(True)

        view_switcher = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        view_switcher.add_css_class("linked")

        self.details_toggle = Gtk.ToggleButton(label=STRINGS.get('STRING_DETAILS_HEADER', 'Paketdetails'))
        self.details_toggle.set_active(True)
        self.details_toggle.connect("toggled", self.on_details_toggle)

        self.terminal_toggle = Gtk.ToggleButton(label="Terminal")
        self.terminal_toggle.set_active(False)
        self.terminal_toggle.connect("toggled", self.on_terminal_toggle)

        view_switcher.append(self.details_toggle)
        view_switcher.append(self.terminal_toggle)

        details_header_box.append(details_header)
        details_header_box.append(view_switcher)

        # Stack: details view + terminal view
        self.detail_stack = Gtk.Stack()
        self.detail_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.detail_stack.set_transition_duration(200)
        self.detail_stack.set_vexpand(True)
        self.detail_stack.set_hexpand(True)

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

        self.detail_stack.add_named(scrolled_details, "details")

        # Embedded Vte terminal
        self.terminal = Vte.Terminal()
        self.terminal.set_vexpand(True)
        self.terminal.set_hexpand(True)
        self.terminal.set_scroll_on_output(True)
        self.terminal.set_scrollback_lines(10000)

        terminal_scrolled = Gtk.ScrolledWindow()
        terminal_scrolled.set_vexpand(True)
        terminal_scrolled.set_hexpand(True)
        terminal_scrolled.set_child(self.terminal)

        self.detail_stack.add_named(terminal_scrolled, "terminal")
        self.detail_stack.set_visible_child_name("details")
        self._terminal_running = False
        self._terminal_handler_id = None

        # Action buttons
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
        self.install_button.add_css_class("suggested-action")
        self.install_button.connect("clicked", self.on_install_clicked)
        self.install_button.set_sensitive(False)

        self.uninstall_button = Gtk.Button(label=STRINGS.get('STRING_UNINSTALL_BUTTON', 'Deinstallieren'))
        self.uninstall_button.add_css_class("destructive-action")
        self.uninstall_button.connect("clicked", self.on_uninstall_clicked)
        self.uninstall_button.set_sensitive(False)

        self.aur_button = Gtk.Button(label=STRINGS.get('STRING_OPEN_IN_BROWSER', 'Im Browser öffnen'))
        self.aur_button.connect("clicked", self.on_aur_clicked)
        self.aur_button.set_sensitive(False)

        button_row.append(self.install_button)
        button_row.append(self.uninstall_button)
        button_row.append(self.aur_button)
        button_row.set_halign(Gtk.Align.START)

        action_box.append(self.status_button)
        action_box.append(button_row)

        details_box.append(details_header_box)
        details_box.append(self.detail_stack)
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

        if DisclaimerDialog.should_show():
            GLib.idle_add(self._show_disclaimer)

    # --- View switching ---

    def _show_disclaimer(self):
        DisclaimerDialog(self).show()
        return False

    def on_details_toggle(self, button):
        if button.get_active():
            self.terminal_toggle.set_active(False)
            self.detail_stack.set_visible_child_name("details")
        elif not self.terminal_toggle.get_active():
            button.set_active(True)

    def on_terminal_toggle(self, button):
        if button.get_active():
            self.details_toggle.set_active(False)
            self.detail_stack.set_visible_child_name("terminal")
        elif not self.details_toggle.get_active():
            button.set_active(True)

    # --- Embedded terminal ---

    def run_in_embedded_terminal(self, command, on_complete=None):
        """Run a command in the embedded Vte terminal."""
        self._terminal_running = True
        self.terminal_toggle.set_active(True)

        # Disconnect previous handler to prevent stale callbacks
        if self._terminal_handler_id is not None:
            self.terminal.disconnect(self._terminal_handler_id)
            self._terminal_handler_id = None

        self.terminal.reset(True, True)
        shell = os.environ.get('SHELL', '/bin/bash')

        def on_child_exited(terminal, status):
            self._terminal_running = False
            exit_code = os.waitstatus_to_exitcode(status) if hasattr(os, 'waitstatus_to_exitcode') else (status >> 8)
            if on_complete:
                GLib.idle_add(on_complete, exit_code == 0)

        self._terminal_handler_id = self.terminal.connect("child-exited", on_child_exited)

        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            os.environ.get('HOME', '/'),
            [shell, '-c', command],
            None, GLib.SpawnFlags.DEFAULT,
            None, None, -1, None, None
        )

    def _build_command(self, yay_args, operation):
        """Build a shell command with success/error notification and proper exit code."""
        success_msg = get_terminal_notification(success=True, operation=operation)
        error_msg = get_terminal_notification(success=False, operation=operation)
        return f'''{yay_args}
STATUS=$?
if [ $STATUS -eq 0 ]; then{success_msg}else{error_msg}fi
exit $STATUS'''

    # --- CSS ---

    def _setup_css(self):
        """Minimal CSS — all widget styling uses native Adwaita."""
        css = Gtk.CssProvider()
        css.load_from_data("""
            paned { background: transparent; border: none; box-shadow: none; }
            paned separator { background: transparent; border: none; margin: 0;
                padding: 0; box-shadow: none; min-width: 0px; min-height: 0px; }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _create_header(self):
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        header_box.set_margin_top(12)
        header_box.set_margin_bottom(12)
        header_box.set_margin_start(15)
        header_box.set_margin_end(15)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        title_box.set_halign(Gtk.Align.START)

        icon = Gtk.Image.new_from_icon_name("gnome-aur-manager")
        icon.set_pixel_size(48)
        title_box.append(icon)

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

    # --- Search ---

    def on_search(self, widget):
        query = self.search_entry.get_text().strip()
        if not query:
            self.status_label.set_text(STRINGS.get('STRING_ENTER_SEARCH', 'Bitte einen Suchbegriff eingeben'))
            return

        self.status_label.set_text(STRINGS.get('STRING_SEARCHING', 'Suche läuft...'))
        self.results_list.remove_all()
        self.details_label.set_text(STRINGS.get('STRING_SELECT_PACKAGE', 'Wählen Sie ein Paket aus der Liste'))
        self.install_button.set_sensitive(False)
        self.uninstall_button.set_sensitive(False)
        self.aur_button.set_sensitive(False)

        threading.Thread(target=self._search_aur, args=(query,), daemon=True).start()

    def _search_aur(self, query):
        try:
            result = subprocess.run(['yay', '-Ss', query],
                                    capture_output=True, text=True, timeout=10)
            packages = self._parse_yay_output(result.stdout)
            GLib.idle_add(self._display_results, packages, query)
        except subprocess.TimeoutExpired:
            GLib.idle_add(self.set_status, STRINGS.get('STRING_SEARCH_TIMEOUT', 'Suche hat zu lange gedauert'))
        except Exception as e:
            GLib.idle_add(self.set_status, f"Fehler: {e}")

    @staticmethod
    def _parse_yay_output(output):
        """Parse yay -Ss output into package list (handles all repo prefixes)."""
        packages = []
        lines = output.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            # Match "repo/name version ..." format
            if '/' in line and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].split('/', 1)[1]
                    version = parts[1]
                    description = ""
                    if i + 1 < len(lines) and lines[i + 1].startswith("    "):
                        description = lines[i + 1].strip()
                        i += 1
                    packages.append({'name': name, 'version': version, 'description': description})
            i += 1
        return packages

    @staticmethod
    def _sort_by_relevance(packages, query):
        """Sort packages by relevance to the search query."""
        q = query.lower()

        def score(pkg):
            name = pkg['name'].lower()
            if name == q:
                return (0, pkg['name'])
            if name.startswith(q):
                return (1, pkg['name'])
            if q in name:
                return (2 + name.find(q) / 1000, pkg['name'])
            desc = pkg['description'].lower()
            if q in desc:
                return (100 + desc.find(q) / 1000, pkg['name'])
            return (1000, pkg['name'])

        return sorted(packages, key=score)

    def _display_results(self, packages, query):
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

            detail = Gtk.Label(label=STRINGS.get('STRING_NO_RESULTS_DETAIL',
                                                  'Keine Pakete gefunden. Versuche einen anderen Suchbegriff.'))
            detail.set_wrap(True)
            detail.set_halign(Gtk.Align.CENTER)
            detail.add_css_class("dim-label")
            box.append(detail)

            row.set_child(box)
            self.results_list.append(row)
            self.status_label.set_text(STRINGS.get('STRING_SEARCH_COMPLETE_EMPTY', 'Suche abgeschlossen - keine Ergebnisse'))
            return

        for pkg in self._sort_by_relevance(packages, query):
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

    # --- Package details ---

    def on_package_selected(self, listbox, row):
        if row is None:
            self.selected_package = None
            self.install_button.set_sensitive(False)
            self.uninstall_button.set_sensitive(False)
            self.aur_button.set_sensitive(False)
            return

        child = row.get_child()
        labels = [w.get_text() for w in child if isinstance(w, Gtk.Label)]
        if labels:
            self.selected_package = labels[0].split(' ')[0]
            threading.Thread(target=self._fetch_details, args=(self.selected_package,), daemon=True).start()

    def _fetch_details(self, package_name):
        try:
            result = subprocess.run(['yay', '-Si', package_name],
                                    capture_output=True, text=True, timeout=10)
            installed = self._is_installed(package_name.split('/')[-1])
            GLib.idle_add(self._display_details, result.stdout, installed)
        except Exception as e:
            GLib.idle_add(self.details_label.set_text,
                         f"{STRINGS.get('STRING_ERROR_PREFIX', 'Fehler:')} {e}")

    @staticmethod
    def _is_installed(package_name):
        try:
            return subprocess.run(['pacman', '-Q', package_name],
                                  capture_output=True, timeout=5).returncode == 0
        except:
            return False

    def _display_details(self, details, installed):
        # Clear grid
        child = self.details_grid.get_first_child()
        while child:
            self.details_grid.remove(child)
            child = self.details_grid.get_first_child()

        row = 0
        for key, value in self._parse_details(details).items():
            key_label = Gtk.Label()
            key_label.set_markup(f"<b>{key}</b>")
            key_label.add_css_class("monospace")
            key_label.set_halign(Gtk.Align.END)

            value_label = Gtk.Label(label=value)
            value_label.set_wrap(True)
            value_label.set_selectable(True)
            value_label.set_halign(Gtk.Align.START)
            value_label.set_hexpand(True)

            self.details_grid.attach(key_label, 0, row, 1, 1)
            self.details_grid.attach(value_label, 1, row, 1, 1)
            row += 1

        self._update_button_state(installed)
        self.aur_button.set_sensitive(True)

    @staticmethod
    def _parse_details(details):
        """Parse yay -Si output into display-friendly key-value pairs."""
        field_map = {
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
        empty = {'keine', 'nichts', 'none', 'nothing', 'aucun', 'aucune',
                 'ninguno', 'ninguna', 'nessuno', 'nessuna'}

        result = {}
        for line in details.split('\n'):
            if not line.strip() or ':' not in line:
                continue
            for yay_key, display_key in field_map.items():
                if line.startswith(yay_key):
                    value = line.split(':', 1)[1].strip()
                    if value.lower() not in empty:
                        result[display_key] = value
                    break
        return result

    def _update_button_state(self, installed):
        """Update button states based on installation status."""
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

    # --- Package operations ---

    def on_install_clicked(self, button):
        if self.selected_package:
            pkg = self.selected_package.split('/')[-1]
            self.install_button.set_sensitive(False)
            self.uninstall_button.set_sensitive(False)
            self._install_package(pkg)

    def on_uninstall_clicked(self, button):
        if self.selected_package:
            pkg = self.selected_package.split('/')[-1]
            self.install_button.set_sensitive(False)
            self.uninstall_button.set_sensitive(False)
            self._uninstall_package(pkg)

    def on_aur_clicked(self, button):
        if self.selected_package:
            pkg = self.selected_package.split('/')[-1]
            try:
                webbrowser.open(f"https://aur.archlinux.org/packages/{pkg}")
            except:
                self.status_label.set_text(
                    STRINGS.get('STRING_BROWSER_ERROR', 'Fehler: Konnte Browser nicht öffnen'))

    def on_cleanup_clicked(self, button):
        """Clear yay cache in embedded terminal."""
        if self._terminal_running:
            return
        self.set_status(STRINGS.get("STRING_CLEARING_CACHE", "Leere Cache..."))
        command = self._build_command('yay -Sc --noconfirm', 'cleanup')

        def on_done(success):
            if success:
                self.set_status(STRINGS.get("STRING_CACHE_CLEARED", "Cache geleert"))
            else:
                self._show_retry_dialog(
                    self._build_command('yay -Sc', 'cleanup'),
                    lambda s: self.set_status(STRINGS.get("STRING_CACHE_CLEARED", "Cache geleert")))

        self.run_in_embedded_terminal(command, on_complete=on_done)

    def on_update_aur_clicked(self, button):
        """Update all installed AUR packages in embedded terminal."""
        if self._terminal_running:
            return
        self.set_status(STRINGS.get("STRING_UPDATING_AUR", "⬆Aktualisiere alle AUR Pakete..."))
        command = self._build_command(
            'yay -Syua --noconfirm --answerdiff None --answerclean None', 'update')

        def on_done(success):
            if success:
                self.set_status(STRINGS.get("STRING_UPDATE_COMPLETE", "AUR Pakete aktualisiert"))
            else:
                self._show_retry_dialog(
                    self._build_command('yay -Syua', 'update'),
                    lambda s: self.set_status(STRINGS.get("STRING_UPDATE_COMPLETE", "AUR Pakete aktualisiert")))

        self.run_in_embedded_terminal(command, on_complete=on_done)

    def _install_package(self, package_name):
        """Install package (automatic, retry interactive on failure)."""
        if self._terminal_running:
            return
        self.set_status(_("STRING_INSTALLING", package=package_name))
        command = self._build_command(
            f'yay -S --noconfirm --answerdiff None --answerclean None {package_name}', 'install')

        def on_done(success):
            installed = self._is_installed(package_name)
            if installed:
                self.set_status(_("STRING_INSTALL_SUCCESS", package=package_name))
                self._update_button_state(True)
            else:
                interactive = self._build_command(f'yay -S {package_name}', 'install')

                def on_retry(s):
                    inst = self._is_installed(package_name)
                    self.set_status(
                        _("STRING_INSTALL_SUCCESS", package=package_name) if inst
                        else STRINGS.get('STRING_INSTALL_ABORTED',
                                         '⚠ Installation abgebrochen oder fehlgeschlagen'))
                    self._update_button_state(inst)

                self._show_retry_dialog(interactive, on_retry,
                    cancel_callback=lambda: (
                        self.set_status(STRINGS.get('STRING_INSTALL_ABORTED',
                                                    '⚠ Installation abgebrochen oder fehlgeschlagen')),
                        self._update_button_state(False)))

        self.run_in_embedded_terminal(command, on_complete=on_done)

    def _uninstall_package(self, package_name):
        """Uninstall package (automatic, retry interactive on failure)."""
        if self._terminal_running:
            return
        self.set_status(_("STRING_UNINSTALLING", package=package_name))

        # Include debug package if installed
        packages = [package_name]
        debug_pkg = f"{package_name}-debug"
        if self._is_installed(debug_pkg):
            packages.append(debug_pkg)
        remove_list = " ".join(packages)

        command = self._build_command(f'yay -Rns --noconfirm {remove_list}', 'uninstall')

        def on_done(success):
            installed = self._is_installed(package_name)
            if not installed:
                self.set_status(_("STRING_UNINSTALL_SUCCESS", package=package_name))
                self._update_button_state(False)
            else:
                interactive = self._build_command(f'yay -Rns {remove_list}', 'uninstall')

                def on_retry(s):
                    inst = self._is_installed(package_name)
                    self.set_status(
                        _("STRING_UNINSTALL_SUCCESS", package=package_name) if not inst
                        else STRINGS.get('STRING_UNINSTALL_ABORTED',
                                         'Deinstallation abgebrochen oder fehlgeschlagen'))
                    self._update_button_state(inst)

                self._show_retry_dialog(interactive, on_retry,
                    cancel_callback=lambda: (
                        self.set_status(STRINGS.get('STRING_UNINSTALL_ABORTED',
                                                    'Deinstallation abgebrochen oder fehlgeschlagen')),
                        self._update_button_state(True)))

        self.run_in_embedded_terminal(command, on_complete=on_done)

    def _show_retry_dialog(self, interactive_command, on_complete=None, cancel_callback=None):
        """Show Adw.AlertDialog offering to retry the failed operation interactively."""
        dialog = Adw.AlertDialog()
        dialog.set_heading(STRINGS.get('STRING_RETRY_TITLE', 'Automatic installation failed'))
        dialog.set_body(STRINGS.get('STRING_RETRY_MESSAGE',
                                    'The automatic installation has failed. Would you like to retry in interactive mode?'))
        dialog.add_response("cancel", STRINGS.get('STRING_RETRY_CANCEL', 'Cancel'))
        dialog.add_response("retry", STRINGS.get('STRING_RETRY_BUTTON', 'Retry interactively'))
        dialog.set_response_appearance("retry", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("retry")
        dialog.set_close_response("cancel")

        def on_response(d, response):
            if response == "retry":
                self.run_in_embedded_terminal(interactive_command, on_complete=on_complete)
            elif cancel_callback:
                cancel_callback()

        dialog.connect("response", on_response)
        dialog.present(self)

    def set_status(self, text):
        self.status_label.set_text(text)
