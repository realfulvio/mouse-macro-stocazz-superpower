"""Readable Linux desktop panel using the same lifecycle and timing as Windows."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
import traceback

import flet as ft

from macro import linux_setup, linux_updater
from macro.updater import UpdateError
from macro.linux_backend import (LinuxRecorder, LinuxPlayer, GlobalHotkeys, UINPUT_DENIED, list_mice, list_keyboards,
                                 mouse_models)
from macro.mouse_devices import mouse_label
from macro import mods, linux_tray
from macro.panel_model import (LINUX_VERSION, BAMBOLA, SKINS, MOD_SKINS, DEFAULT_SKIN, skin_is_dark, skin_label,
                               register_mod_skins, UPDATE_DOT, parse_repeats, playback_options,
                               settings_path, read_settings, write_settings, save_replay_trace,
                               save_error_log)
from macro.session import Session, State, validate_gestures

ACTIVE = (State.RECORDING, State.PLAYING, State.STOPPING)
NORMAL_SIZE = (440, 800)
EXPANDED_WIDTH = 840
ACTIVE_SIZE = (440, 132)  # compact bar while recording or playing
BAMBOLA_HERO = tuple(BAMBOLA['linux']['hero'])               # horse in the status card
BAMBOLA_BAR = tuple(BAMBOLA['linux']['bar_head']['size'])    # head of the horse in the compact bar
ACTIVE_SIZES = {'bambola': tuple(BAMBOLA['linux']['active_size'])}  # per-skin override: the Bambola bar is as small as TinyTask
ACTIVE_OPACITY = 0.95     # like the Windows bar: slightly see-through
ACCESS_TEXT = ('Il programma non può ancora leggere il mouse e i tasti F9/F10. Premi Concedi accesso: '
               'il sistema chiede la password una volta sola.')
ACCESS_MANUAL = 'Il programma non può ancora leggere il mouse. Apri la Guida per configurare l’accesso una volta.'
ACCESS_NO_AGENT = ('Il sistema non può mostrare la richiesta della password in questa sessione '
                   '(per esempio la modalità gioco di Steam). Passa al Desktop e premi di nuovo Concedi accesso.')
ACCESS_RELOGIN = ('Regola installata. Se il mouse non compare ancora, esci e rientra nella sessione, '
                  'poi premi Aggiorna elenco.')
EN = {
    'Pronto': 'Ready', 'Registrazione': 'Recording', 'Riproduzione': 'Playback',
    'Arresto…': 'Stopping…', 'Errore': 'Error', 'Registra': 'Record',
    'Riproduci': 'Play', 'Stop': 'Stop', 'Eventi': 'Events', 'Durata': 'Duration',
    'Ripetizioni': 'Repeats', 'Salva': 'Save', 'Carica': 'Load', 'Opzioni': 'Options',
    'Guida': 'Help', 'Emergenza': 'Emergency', 'Mouse': 'Mouse',
    'Aggiorna elenco': 'Refresh devices', 'Velocità': 'Speed', 'Normale': 'Normal',
    'Rapida 2×': 'Fast 2×', 'Cambia scheda': 'Next tab',
    'Ctrl+Tab tra un giro e l’altro': 'Ctrl+Tab between cycles',
    'Pagine lente': 'Slow pages', 'Aggiunge pause tra i clic': 'Adds pauses between clicks',
    'Movimento umano': 'Human-like movement',
    'Registra anche la tastiera': 'Record the keyboard too',
    'I tasti digitati finiscono nel file in chiaro, password comprese':
        'Typed keys are stored in the file in plain text, passwords included',
    'Salva avviabile (.sh)': 'Save launchable (.sh)',
    'Percorsi e pause cambiano a ogni giro; i clic restano negli stessi punti':
        'Paths and pauses change every cycle; clicks stay on the same spots',
    'Skin': 'Skin', 'Unicorno': 'Unicorn', 'Palio': 'Palio',
    'Modalità': 'Mode', 'N volte': 'Repeat count', 'Infinito': 'Unlimited',
    'Durata in minuti': 'Duration in minutes', 'Doppio clic (ms)': 'Double click (ms)',
    'Aggiornamenti': 'Updates', 'Controlla ora': 'Check now', 'Controlla all’avvio': 'Check at startup',
    'Chiudi': 'Close', 'Annulla': 'Cancel', 'Installa': 'Install',
    'Nessun aggiornamento da installare': 'No update to install',
    'Stato aggiornamenti sconosciuto': 'Update status unknown', 'Controllo in corso…': 'Checking…',
    'Permessi mouse insufficienti. Vedi la Guida e aggiorna l’elenco.':
        'Mouse access denied. See Help, then refresh devices.',
    'Registra i gesti del mouse.': 'Record your mouse gestures.',
    'Esegui i gesti del mouse, poi F9.': 'Perform the mouse gestures, then press F9.',
    'Macro pronta. Ripristina lo stato iniziale, poi F10.': 'Macro ready. Restore the starting state, then press F10.',
    'Macro caricata. Ripristina lo stato iniziale e premi F10.': 'Macro loaded. Restore the starting state and press F10.',
    'Macro salvata.': 'Macro saved.', 'Riproduzione in corso.': 'Playing.',
    'Arresto in corso…': 'Stopping…', 'Fermato. Controlla la pagina prima di ripartire.':
        'Stopped. Check the page before starting again.',
    'Parti sempre dalla stessa posizione del cursore.': 'Start from the same cursor position each time.',
    'Impossibile salvare le preferenze.': 'Could not save preferences.',
    'Controllo aggiornamenti…': 'Checking for updates…',
    'Controllo aggiornamenti all’avvio attivo.': 'Update check at startup on.',
    'Controllo aggiornamenti all’avvio disattivato: nessun accesso alla rete.':
        'Update check at startup off: no network access.',
    'Non riesco a controllare gli aggiornamenti.': 'Could not check for updates.',
    'Nessuna release Linux pubblicata su GitHub.': 'No Linux release published on GitHub.',
    'Movimento umano attivo: percorsi e pause cambiano a ogni giro, i clic restano sugli stessi punti.':
        'Human-like movement on: paths and pauses change every cycle, clicks stay on the same spots.',
    'Movimento umano disattivato: replay identico alla registrazione.':
        'Human-like movement off: replay identical to the recording.',
    'Nessun clic o rotella nella macro. Registra i gesti del mouse.':
        'No click or wheel in the macro. Record mouse gestures.',
    'Registrazione fermata con un pulsante premuto. Registra di nuovo il gesto completo.':
        'Recording stopped with a button held. Record the complete gesture again.',
    'Imposta da 1 a 999 ripetizioni.': 'Set 1 to 999 repeats.',
    'Tastiera attiva: dalla prossima registrazione i tasti digitati finiscono nella macro, password comprese.':
        'Keyboard on: from the next recording typed keys are stored in the macro, passwords included.',
    'Tastiera disattivata: si registra solo il mouse.': 'Keyboard off: only the mouse is recorded.',
    'Nessuna tastiera accessibile. Premi Concedi accesso o spegni «Registra anche la tastiera».':
        'No keyboard accessible. Press Grant access or turn off “Record the keyboard too”.',
    'Tastiera non accessibile: premi "Concedi accesso" nel pannello oppure spegni la registrazione dei tasti.':
        'Keyboard not accessible: press "Grant access" in the panel or turn off key recording.',
    'La macro contiene un tasto rilasciato senza pressione. Registra di nuovo.':
        'The macro contains a key release without a press. Record again.',
    'Registrazione fermata con un tasto premuto. Registra di nuovo.': 'Recording stopped with a key held. Record again.',
    'La modalità Durata non si può esportare: scegli N volte o Infinito.':
        'Duration mode cannot be exported: choose N times or Infinite.',
    'Concedi accesso': 'Grant access',
    ACCESS_TEXT: 'The program cannot read the mouse and the F9/F10 keys yet. Press Grant access: '
                 'the system asks for your password once.',
    ACCESS_MANUAL: 'The program cannot read the mouse yet. Open Help to configure access once.',
    'Accesso al mouse concesso.': 'Mouse access granted.',
    ACCESS_NO_AGENT: 'This session cannot show the password prompt (for example Steam Game Mode). '
                     'Switch to the Desktop and press Grant access again.',
    ACCESS_RELOGIN: 'Rule installed. If the mouse is still missing, log out and back in, then press Refresh devices.',
    'Configurazione annullata.': 'Setup cancelled.',
    UINPUT_DENIED: 'Cannot create the virtual mouse: /dev/uinput is missing or not accessible. '
                   'Press "Grant access" in the panel.',
    'Scorciatoie globali non disponibili: accesso tastiera necessario.':
        'Global shortcuts unavailable: keyboard access required.',
}
EN_TEMPLATES = [
    (r'Mouse: giro 1/(\d+)', r'Mouse: cycle 1/\1'),
    (r'Mouse: (\d+)/(\d+) completati', r'Mouse: \1/\2 completed'),
    (r'Completati (\d+) giri\.', r'Completed \1 cycles.'),
    (r'Sei aggiornato: versione (.+)\.', r'You are up to date: version \1.'),
    (r'Disponibile la versione (.+): clicca il pallino in alto\.', r'Version \1 is available: click the dot at the top.'),
    (r'Disponibile la versione (.+) \(hai la (.+)\)', r'Version \1 is available (you have \2)'),
    (r'Aggiornato · versione (.+)', r'Up to date · version \1'),
    (r'Scarica e installa la versione (.+)', r'Download and install version \1'),
    (r'Scarico la versione (.+)…', r'Downloading version \1…'),
    (r'Flatpak: aggiorna dal gestore software o scarica il nuovo \.flatpak', r'Flatpak: update from the software centre or download the new .flatpak'),
    (r'Mouse rilevati: (.+)', r'Mice detected: \1'),
    (r'Macro avviabile creata: (.+)\. Serve Mouse Macro installato sul PC dove la apri\.',
     r'Launchable macro created: \1. Mouse Macro must be installed on the PC where you open it.'),
    (r'Mouse: modello non disponibile', r'Mouse: model unavailable'),
]


def duration_text(seconds):
    return f'{int(seconds)//60:02d}:{int(seconds)%60:02d}'


class LinuxPanel:
    def __init__(self, page, language='it', preferences=None, preview=False, open_request=None):
        self.page, self.language, self.preview = page, language, preview
        self.open_request = open_request  # macro avviabile: caricata all'avvio, mai avviata da sola
        self.path = Path(preferences) if preferences else settings_path()
        self.folder = self.path.parent  # diagnostics live next to the preferences
        self.mods_dir = self.folder / 'mods'
        try:
            register_mod_skins(mods.installed(self.mods_dir))  # before read_settings: it validates the skin name
        except Exception:
            pass  # a damaged mod must never stop the panel from opening
        self.settings = read_settings(self.path)
        self.tray = None
        self.tray_actions = queue.Queue()
        self.skin = self.settings.get('skin', DEFAULT_SKIN)
        self.colors = SKINS[self.skin]
        self.commands = queue.Queue()
        self.hotkeys = None
        self.closed = False
        self.dialog_open = False
        self.expanded = False
        self.active_view = False
        self.started = None
        self.dirty = threading.Event()
        self.devices = []
        self.models = []
        self.access = {'events': True, 'uinput': True, 'rule': False}
        self.speed = 1.0
        self.update = {'state': 'unknown', 'latest': None, 'release': None}
        self.last_options = None
        self.trace_saved = None
        self.session = Session(self.make_recorder, LinuxPlayer, self.dirty.set, platform='linux')
        self.page.title = f'Mouse Macro {LINUX_VERSION} · Linux · hcok'
        self.page.fonts = {'Outfit': 'fonts/Outfit.ttf'}
        self.page.theme = ft.Theme(font_family='Outfit', color_scheme_seed=self.colors['play'])
        self.page.theme_mode = ft.ThemeMode.DARK if skin_is_dark(self.skin) else ft.ThemeMode.LIGHT
        self.page.padding = 16
        self.page.bgcolor = self.colors['background']
        window = self.settings.get('window', {})
        self.normal_size = [window.get('width', NORMAL_SIZE[0]), window.get('height', NORMAL_SIZE[1])]
        self.page.window.width, self.page.window.height = self.normal_size
        if 'left' in window and 'top' in window:
            # Wayland compositors may ignore a requested position; X11 honors it.
            self.page.window.left, self.page.window.top = window['left'], window['top']
        self.page.window.min_width, self.page.window.min_height = 420, 380
        self.page.window.always_on_top = True
        self.page.window.prevent_close = True
        self.page.window.on_event = self.window_event
        self.page.on_disconnect = self.disconnect
        self.page.on_keyboard_event = self.keyboard
        self.picker = ft.FilePicker()
        self.page.services.append(self.picker)
        self.build()
        self.page.add(self.root)
        self.render()

    def tr(self, text):
        if self.language != 'en' or not isinstance(text, str):
            return text
        if text in EN:
            return EN[text]
        for pattern, replacement in EN_TEMPLATES:
            if re.fullmatch(pattern, text):
                return re.sub(pattern, replacement, text)
        from localization import translate
        return translate(text, 'en')

    def text(self, value, size=18, bold=False, muted=False, **kwargs):
        return ft.Text(self.tr(value), size=size,
                       weight=ft.FontWeight.W_600 if bold else ft.FontWeight.W_400,
                       color=self.colors['muted' if muted else 'text'], **kwargs)

    def button(self, label, handler, color=None, icon=None, **kwargs):
        kwargs.setdefault('height', 52)
        return ft.Button(content=self.text(label, 18, True), icon=icon, on_click=handler,
                         bgcolor=color or self.colors['surface'], color=self.colors['text'],
                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                         **kwargs)

    def card(self, control, **kwargs):
        return ft.Container(content=control, padding=16, bgcolor=self.colors['surface'],
                            border=ft.Border.all(1, self.colors['border']), border_radius=14, **kwargs)

    def horse(self, state='pronto', size=72, bar=False):
        if self.skin == 'bambola':
            return self.bambola_horse(state, bar)
        if self.skin in MOD_SKINS:
            return self.mod_horse(state, size)
        prefix = 'palio' if self.skin == 'palio' else 'unicorn'
        if prefix == 'palio':
            return ft.Image(src=f'horses/{prefix}_{state}.png', width=size, height=size,
                            fit=ft.BoxFit.CONTAIN, exclude_from_semantics=True)
        # The supplied originals carry catalog captions: crop in the view only.
        regions = {'pronto': (180,194,126,113), 'registrazione': (184,191,144,114),
                   'riproduzione': (179,181,151,119), 'errore': (209,181,134,123)}
        x,y,w,h = regions[state]
        scale = min(size/w, size/h)
        return ft.Stack([ft.Image(src=f'horses/{prefix}_{state}.png', width=512*scale,
                                 height=512*scale, left=-x*scale+(size-w*scale)/2,
                                 top=-y*scale+(size-h*scale)/2, exclude_from_semantics=True)],
                        width=size, height=size, clip_behavior=ft.ClipBehavior.HARD_EDGE)

    def mod_horse(self, state, size):
        mod = MOD_SKINS[self.skin]
        src = str(mod['folder'] / f'{state}.png')
        if not mod['regions']:
            return ft.Image(src=src, width=size, height=size, fit=ft.BoxFit.CONTAIN, exclude_from_semantics=True)
        x, y, w, h = mod['regions'][state]
        scale = min(size / w, size / h)
        full = self.mod_image_size(src)
        return ft.Stack([ft.Image(src=src, width=full[0] * scale, height=full[1] * scale,
                                  left=-x * scale + (size - w * scale) / 2, top=-y * scale + (size - h * scale) / 2,
                                  exclude_from_semantics=True)],
                        width=size, height=size, clip_behavior=ft.ClipBehavior.HARD_EDGE)

    @staticmethod
    def mod_image_size(path):
        width, height = mods.png_size(Path(path).read_bytes()[:64])
        return width, height

    # Bambola clips are cropped animated WebP (assets/horses, data in assets/skins/bambola.json).
    BAMBOLA_SIZE = tuple(BAMBOLA['images']['frame'])
    BAMBOLA_HEAD = tuple(BAMBOLA['linux']['bar_head']['crop'])  # head and neck (x, y, w, h)

    def bambola_horse(self, state, bar=False):
        src = f'horses/bambola_{state}.webp'
        width, height = self.BAMBOLA_SIZE
        if not bar:
            return ft.Image(src=src, width=BAMBOLA_HERO[0], height=BAMBOLA_HERO[1],
                            fit=ft.BoxFit.CONTAIN, exclude_from_semantics=True)
        x, y, w, h = self.BAMBOLA_HEAD
        scale = BAMBOLA_BAR[0] / w
        return ft.Stack([ft.Image(src=src, width=width*scale, height=height*scale, left=-x*scale,
                                  top=-y*scale, exclude_from_semantics=True)],
                        width=BAMBOLA_BAR[0], height=BAMBOLA_BAR[1], clip_behavior=ft.ClipBehavior.HARD_EDGE)

    def build(self):
        self.status = self.text('Pronto', 26, True)
        self.message = self.text(self.session.message, 16, muted=True)
        self.event_count, self.duration = self.text('0', 22, True), self.text('00:00', 22, True)
        self.mascot = ft.Container(self.horse())
        self.dot = ft.Container(width=12, height=12, border_radius=6, bgcolor=self.colors['ready'])
        self.mouse_model = self.text(self.mouse_text(), 16, muted=True)
        if self.skin == 'bambola':
            # Large horse on the right, status and counters over the open space on the left.
            self.mascot = ft.Container(self.horse(), right=-8, bottom=-4)
            self.status_card = self.card(ft.Column([
                ft.Stack([self.mascot,
                          ft.Column([ft.Row([self.dot, self.status]), ft.Container(self.message, width=170)],
                                    spacing=6, left=0, top=0),
                          ft.Row([ft.Column([self.text('Eventi',16,muted=True), self.event_count], spacing=0),
                                  ft.Column([self.text('Durata',16,muted=True), self.duration], spacing=0)],
                                 spacing=24, left=0, bottom=0)],
                         height=BAMBOLA_HERO[1] + 4, clip_behavior=ft.ClipBehavior.HARD_EDGE),
                self.mouse_model,
            ], spacing=10))
        else:
            self.status_card = self.card(ft.Column([
                ft.Row([ft.Column([ft.Row([self.dot, self.status]), self.message], expand=True), self.mascot]),
                ft.Row([ft.Column([self.text('Eventi',16,muted=True), self.event_count], expand=True),
                        ft.Column([self.text('Durata',16,muted=True), self.duration], expand=True)]),
                self.mouse_model,
            ], spacing=14))
        self.record = self.button('Registra', self.record_clicked, self.colors['record'],
                                  ft.Icons.FIBER_MANUAL_RECORD, tooltip='F9')
        self.play = self.button('Riproduci', self.play_clicked, self.colors['play'],
                                ft.Icons.PLAY_ARROW_ROUNDED, tooltip='F10')
        self.record.height = self.play.height = 64
        self.record.expand = self.play.expand = True
        self.repeat = ft.TextField(value='1', text_size=20, width=94, text_align=ft.TextAlign.CENTER,
                                   on_change=self.repeat_changed, color=self.colors['text'],
                                   border_color=self.colors['border'], content_padding=12)
        self.minus = self.button('−', lambda e:self.change_count(-1), width=48)
        self.plus = self.button('+', lambda e:self.change_count(1), width=48)
        self.preset = self.button('Preset 20', lambda e:self.set_count(20))
        self.save = self.button('Salva', self.save_file, icon=ft.Icons.SAVE_OUTLINED, expand=True)
        self.load = self.button('Carica', self.load_file, icon=ft.Icons.FOLDER_OPEN, expand=True)
        self.option_button = self.button('Opzioni', self.toggle_options, icon=ft.Icons.TUNE)
        self.mouse = ft.Dropdown(label=self.tr('Mouse'), text_size=16, options=[],
                                 value=self.settings.get('device'), on_select=self.mouse_changed)
        self.refresh = self.button('Aggiorna elenco', self.refresh_devices, icon=ft.Icons.REFRESH)
        self.device_hint = self.text('', 16, muted=True)
        self.access_text = self.text(ACCESS_TEXT if linux_setup.can_grant() else ACCESS_MANUAL, 16)
        self.access_button = self.button('Concedi accesso', self.grant_access, self.colors['record'],
                                         ft.Icons.LOCK_OPEN, visible=linux_setup.can_grant())
        self.access_banner = self.card(ft.Column([ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED,
                                                                  color=self.colors['record']),
                                                          ft.Container(self.access_text, expand=True)]),
                                                  ft.Row([self.access_button])], spacing=10), visible=False)
        self.normal = self.button('Normale', lambda e:self.set_speed(1.0), expand=True)
        self.rapid = self.button('Rapida 2×', lambda e:self.set_speed(2.0), expand=True)
        self.next_tab = ft.Switch(value=False, on_change=self.option_changed)
        self.slow = ft.Switch(value=False, on_change=self.option_changed)
        self.human = ft.Switch(value=False, on_change=self.human_changed)
        self.keyboard_switch = ft.Switch(value=False, on_change=self.keyboard_changed)  # sempre spento all'avvio
        self.export_button = self.button('Salva avviabile (.sh)', self.export_file, icon=ft.Icons.ROCKET_LAUNCH_OUTLINED)
        def setting(label, hint, switch):
            return ft.Row([ft.Column([self.text(label,18,True), self.text(hint,16,muted=True)], expand=True), switch])
        self.mode = ft.Dropdown(label=self.tr('Modalità'), value='count', text_size=16,
                                options=[ft.DropdownOption(key=k,text=self.tr(v)) for k,v in
                                         [('count','N volte'),('infinite','Infinito'),('duration','Durata')]],
                                on_select=self.mode_changed)
        self.minutes = ft.TextField(label=self.tr('Durata in minuti'), value='10', text_size=18, visible=False)
        self.double_click = ft.TextField(label=self.tr('Doppio clic (ms)'),
                                         value=str(self.settings.get('double_click_ms','400')), text_size=18,
                                         on_blur=self.preference_changed)
        self.skin_choice = ft.Dropdown(label=self.tr('Skin'),value=self.skin,text_size=16,
                                       options=self.skin_options(),
                                       on_select=self.skin_changed)
        self.settings_button = self.button('Impostazioni e mod', self.settings_menu, icon=ft.Icons.SETTINGS)
        self.update_dot = ft.Container(width=14, height=14, border_radius=7)
        self.update_button = ft.Button(
            content=ft.Row([self.update_dot, self.text('Aggiornamenti', 18, True)], tight=True, spacing=10),
            icon=ft.Icons.SYSTEM_UPDATE, on_click=self.update_menu, bgcolor=self.colors['surface'],
            color=self.colors['text'], height=52,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
        self.header_dot = ft.Container(width=14, height=14, border_radius=7, on_click=self.update_menu,
                                       tooltip=self.tr('Aggiornamenti'))
        self.options = self.card(ft.Column([
            self.text('Opzioni',24,True), self.preset, self.text('Velocità',18,True),
            ft.Row([self.normal,self.rapid]),
            setting('Cambia scheda','Ctrl+Tab tra un giro e l’altro',self.next_tab),
            setting('Pagine lente','Aggiunge pause tra i clic',self.slow),
            setting('Movimento umano','Percorsi e pause cambiano a ogni giro; i clic restano negli stessi punti',
                    self.human),
            setting('Registra anche la tastiera','I tasti digitati finiscono nel file in chiaro, password comprese',
                    self.keyboard_switch),
            ft.Divider(color=self.colors['border']), self.mode,self.minutes,self.double_click,
            self.export_button,
            self.skin_choice,self.settings_button,self.update_button,
        ],spacing=16,scroll=ft.ScrollMode.AUTO),expand=True,visible=False)
        self.main_column = ft.Column([
            ft.Row([ft.Column([self.text('Mouse Macro',24,True),self.text('Stocazz Superpower',18,muted=True)],
                              expand=True), self.header_dot]),
            self.access_banner,self.status_card,ft.Row([self.record]),ft.Row([self.play]),
            self.card(ft.Row([self.text('Ripetizioni',18,True,expand=True),self.minus,self.repeat,self.plus])),
            ft.Row([self.save,self.load]), self.mouse,self.refresh,self.device_hint,
        ],spacing=12,expand=True,scroll=ft.ScrollMode.AUTO)
        self.normal_view = ft.Row([self.main_column,self.options],spacing=16,expand=True)
        # Compact bar shown alone while recording or playing, as on Windows.
        compact = self.skin == 'bambola'
        self.activity_horse = ft.Container(self.horse('registrazione', 48, bar=True) if compact
                                           else self.horse('registrazione', 48))
        tight = {'style': ft.TextStyle(height=1.1)} if compact else {}  # line-height multiplier: three lines must fit in 69 px
        self.activity_status = self.text('Registrazione',17 if compact else 22,True,**tight)
        self.activity_count = self.text('',12 if compact else 18,**tight)
        self.activity_hint = self.text('',10.5 if compact else 14,muted=True,**tight)
        if compact:
            self.stop = ft.Button(content=ft.Icon(ft.Icons.STOP_ROUNDED, color=self.colors['text'], size=22),
                                  on_click=self.stop_clicked, bgcolor=self.colors['record'], width=44, height=40,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=9),
                                                       padding=ft.Padding.all(0)))
        else:
            self.stop = ft.Button(content=self.text('Stop',24,True), icon=ft.Icons.STOP_ROUNDED,
                                  on_click=self.stop_clicked, bgcolor=self.colors['record'],
                                  color=self.colors['text'], width=140, height=72,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)))
        self.progress = ft.ProgressBar(value=0,color=self.colors['play'],bgcolor=self.colors['border'],visible=False,
                                       **({'bar_height': 3} if compact else {}))
        if compact:
            # 300x72 like a TinyTask-sized bar: horse head, three short lines, square Stop.
            self.activity_view = ft.WindowDragArea(ft.Column([
                ft.Row([self.activity_horse,
                        ft.Column([self.activity_status,self.activity_count,self.activity_hint],spacing=0,expand=True,
                                  alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(self.stop, padding=ft.Padding.only(right=10))],
                       spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER, height=BAMBOLA_BAR[1]-6),
                self.progress, ft.Container(height=3),
            ],spacing=0), maximizable=False, visible=False)
        else:
            self.activity_view = ft.WindowDragArea(ft.Column([
                ft.Row([self.activity_horse,
                        ft.Column([self.activity_status,self.activity_count,self.activity_hint],spacing=2,expand=True),
                        self.stop], spacing=12),
                self.progress,
            ],spacing=8), maximizable=False, visible=False)
        self.footer = ft.Row([
            ft.IconButton(ft.Icons.HELP_OUTLINE,on_click=self.help,tooltip=self.tr('Guida'),icon_size=28,
                          icon_color=self.colors['text'],bgcolor=self.colors['surface'],width=52,height=52),
            self.option_button,
            self.button('Emergenza',self.emergency,icon=ft.Icons.WARNING_AMBER_ROUNDED,expand=True,
                        tooltip='Ctrl+Alt+F11'),
        ])
        self.shortcut_hint = self.text('F9 · F10 · Ctrl+Alt+F11',16,muted=True)
        self.root = ft.Column([self.normal_view,self.activity_view,self.footer,self.shortcut_hint],
                              spacing=12,expand=True)

    def mouse_text(self):
        selected = next((n for p, n in self.devices if p == self.mouse.value), None) if hasattr(self, 'mouse') else None
        if selected:
            return self.tr(mouse_label([selected]))
        if self.devices:
            return self.tr(mouse_label([n for p, n in self.devices]))
        if self.models:
            # /proc names are readable without device access: show the model anyway.
            return self.tr(mouse_label(self.models)) + (' · no access' if self.language == 'en' else ' · senza permessi')
        return self.tr(mouse_label([]))

    def valid_macro(self):
        try:
            validate_gestures(self.session.macro.events)
            return True
        except ValueError:
            return False

    def set_active_view(self, active):
        if active == self.active_view:
            return
        window = self.page.window
        active_size = ACTIVE_SIZES.get(self.skin, ACTIVE_SIZE)
        if active:
            self.remember_window()
            window.min_width = min(420, active_size[0])
            window.min_height = min(140, active_size[1])
            window.width, window.height = active_size
            self.page.padding = 0 if self.skin in ACTIVE_SIZES else 16
            try:
                window.opacity = ACTIVE_OPACITY
            except (AttributeError, ValueError):
                pass
            self.started = time.monotonic()
        else:
            window.min_width = 420
            window.min_height = 380
            self.page.padding = 16
            window.width = EXPANDED_WIDTH if self.expanded else self.normal_size[0]
            window.height = self.normal_size[1]
            try:
                window.opacity = 1.0
            except (AttributeError, ValueError):
                pass
            self.started = None
        self.active_view = active

    def activity_detail(self, state, count, seconds):
        if state == State.RECORDING:
            unit = 'events' if self.language == 'en' else 'eventi'
            return f'{count} {unit} · {duration_text(seconds)}'
        cycles = 'cycles' if self.language == 'en' else 'giri'
        options = self.last_options
        done = self.session.completed
        if options is not None and options.repeat_count and self.mode.value == 'count':
            return f'{done}/{options.repeat_count} {cycles} · {duration_text(seconds)}'
        if options is not None and self.mode.value == 'duration':
            return f'{done} {cycles} · {duration_text(seconds)} / {duration_text(options.duration_seconds)}'
        return f'{done} {cycles} · {duration_text(seconds)}'

    def render(self):
        state = self.session.state
        active = state in ACTIVE
        self.set_active_view(active)
        label = {State.READY:'Pronto',State.RECORDING:'Registrazione',State.PLAYING:'Riproduzione',
                 State.STOPPING:'Arresto…',State.ERROR:'Errore',State.CLOSED:'Pronto'}[state]
        self.status.value = self.activity_status.value = self.tr(label)
        self.message.value = self.tr(self.session.message)
        self.dot.bgcolor = self.colors['record' if state==State.RECORDING else 'play' if active else
                                       'error' if state==State.ERROR else 'ready']
        horse_state = 'registrazione' if state==State.RECORDING else 'riproduzione' if active else 'errore' if state==State.ERROR else 'pronto'
        self.mascot.content = self.horse(horse_state)
        self.activity_horse.content = self.horse(horse_state, 48, bar=True)
        self.activity_status.color = self.colors['record' if state==State.RECORDING else 'text']
        recorder = self.session.recorder
        count = recorder.current_event_count if recorder and state==State.RECORDING else len(self.session.macro.events)
        seconds = (time.monotonic()-self.started if active and self.started else
                   self.session.macro.events[-1].t if self.session.macro.events else 0)
        self.event_count.value,self.duration.value = str(count),duration_text(seconds)
        self.activity_count.value = self.activity_detail(state, count, seconds)
        self.activity_hint.value = ('F9 stop' if state==State.RECORDING else 'F10 stop · Ctrl+Alt+F11')
        self.mouse_model.value = self.mouse_text()
        self.access_banner.visible = not self.preview and self.access_missing()
        self.access_button.disabled = active or self.dialog_open
        self.normal_view.visible,self.activity_view.visible = not active,active
        self.footer.visible = self.shortcut_hint.visible = not active
        self.options.visible = self.expanded and not active
        self.record.disabled = active or self.dialog_open
        self.play.disabled = active or self.dialog_open or not self.valid_macro()
        self.save.disabled = active or self.dialog_open or not self.valid_macro()
        self.load.disabled = active or self.dialog_open
        for button in (self.record, self.play, self.save, self.load):
            # Colored buttons keep their color when disabled: dim them so it shows.
            button.opacity = 0.45 if button.disabled else 1.0
        self.stop.disabled = state==State.STOPPING
        if self.skin == 'bambola':
            self.stop.bgcolor = self.colors['play' if state==State.PLAYING else 'record']
        self.stop.tooltip = 'F9' if state==State.RECORDING else 'F10'
        self.progress.visible = state in (State.PLAYING,State.STOPPING) and self.mode.value=='count'
        try:
            self.progress.value = self.session.completed/parse_repeats(self.repeat.value)
        except ValueError:
            self.progress.value = 0
        self.normal.bgcolor = self.colors['play' if self.speed==1 else 'surface']
        self.rapid.bgcolor = self.colors['play' if self.speed==2 else 'surface']
        self.repeat.disabled = self.mode.value!='count'
        dot = self.colors[UPDATE_DOT.get(self.update['state'], 'border')]
        self.update_dot.bgcolor = self.header_dot.bgcolor = dot
        self.header_dot.tooltip = self.update_status()
        self.save_trace()
        self.page.update()

    def save_trace(self):
        """Write ultimo-replay.json once per finished playback, like Windows."""
        trace = self.session.last_trace
        if trace and self.session.state in (State.READY, State.ERROR) and self.trace_saved is not trace:
            self.trace_saved = trace
            save_replay_trace(self.folder, LINUX_VERSION, self.last_options,
                              self.session.state.value, list(trace))

    def log_error(self, name='errore.log'):
        save_error_log(self.folder, traceback.format_exc(), name)

    def make_recorder(self):
        if not self.mouse.value:
            raise ValueError(self.tr('Permessi mouse insufficienti. Vedi la Guida e aggiorna l’elenco.'))
        keyboards = []
        if self.keyboard_switch.value:
            keyboards = [path for path, name in list_keyboards()]
            if not keyboards:
                raise ValueError(self.tr('Nessuna tastiera accessibile. Premi Concedi accesso o spegni «Registra anche la tastiera».'))
        return LinuxRecorder(self.mouse.value, keyboards)

    async def start(self):
        self.start_tray()
        await self.refresh_devices()
        if self.open_request:
            await self.apply_open_request()
        self.page.run_task(self.pump)
        if self.settings.get('check_updates', True):
            self.page.run_task(self.check_updates)
        self.render()

    async def pump(self):
        while not self.closed:
            try:
                while not self.tray_actions.empty():
                    await self.tray_action(self.tray_actions.get())
                while not self.commands.empty():
                    command = self.commands.get()
                    if not self.dialog_open or command=='emergency':
                        await self.dispatch(command)
                if self.dirty.is_set() or self.session.state in ACTIVE:
                    self.dirty.clear()
                    self.render()
            except Exception as error:
                self.log_error()
                self.session.request_stop()
                self.session.error(error)
            await asyncio.sleep(.1)

    def hotkey(self, code):
        from macro.linux_backend import HOTKEY_RECORD,HOTKEY_PLAY,HOTKEY_EMERGENCY
        command = {HOTKEY_RECORD:'record',HOTKEY_PLAY:'play',HOTKEY_EMERGENCY:'emergency'}.get(code)
        if command=='emergency' or command=='play' and self.session.state in ACTIVE:
            self.session.request_stop()
        if command:
            self.commands.put(command)

    async def keyboard(self,e):
        if self.hotkeys and not self.hotkeys.failed:
            return
        command = ('emergency' if e.key=='F11' and e.ctrl and (e.alt or e.shift) else
                   {'F9':'record','F10':'play'}.get(e.key))
        if command and (not self.dialog_open or command=='emergency'):
            await self.dispatch(command)

    async def dispatch(self,command,mouse_stop=False):
        try:
            if command=='record':
                await asyncio.to_thread(self.session.toggle_record,mouse_stop)
            elif command=='play':
                if self.session.state in (State.PLAYING,State.STOPPING):
                    self.session.request_stop()
                else:
                    options = playback_options(self.repeat.value,self.speed,self.slow.value,self.human.value,
                                               self.mode.value,self.minutes.value,self.double_click.value)
                    self.last_options = options
                    await asyncio.to_thread(self.session.toggle_play,options,self.next_tab.value)
            elif command=='emergency':
                self.session.request_stop()
                if self.session.state==State.RECORDING:
                    await asyncio.to_thread(self.session.toggle_record,mouse_stop)
        except (OSError,ValueError) as error:
            self.session.error(error)
        except Exception as error:
            self.log_error()
            self.session.request_stop()
            self.session.error(error)
        self.render()

    async def record_clicked(self,e=None):
        await self.dispatch('record')

    async def play_clicked(self,e=None):
        await self.dispatch('play')

    async def stop_clicked(self,e=None):
        await self.dispatch('record' if self.session.state==State.RECORDING else 'emergency',mouse_stop=True)

    async def emergency(self,e=None):
        await self.dispatch('emergency',mouse_stop=e is not None)

    def repeat_changed(self,e=None):
        try:
            parse_repeats(self.repeat.value)
            self.repeat.error_text = None
        except ValueError as error:
            self.repeat.error_text = self.tr(str(error))
        self.page.update()

    def set_count(self,value):
        self.repeat.value = str(value)
        self.repeat_changed()

    def change_count(self,delta):
        try:
            self.set_count(max(1,min(999,parse_repeats(self.repeat.value)+delta)))
        except ValueError as error:
            self.session.error(error)
            self.render()

    def set_speed(self,value):
        self.speed=value
        self.render()

    def option_changed(self,e=None):
        self.render()

    def human_changed(self,e=None):
        self.session.message = ('Movimento umano attivo: percorsi e pause cambiano a ogni giro, i clic restano sugli stessi punti.'
                                if self.human.value else 'Movimento umano disattivato: replay identico alla registrazione.')
        self.render()

    def keyboard_changed(self,e=None):
        self.session.message = ('Tastiera attiva: dalla prossima registrazione i tasti digitati finiscono nella macro, password comprese.'
                                if self.keyboard_switch.value else 'Tastiera disattivata: si registra solo il mouse.')
        self.render()

    async def apply_open_request(self):
        """Macro avviabile (.sh): carica il file e imposta giri e opzioni. La riproduzione resta a F10."""
        request, self.open_request = self.open_request, None
        if not await asyncio.to_thread(self.session.load, request.path):
            return
        self.repeat.value = str(request.repeats)
        self.mode.value = 'infinite' if request.infinite else 'count'
        self.speed = float(request.speed)
        self.next_tab.value, self.slow.value, self.human.value = request.next_tab, request.slow, request.human
        self.render()

    async def export_file(self,e=None):
        if self.session.state in ACTIVE or self.dialog_open:
            return
        self.dialog_open=True
        self.render()
        try:
            if self.mode.value == 'duration':
                raise ValueError('La modalità Durata non si può esportare: scegli N volte o Infinito.')
            infinite = self.mode.value == 'infinite'
            repeats = 1 if infinite else parse_repeats(self.repeat.value)
            path=await self.picker.save_file(dialog_title=self.tr('Salva avviabile (.sh)'),file_name='macro.sh',
                file_type=ft.FilePickerFileType.CUSTOM,allowed_extensions=['sh'])
            if path:
                await asyncio.to_thread(self.session.export,path,repeats,int(self.speed),self.slow.value,
                                        self.human.value,self.next_tab.value,infinite)
        except Exception as error:
            self.session.error(error)
        finally:
            self.dialog_open=False
            self.render()

    def mode_changed(self,e=None):
        self.minutes.visible=self.mode.value=='duration'
        self.render()

    def toggle_options(self,e=None):
        self.expanded=not self.expanded
        self.page.window.width=EXPANDED_WIDTH if self.expanded else self.normal_size[0]
        self.render()

    def mouse_changed(self,e=None):
        self.settings['device']=self.mouse.value
        self.preference_changed()

    def write_preferences(self):
        if not write_settings(self.path,self.settings):
            self.session.message='Impossibile salvare le preferenze.'

    def preference_changed(self,e=None):
        self.settings['double_click_ms']=self.double_click.value
        self.write_preferences()
        self.render()

    def remember_window(self):
        """Store the normal panel geometry; the compact bar is never persisted."""
        if self.active_view:
            return
        window = self.page.window
        geometry = {}
        for key in ('width', 'height', 'left', 'top'):
            value = getattr(window, key, None)
            if type(value) in (int, float):
                geometry[key] = int(value)
        if self.expanded:
            geometry.pop('width', None)  # the collapsed width is the one restored at launch
        if geometry.get('width', 10**6) < 420 or geometry.get('height', 10**6) < 380:
            return
        self.normal_size = [geometry.get('width', self.normal_size[0]), geometry.get('height', self.normal_size[1])]
        stored = dict(self.settings.get('window', {}))
        stored.update(geometry)
        self.settings['window'] = stored

    def skin_changed(self,e=None):
        self.skin=self.skin_choice.value
        self.settings['skin']=self.skin
        self.write_preferences()
        # Rebuild controls together so a skin cannot leave mixed colors behind.
        repeats,mode,minutes=self.repeat.value,self.mode.value,self.minutes.value
        speed,next_tab,slow,human=self.speed,self.next_tab.value,self.slow.value,self.human.value
        device=self.mouse.value
        self.colors=SKINS[self.skin]
        self.page.bgcolor=self.colors['background']
        self.page.theme_mode=ft.ThemeMode.DARK if skin_is_dark(self.skin) else ft.ThemeMode.LIGHT
        self.page.theme=ft.Theme(font_family='Outfit',color_scheme_seed=self.colors['play'])
        self.build()
        self.repeat.value,self.mode.value,self.minutes.value=repeats,mode,minutes
        self.speed,self.next_tab.value,self.slow.value,self.human.value=speed,next_tab,slow,human
        self.minutes.visible=mode=='duration'
        self.mouse.options=[ft.DropdownOption(key=p,text=n) for p,n in self.devices]
        self.mouse.value=device
        self.options.visible=self.expanded
        self.page.controls.clear()
        self.page.add(self.root)
        self.render()

    async def start_hotkeys(self):
        """(Re)start the global F9/F10 listener: also after access is granted,
        without restarting the program."""
        if self.hotkeys and not self.hotkeys.failed:
            return
        if self.hotkeys:
            await asyncio.to_thread(self.hotkeys.stop)
        self.hotkeys = GlobalHotkeys(self.hotkey)
        await asyncio.to_thread(self.hotkeys.start)
        self.shortcut_hint.value = self.tr('Scorciatoie globali non disponibili: accesso tastiera necessario.'
                                           if self.hotkeys.failed else 'F9 · F10 · Ctrl+Alt+F11')

    def access_missing(self):
        return (not self.devices or not self.access.get('uinput')
                or bool(self.hotkeys and self.hotkeys.failed))

    async def grant_access(self, e=None):
        if self.session.state in ACTIVE or self.dialog_open:
            return
        self.dialog_open = True
        self.render()
        try:
            ok, detail = await asyncio.to_thread(linux_setup.grant_access)
        finally:
            self.dialog_open = False
        if not ok:
            self.session.message = {'annullato': 'Configurazione annullata.',
                                    'senza_agente': ACCESS_NO_AGENT}.get(detail, detail)
            self.render()
            return
        await asyncio.sleep(1)  # logind applies the seat ACLs right after the udev change event
        await self.refresh_devices()
        self.session.message = 'Accesso al mouse concesso.' if not self.access_missing() else ACCESS_RELOGIN
        self.render()

    async def refresh_devices(self,e=None):
        self.devices=await asyncio.to_thread(list_mice)
        self.models=await asyncio.to_thread(mouse_models)
        self.access=await asyncio.to_thread(linux_setup.input_access)
        if not self.preview:
            await self.start_hotkeys()
        self.mouse.options=[ft.DropdownOption(key=p,text=n) for p,n in self.devices]
        paths={p for p,n in self.devices}
        if self.mouse.value not in paths:
            self.mouse.value=self.devices[0][0] if self.devices else None
        self.device_hint.value=self.tr('Parti sempre dalla stessa posizione del cursore.' if self.devices else
                                       'Permessi mouse insufficienti. Vedi la Guida e aggiorna l’elenco.')
        self.render()

    async def file_action(self,save):
        if self.session.state in ACTIVE or self.dialog_open:
            return
        self.dialog_open=True
        self.render()
        try:
            if save:
                path=await self.picker.save_file(dialog_title=self.tr('Salva'),file_name='macro.mmr',
                    file_type=ft.FilePickerFileType.CUSTOM,allowed_extensions=['mmr'])
                if path:
                    await asyncio.to_thread(self.session.save,Path(path).with_suffix('.mmr') if not Path(path).suffix else path)
            else:
                files=await self.picker.pick_files(dialog_title=self.tr('Carica'),allow_multiple=False,
                    file_type=ft.FilePickerFileType.CUSTOM,allowed_extensions=['mmr','json'])
                if files and files[0].path:
                    await asyncio.to_thread(self.session.load,files[0].path)
        except Exception as error:
            self.session.error(error)
        finally:
            self.dialog_open=False
            self.render()

    async def save_file(self,e=None):
        await self.file_action(True)

    async def load_file(self,e=None):
        await self.file_action(False)

    # Updates: same flow as Windows (dot, startup check, verified install), but
    # reading linux-v* releases, never /releases/latest.
    def update_status(self):
        state, latest = self.update['state'], self.update['latest']
        return self.tr({'current': f'Aggiornato · versione {LINUX_VERSION}',
                        'available': f'Disponibile la versione {latest} (hai la {LINUX_VERSION})',
                        'checking': 'Controllo in corso…'}.get(state, 'Stato aggiornamenti sconosciuto'))

    async def check_updates(self, manual=False):
        if self.update['state'] == 'checking':
            return
        previous = self.update['state']
        self.update['state'] = 'checking'
        if manual:
            self.session.message = 'Controllo aggiornamenti…'
        self.render()
        try:
            state, release = await asyncio.to_thread(linux_updater.check, LINUX_VERSION)
            self.update = {'state': state, 'latest': release['version'], 'release': release}
            if manual or state == 'available':
                self.session.message = (f'Disponibile la versione {release["version"]}: clicca il pallino in alto.'
                                        if state == 'available' else f'Sei aggiornato: versione {LINUX_VERSION}.')
        except Exception as error:  # a failed check must never disturb the panel
            self.update['state'] = previous if previous != 'checking' else 'unknown'
            if manual:
                self.session.message = str(error) if isinstance(error, UpdateError) else f'Controllo non riuscito: {error}'
        if not self.closed:
            self.render()

    def skin_options(self):
        return [ft.DropdownOption(key=k, text=self.tr(skin_label(k))) for k in SKINS]

    def reload_mod_skins(self):
        register_mod_skins(mods.installed(self.mods_dir))
        self.skin_choice.options = self.skin_options()
        if self.skin not in SKINS:
            self.skin_choice.value = DEFAULT_SKIN
            self.skin_changed()
        self.page.update()

    def settings_menu(self, e=None):
        if self.session.state in ACTIVE or self.dialog_open:
            return
        self.page.show_dialog(self.settings_dialog())

    def reopen_settings(self):
        self.page.pop_dialog()
        self.page.show_dialog(self.settings_dialog())

    def settings_dialog(self):
        close_switch = ft.Switch(value=bool(self.settings.get('close_to_tray')), on_change=self.close_to_tray_changed,
                                 disabled=not (self.tray and self.tray.registered))
        tray_hint = ('La X nasconde il pannello nell’area di notifica' if self.tray and self.tray.registered
                     else 'Non disponibile: questo desktop non ha un’area di notifica')
        rows = []
        for info in mods.installed(self.mods_dir):
            name = 'mod:' + info.id
            actions = []
            if info.kind == 'theme':
                actions.append(self.button('In uso' if self.skin == name else 'Usa tema',
                                           lambda e, n=name: self.use_mod_theme(n), height=44,
                                           color=self.colors['play'] if self.skin == name else None))
            actions.append(self.button('Rimuovi', lambda e, i=info: self.remove_mod(i), height=44))
            kind = 'Tema' if info.kind == 'theme' else 'Raccolta di macro'
            rows.append(self.card(ft.Column([
                self.text(info.name, 18, True),
                self.text(f'{kind} · v{info.version} · di {info.author}', 14, muted=True),
                ft.Row(actions, wrap=True)], spacing=8)))
        if not rows:
            rows.append(self.text('Nessuna mod installata.', 16, muted=True))
        return ft.AlertDialog(
            title=self.text('Impostazioni e mod', 22, True),
            content=ft.Container(ft.Column([
                ft.Row([ft.Column([self.text('Chiudi nel tray', 18, True), self.text(tray_hint, 14, muted=True)],
                                  expand=True), close_switch]),
                ft.Divider(color=self.colors['border']),
                self.text('Mod: pacchetti .mmmod di soli dati (temi e macro), senza codice.', 14, muted=True),
                *rows,
                ft.Row([self.button('Installa da file…', self.install_mod, icon=ft.Icons.ADD, height=44),
                        self.button('Apri cartella mod', self.open_mods_folder, icon=ft.Icons.FOLDER_OPEN, height=44)],
                       wrap=True),
            ], tight=True, spacing=12, scroll=ft.ScrollMode.AUTO), width=520),
            actions=[self.button('Chiudi', lambda e: self.page.pop_dialog())])

    def close_to_tray_changed(self, e=None):
        self.settings['close_to_tray'] = bool(e.control.value)
        write_settings(self.path, self.settings)
        if self.tray:
            self.tray.refresh()

    def use_mod_theme(self, name):
        self.skin_choice.value = name
        self.skin_changed()
        self.reopen_settings()

    def open_mods_folder(self, e=None):
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(['xdg-open', str(self.mods_dir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as error:
            self.session.error(error)

    def remove_mod(self, info):
        def confirmed(e=None):
            try:
                if self.skin == 'mod:' + info.id:
                    self.skin_choice.value = DEFAULT_SKIN
                    self.skin_changed()
                mods.remove(self.mods_dir, info.id)
                self.reload_mod_skins()
            except mods.ModError as error:
                self.session.error(error)
            self.reopen_settings()
        self.page.pop_dialog()
        self.page.show_dialog(ft.AlertDialog(
            title=self.text(f'Rimuovere «{info.name}»?', 20, True),
            actions=[self.button('Annulla', lambda e: self.reopen_settings()),
                     self.button('Rimuovi', confirmed, self.colors['record'])]))

    async def install_mod(self, e=None):
        self.dialog_open = True
        try:
            files = await self.picker.pick_files(dialog_title=self.tr('Installa mod'), allow_multiple=False,
                                                 file_type=ft.FilePickerFileType.CUSTOM,
                                                 allowed_extensions=['mmmod'])
            if not (files and files[0].path):
                return
            path = files[0].path
            info = await asyncio.to_thread(mods.inspect, path)
        except mods.ModError as error:
            self.page.pop_dialog()
            self.page.show_dialog(ft.AlertDialog(
                title=self.text('Mod non installabile', 20, True), content=self.text(str(error), 16),
                actions=[self.button('OK', lambda e: self.reopen_settings())]))
            return
        except Exception as error:
            self.session.error(error)
            return
        finally:
            self.dialog_open = False
        async def go(e=None):
            try:
                if self.skin == 'mod:' + info.id:
                    self.skin_choice.value = DEFAULT_SKIN
                    self.skin_changed()
                await asyncio.to_thread(mods.install, path, self.mods_dir)
                self.reload_mod_skins()
            except (mods.ModError, OSError) as error:
                self.session.error(error)
            self.reopen_settings()
        lines = [self.text('• ' + line, 15) for line in info.summary()]
        self.page.pop_dialog()
        self.page.show_dialog(ft.AlertDialog(
            title=self.text(f'Installare «{info.name}» {info.version}?', 20, True),
            content=ft.Container(ft.Column([self.text(f'di {info.author}', 15, muted=True), *lines,
                                            self.text(f'SHA-256: {info.sha256[:16]}…', 14, muted=True),
                                            self.text('Installa solo mod di cui ti fidi.', 14, muted=True)],
                                           tight=True, spacing=6), width=480),
            actions=[self.button('Annulla', lambda e: self.reopen_settings()),
                     self.button('Installa', go, self.colors['play'])]))

    # System tray (StatusNotifierItem): present on KDE and on GNOME with AppIndicator, absent in game mode.
    def tray_items(self):
        Item = linux_tray.Item
        visible = self.page.window.visible is not False
        return [Item(1, self.tr('Nascondi pannello' if visible else 'Mostra pannello'), 'toggle'), Item(2, None),
                Item(3, self.tr('Registra · F9'), 'record'), Item(4, self.tr('Riproduci · F10'), 'play'),
                Item(5, self.tr('Ferma tutto · Ctrl+Alt+F11'), 'emergency'), Item(6, None),
                Item(7, self.tr('Impostazioni e mod…'), 'settings'),
                Item(8, self.tr('Chiudi nel tray'), 'close_to_tray', checked=bool(self.settings.get('close_to_tray'))),
                Item(9, None), Item(10, self.tr('Esci'), 'quit')]

    def start_tray(self):
        if self.preview or os.environ.get('MOUSE_MACRO_NO_TRAY'):
            return
        assets = Path(__file__).resolve().parent / 'assets'
        tray = linux_tray.LinuxTray('Mouse Macro Stocazz Superpower', assets, 'icon', self.tray_items,
                                    self.tray_actions.put)
        if tray.start():
            self.tray = tray

    async def tray_action(self, name):
        if name == 'toggle':
            await self.toggle_window()
        elif name in ('record', 'play', 'emergency'):
            if name != 'record' and self.session.state in ACTIVE:
                self.session.request_stop()
            await self.dispatch(name)
        elif name == 'settings':
            self.page.window.visible = True
            self.page.update()
            self.settings_menu()
        elif name == 'close_to_tray':
            self.settings['close_to_tray'] = not self.settings.get('close_to_tray')
            write_settings(self.path, self.settings)
        elif name == 'quit':
            await self.close_window()

    async def toggle_window(self):
        show = self.page.window.visible is False
        self.page.window.visible = show
        if show:
            self.page.window.minimized = False
            await self.page.window.to_front()
        self.page.update()

    def update_menu(self, e=None):
        if self.session.state in ACTIVE or self.dialog_open:
            return
        available = self.update['state'] == 'available'
        startup = ft.Switch(value=self.settings.get('check_updates', True), on_change=self.startup_check_changed)
        async def check_now(e=None):
            self.page.pop_dialog()
            await self.check_updates(manual=True)
        async def install(e=None):
            self.page.pop_dialog()
            await self.install_update()
        flatpak = linux_updater.in_flatpak()
        install_label = ('Flatpak: aggiorna dal gestore software o scarica il nuovo .flatpak' if flatpak and available else
                         f'Scarica e installa la versione {self.update["latest"]}' if available
                         else 'Nessun aggiornamento da installare')
        install_button = self.button(install_label, install, self.colors['play'] if available else None,
                                     ft.Icons.DOWNLOAD)
        install_button.disabled = not available or flatpak
        self.page.show_dialog(ft.AlertDialog(
            title=self.text('Aggiornamenti', 22, True),
            content=ft.Container(ft.Column([
                ft.Row([ft.Container(width=14, height=14, border_radius=7,
                                     bgcolor=self.colors[UPDATE_DOT.get(self.update['state'], 'border')]),
                        self.text(self.update_status(), 18, expand=True)]),
                self.button('Controlla ora', check_now, icon=ft.Icons.REFRESH),
                install_button,
                ft.Row([self.text('Controlla all’avvio', 18, expand=True), startup]),
            ], tight=True, spacing=14), width=480),
            actions=[self.button('Chiudi', lambda e: self.page.pop_dialog())]))

    def startup_check_changed(self, e=None):
        value = bool(e.control.value) if e is not None and getattr(e, 'control', None) is not None \
            else not self.settings.get('check_updates', True)
        self.settings['check_updates'] = value
        self.write_preferences()
        if self.session.message != 'Impossibile salvare le preferenze.':
            self.session.message = ('Controllo aggiornamenti all’avvio attivo.' if value
                                    else 'Controllo aggiornamenti all’avvio disattivato: nessun accesso alla rete.')
        self.render()

    async def install_update(self):
        release = self.update.get('release')
        if (self.update['state'] != 'available' or not release or self.session.state in ACTIVE
                or linux_updater.in_flatpak()):
            return
        self.dialog_open = True
        self.session.message = f'Scarico la versione {release["version"]}…'
        self.render()
        try:
            appimage = os.environ.get('APPIMAGE')
            if appimage and linux_updater.APPIMAGE.format(release['version']) in release.get('assets', {}):
                # Portable copy: replace the AppImage file itself, like the Windows portable ZIP.
                binary = await asyncio.to_thread(linux_updater.install_appimage, release, appimage)
            else:
                current = linux_updater.running_package()
                target = await asyncio.to_thread(linux_updater.install, release, None, None,
                                                 [current] if current else [])
                binary = target / linux_updater.BINARIES[1 if self.language == 'en' else 0]
        except Exception as error:
            self.dialog_open = False
            self.session.error(error if isinstance(error, UpdateError) else
                               f'Aggiornamento non riuscito: {error}')
            self.render()
            return
        self.dialog_open = False
        subprocess.Popen([str(binary), '--wait-for-exit', str(os.getpid())], cwd=str(Path(binary).parent),
                         start_new_session=True, close_fds=True)
        await self.close_window()

    def help(self,e=None):
        message=('F9: registra/ferma. F10: riproduci/ferma. Ctrl+Alt+F11: emergenza.\n\n'
                 'Su Linux i movimenti sono relativi: parti dalla stessa posizione del cursore e mantieni '
                 'scala e accelerazione del mouse. Cambia scheda invia Ctrl+Tab soltanto tra i giri.\n\n'
                 'Movimento umano (spento all’avvio): a ogni giro il percorso del cursore cambia un poco '
                 'e le pause variano; la somma degli spostamenti fra due clic resta identica, quindi i '
                 'clic cadono negli stessi punti se l’accelerazione del mouse è disattivata (profilo '
                 '“piatto”). Non rende invisibile l’automazione: controlla i termini del sito che usi.\n\n'
                 'Tastiera (spenta all’avvio): con «Registra anche la tastiera» i tasti digitati finiscono '
                 'nel file della macro in chiaro, password comprese; F9, F10 e F11 non vengono registrati. '
                 'Il permesso di lettura della tastiera è lo stesso già usato per F9/F10. '
                 'Salva avviabile crea uno script .sh e un .mmr: lo script apre Mouse Macro con la macro '
                 'caricata, poi premi F10.\n\n'
                 'Su molti desktop Ctrl+Alt+F11 passa anche a una console di testo: la macro si ferma '
                 'comunque; torna al desktop con Ctrl+Alt+F1, F2 o F7. Ctrl+Maiusc+F11 ferma tutto '
                 'senza cambiare console.\n\n'
                 'Servono accesso al mouse e, per i tasti globali, alla tastiera. Se in alto compare '
                 'Concedi accesso, premilo: il sistema chiede la password una volta e installa una regola '
                 'udev che vale solo per chi è seduto alla sessione locale. Senza quel pulsante (Flatpak) '
                 'esegui una volta da terminale setup-linux-input.sh dalla pagina del progetto, poi esci, '
                 'rientra e aggiorna l’elenco. Non eseguire tutta l’app come root.')
        if self.language=='en':
            message=('F9 records/stops; F10 plays/stops; Ctrl+Alt+F11 stops immediately.\n\n'
                     'Linux uses relative movements. Start from the same cursor position; keep mouse '
                     'acceleration and display scale unchanged. Next tab sends Ctrl+Tab only between cycles.\n\n'
                     'Human-like movement (off at launch) slightly changes the cursor path and the pauses '
                     'every cycle; the sum of the movements between two clicks stays identical, so clicks '
                     'land on the same spots when mouse acceleration is off (flat profile). It does not '
                     'hide automation: check the terms of the site you use.\n\n'
                     'Keyboard (off at launch): with “Record the keyboard too” typed keys are stored in the macro '
                     'file in plain text, passwords included; F9, F10 and F11 are not recorded. Reading the '
                     'keyboard uses the same permission already needed for F9/F10. Save launchable writes a .sh '
                     'script and a .mmr: the script opens Mouse Macro with the macro loaded, then press F10.\n\n'
                     'On many desktops Ctrl+Alt+F11 also switches to a text console: playback stops anyway; '
                     'return with Ctrl+Alt+F1, F2 or F7. Ctrl+Shift+F11 stops without switching console.\n\n'
                     'Mouse access and keyboard access for global shortcuts are required. If Grant access '
                     'appears at the top, press it: the system asks for your password once and installs a udev '
                     'rule that only applies to the user at the local session. Without that button (Flatpak) run '
                     'setup-linux-input.sh from the project page once in a terminal, then log in again and '
                     'refresh devices. Do not run the entire app as root.')
        self.page.show_dialog(ft.AlertDialog(title=self.text('Guida',22,True),
            content=ft.Container(ft.Column([self.text(message,16)],scroll=ft.ScrollMode.AUTO,tight=True),width=520),
            actions=[self.button('OK',lambda e:self.page.pop_dialog())]))

    async def window_event(self,e):
        if e.type==ft.WindowEventType.CLOSE:
            if self.settings.get('close_to_tray') and self.tray and self.tray.registered:
                self.remember_window()
                write_settings(self.path, self.settings)
                self.page.window.visible = False  # hotkeys and tray icon stay active
                self.page.update()
                return
            await self.close_window()
        elif e.type in (ft.WindowEventType.MOVED, ft.WindowEventType.RESIZED) and not self.active_view:
            self.remember_window()
            write_settings(self.path, self.settings)

    async def close_window(self):
        self.remember_window()
        write_settings(self.path, self.settings)
        await self.disconnect()
        await self.page.window.destroy()

    async def disconnect(self,e=None):
        if self.closed:
            return
        self.closed=True
        self.session.request_stop()
        try:
            await asyncio.to_thread(self.session.close)
        finally:
            if self.tray:
                self.tray.stop()
            if self.hotkeys:
                await asyncio.to_thread(self.hotkeys.stop)


async def main(page,language='it',open_request=None):
    panel=LinuxPanel(page,language,open_request=open_request)
    await panel.start()


def wait_for_exit(pid, timeout=20.0):
    """After an update the new binary waits for the old instance to close."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        time.sleep(.2)
    return False


