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

from macro import linux_updater
from macro.updater import UpdateError
from macro.linux_backend import LinuxRecorder, LinuxPlayer, GlobalHotkeys, list_mice, mouse_models
from macro.mouse_devices import mouse_label
from macro.panel_model import (LINUX_VERSION, SKINS, UPDATE_DOT, parse_repeats, playback_options,
                               settings_path, read_settings, write_settings, save_replay_trace,
                               save_error_log)
from macro.session import Session, State, validate_gestures

ACTIVE = (State.RECORDING, State.PLAYING, State.STOPPING)
NORMAL_SIZE = (440, 800)
EXPANDED_WIDTH = 840
ACTIVE_SIZE = (440, 132)  # compact bar while recording or playing
ACTIVE_OPACITY = 0.95     # like the Windows bar: slightly see-through
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
    (r'Mouse rilevati: (.+)', r'Mice detected: \1'),
    (r'Mouse: modello non disponibile', r'Mouse: model unavailable'),
]


def duration_text(seconds):
    return f'{int(seconds)//60:02d}:{int(seconds)%60:02d}'


class LinuxPanel:
    def __init__(self, page, language='it', preferences=None, preview=False):
        self.page, self.language, self.preview = page, language, preview
        self.path = Path(preferences) if preferences else settings_path()
        self.folder = self.path.parent  # diagnostics live next to the preferences
        self.settings = read_settings(self.path)
        self.skin = self.settings.get('skin', 'unicorno')
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
        self.speed = 1.0
        self.update = {'state': 'unknown', 'latest': None, 'release': None}
        self.last_options = None
        self.trace_saved = None
        self.session = Session(self.make_recorder, LinuxPlayer, self.dirty.set, platform='linux')
        self.page.title = f'Mouse Macro {LINUX_VERSION} · Linux · hcok'
        self.page.fonts = {'Outfit': 'fonts/Outfit.ttf'}
        self.page.theme = ft.Theme(font_family='Outfit', color_scheme_seed=self.colors['play'])
        self.page.theme_mode = ft.ThemeMode.DARK if self.skin == 'unicorno' else ft.ThemeMode.LIGHT
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
        return ft.Button(content=self.text(label, 18, True), icon=icon, on_click=handler,
                         bgcolor=color or self.colors['surface'], color=self.colors['text'],
                         height=52, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                         **kwargs)

    def card(self, control, **kwargs):
        return ft.Container(content=control, padding=16, bgcolor=self.colors['surface'],
                            border=ft.Border.all(1, self.colors['border']), border_radius=14, **kwargs)

    def horse(self, state='pronto', size=72):
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

    def build(self):
        self.status = self.text('Pronto', 26, True)
        self.message = self.text(self.session.message, 16, muted=True)
        self.event_count, self.duration = self.text('0', 22, True), self.text('00:00', 22, True)
        self.mascot = ft.Container(self.horse())
        self.dot = ft.Container(width=12, height=12, border_radius=6, bgcolor=self.colors['ready'])
        self.mouse_model = self.text(self.mouse_text(), 16, muted=True)
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
        self.normal = self.button('Normale', lambda e:self.set_speed(1.0), expand=True)
        self.rapid = self.button('Rapida 2×', lambda e:self.set_speed(2.0), expand=True)
        self.next_tab = ft.Switch(value=False, on_change=self.option_changed)
        self.slow = ft.Switch(value=False, on_change=self.option_changed)
        self.human = ft.Switch(value=False, on_change=self.human_changed)
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
                                       options=[ft.DropdownOption(key=k,text=self.tr(v)) for k,v in
                                                [('unicorno','Unicorno'),('palio','Palio')]],
                                       on_select=self.skin_changed)
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
            ft.Divider(color=self.colors['border']), self.mode,self.minutes,self.double_click,
            self.skin_choice,self.update_button,
        ],spacing=16,scroll=ft.ScrollMode.AUTO),expand=True,visible=False)
        self.main_column = ft.Column([
            ft.Row([ft.Column([self.text('Mouse Macro',24,True),self.text('Stocazz Superpower',18,muted=True)],
                              expand=True), self.header_dot]),
            self.status_card,ft.Row([self.record]),ft.Row([self.play]),
            self.card(ft.Row([self.text('Ripetizioni',18,True,expand=True),self.minus,self.repeat,self.plus])),
            ft.Row([self.save,self.load]), self.mouse,self.refresh,self.device_hint,
        ],spacing=12,expand=True,scroll=ft.ScrollMode.AUTO)
        self.normal_view = ft.Row([self.main_column,self.options],spacing=16,expand=True)
        # Compact bar shown alone while recording or playing, as on Windows.
        self.activity_horse = ft.Container(self.horse('registrazione', 48))
        self.activity_status = self.text('Registrazione',22,True)
        self.activity_count = self.text('',18)
        self.activity_hint = self.text('',14,muted=True)
        self.stop = ft.Button(content=self.text('Stop',24,True), icon=ft.Icons.STOP_ROUNDED,
                              on_click=self.stop_clicked, bgcolor=self.colors['record'],
                              color=self.colors['text'], width=140, height=72,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)))
        self.progress = ft.ProgressBar(value=0,color=self.colors['play'],bgcolor=self.colors['border'],visible=False)
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
        if active:
            self.remember_window()
            window.min_height = 140
            window.width, window.height = ACTIVE_SIZE
            try:
                window.opacity = ACTIVE_OPACITY
            except (AttributeError, ValueError):
                pass
            self.started = time.monotonic()
        else:
            window.min_height = 380
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
        self.activity_horse.content = self.horse(horse_state, 48)
        self.activity_status.color = self.colors['record' if state==State.RECORDING else 'text']
        recorder = self.session.recorder
        count = recorder.current_event_count if recorder and state==State.RECORDING else len(self.session.macro.events)
        seconds = (time.monotonic()-self.started if active and self.started else
                   self.session.macro.events[-1].t if self.session.macro.events else 0)
        self.event_count.value,self.duration.value = str(count),duration_text(seconds)
        self.activity_count.value = self.activity_detail(state, count, seconds)
        self.activity_hint.value = ('F9 stop' if state==State.RECORDING else 'F10 stop · Ctrl+Alt+F11')
        self.mouse_model.value = self.mouse_text()
        self.normal_view.visible,self.activity_view.visible = not active,active
        self.footer.visible = self.shortcut_hint.visible = not active
        self.options.visible = self.expanded and not active
        self.record.disabled = active or self.dialog_open
        self.play.disabled = active or self.dialog_open or not self.valid_macro()
        self.save.disabled = active or self.dialog_open or not self.valid_macro()
        self.load.disabled = active or self.dialog_open
        self.stop.disabled = state==State.STOPPING
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
        return LinuxRecorder(self.mouse.value)

    async def start(self):
        await self.refresh_devices()
        self.hotkeys = GlobalHotkeys(self.hotkey)
        await asyncio.to_thread(self.hotkeys.start)
        if self.hotkeys.failed:
            self.shortcut_hint.value = ('Scorciatoie globali non disponibili: accesso tastiera necessario.'
                                        if self.language=='it' else 'Global shortcuts unavailable: keyboard access required.')
        self.page.run_task(self.pump)
        if self.settings.get('check_updates', True):
            self.page.run_task(self.check_updates)
        self.render()

    async def pump(self):
        while not self.closed:
            try:
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
        self.page.theme_mode=ft.ThemeMode.DARK if self.skin=='unicorno' else ft.ThemeMode.LIGHT
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

    async def refresh_devices(self,e=None):
        self.devices=await asyncio.to_thread(list_mice)
        self.models=await asyncio.to_thread(mouse_models)
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
        install_label = (f'Scarica e installa la versione {self.update["latest"]}' if available
                         else 'Nessun aggiornamento da installare')
        install_button = self.button(install_label, install, self.colors['play'] if available else None,
                                     ft.Icons.DOWNLOAD)
        install_button.disabled = not available
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
        if self.update['state'] != 'available' or not release or self.session.state in ACTIVE:
            return
        self.dialog_open = True
        self.session.message = f'Scarico la versione {release["version"]}…'
        self.render()
        try:
            current = linux_updater.running_package()
            target = await asyncio.to_thread(linux_updater.install, release, None, None,
                                             [current] if current else [])
        except Exception as error:
            self.dialog_open = False
            self.session.error(error if isinstance(error, UpdateError) else
                               f'Aggiornamento non riuscito: {error}')
            self.render()
            return
        self.dialog_open = False
        binary = target / linux_updater.BINARIES[1 if self.language == 'en' else 0]
        subprocess.Popen([str(binary), '--wait-for-exit', str(os.getpid())], cwd=str(target),
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
                 'Su molti desktop Ctrl+Alt+F11 passa anche a una console di testo: la macro si ferma '
                 'comunque; torna al desktop con Ctrl+Alt+F1, F2 o F7. Ctrl+Maiusc+F11 ferma tutto '
                 'senza cambiare console.\n\n'
                 'Servono accesso al mouse e, per i tasti globali, alla tastiera. La configurazione '
                 'mirata è in scripts/setup-linux-input.sh; dopo il login aggiorna l’elenco. '
                 'Non eseguire tutta l’app come root.')
        if self.language=='en':
            message=('F9 records/stops; F10 plays/stops; Ctrl+Alt+F11 stops immediately.\n\n'
                     'Linux uses relative movements. Start from the same cursor position; keep mouse '
                     'acceleration and display scale unchanged. Next tab sends Ctrl+Tab only between cycles.\n\n'
                     'Human-like movement (off at launch) slightly changes the cursor path and the pauses '
                     'every cycle; the sum of the movements between two clicks stays identical, so clicks '
                     'land on the same spots when mouse acceleration is off (flat profile). It does not '
                     'hide automation: check the terms of the site you use.\n\n'
                     'On many desktops Ctrl+Alt+F11 also switches to a text console: playback stops anyway; '
                     'return with Ctrl+Alt+F1, F2 or F7. Ctrl+Shift+F11 stops without switching console.\n\n'
                     'Mouse access and keyboard access for global shortcuts '
                     'are required. See scripts/setup-linux-input.sh, then log in again and refresh devices. '
                     'Do not run the entire app as root.')
        self.page.show_dialog(ft.AlertDialog(title=self.text('Guida',22,True),
            content=ft.Container(ft.Column([self.text(message,16)],scroll=ft.ScrollMode.AUTO,tight=True),width=520),
            actions=[self.button('OK',lambda e:self.page.pop_dialog())]))

    async def window_event(self,e):
        if e.type==ft.WindowEventType.CLOSE:
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
            if self.hotkeys:
                await asyncio.to_thread(self.hotkeys.stop)


async def main(page,language='it'):
    panel=LinuxPanel(page,language)
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
    def log_thread_error(args):
        save_error_log(config_dir(), ''.join(traceback.format_exception(args.exc_type, args.exc_value,
                                                                          args.exc_traceback)))
    threading.excepthook = log_thread_error
    if os.environ.get('WAYLAND_DISPLAY'):
        # Flet treats a Linux session without DISPLAY as a headless server and
        # would open a web server; a pure Wayland desktop has a native window.
        import flet.app as flet_app
        flet_app.is_linux_server = lambda: False
    async def start(page):
        try:
            await main(page,language)
        except Exception:
            save_error_log(config_dir(), traceback.format_exc(), 'errore-avvio.log')
            raise
    try:
        ft.run(start,assets_dir=str(Path(__file__).resolve().parent/'assets'))
    except Exception:
        save_error_log(config_dir(), traceback.format_exc(), 'errore-avvio.log')
        raise