def run(language='it', argv=None):
    from macro.panel_model import config_dir
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) == 2 and argv[0] == '--self-test':
        from macro.diagnostics import linux_self_test
        raise SystemExit(linux_self_test(argv[1], language))
    if len(argv) == 2 and argv[0] == '--wait-for-exit' and argv[1].isdecimal():
        wait_for_exit(int(argv[1]))
    open_request = None
    if '--open' in argv:
        from macro.runner import parse_run_args
        try:
            open_request = parse_run_args(argv, '--open')
        except ValueError as error:
            save_error_log(config_dir(), f'Macro avviabile non valida: {error}', 'errore-avvio.log')
    def log_thread_error(args):
        save_error_log(config_dir(), ''.join(traceback.format_exception(args.exc_type, args.exc_value,
                                                                          args.exc_traceback)))
    threading.excepthook = log_thread_error
    if not linux_setup.has_display():
        # Without a graphical session Flet falls back to a web server and tries to
        # pip-install flet-web, which crashes inside the frozen binary: stop here.
        linux_setup.startup_failure(config_dir(), language, no_display=True)
        raise SystemExit(1)
    if os.environ.get('APPIMAGE'):
        # Portable copy: after the first double click it is also in the applications menu.
        linux_setup.integrate_appimage(os.environ['APPIMAGE'], Path(__file__).resolve().parent/'assets'/'icon.png')
    if os.environ.get('WAYLAND_DISPLAY'):
        # Flet treats a Linux session without DISPLAY as a headless server and
        # would open a web server; a pure Wayland desktop has a native window.
        import flet.app as flet_app
        flet_app.is_linux_server = lambda: False
    opened = threading.Event()
    async def start(page):
        opened.set()
        try:
            await main(page,language,open_request)
        except Exception:
            save_error_log(config_dir(), traceback.format_exc(), 'errore-avvio.log')
            raise
    try:
        ft.run(start,assets_dir=str(Path(__file__).resolve().parent/'assets'))
    except Exception:
        save_error_log(config_dir(), traceback.format_exc(), 'errore-avvio.log')
        linux_setup.startup_failure(config_dir(), language)
        raise
    if not opened.is_set():
        # The window process exited before connecting (e.g. a missing system library):
        # started with a double click, nothing would be visible at all.
        linux_setup.startup_failure(config_dir(), language)
        raise SystemExit(1)
