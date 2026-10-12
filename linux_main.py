"""Readable Linux desktop panel using the same lifecycle and timing as Windows."""
from __future__ import annotations

import asyncio
from pathlib import Path
import queue
import threading
import time

import flet as ft

from macro import updater
from macro.engine import LoopMode
from macro.linux_backend import LinuxRecorder, LinuxPlayer, GlobalHotkeys, list_mice
from macro.panel_model import (SKINS, parse_repeats, playback_options, settings_path,
                               read_settings, write_settings)
from macro.session import Session, State, VERSION, validate_gestures

ACTIVE = (State.RECORDING, State.PLAYING, State.STOPPING)
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
    'Pause variabili': 'Vary pauses', 'Varia le pause, conserva i movimenti': 'Varies pauses; keeps movements',
    'Skin': 'Skin', 'Unicorno': 'Unicorn', 'Palio': 'Palio',
    'Modalità': 'Mode', 'N volte': 'Repeat count', 'Infinito': 'Unlimited',
    'Durata in minuti': 'Duration in minutes', 'Doppio clic (ms)': 'Double click (ms)',
    'Controlla aggiornamenti': 'Check updates', 'Torna al pannello': 'Back to panel',
    'Permessi mouse insufficienti. Vedi la Guida e aggiorna l’elenco.':
        'Mouse access denied. See Help, then refresh devices.',
}


def duration_text(seconds):
    return f'{int(seconds)//60:02d}:{int(seconds)%60:02d}'


class LinuxPanel:
    def __init__(self, page, language='it', preferences=None, preview=False):
        self.page, self.language, self.preview = page, language, preview
        self.path = Path(preferences) if preferences else settings_path()
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
        self.session = Session(self.make_recorder, LinuxPlayer, self.dirty.set, platform='linux')
        self.page.title = f'Mouse Macro {VERSION} · Linux · hcok'
        self.page.fonts = {'Outfit': 'fonts/Outfit.ttf'}
        self.page.theme = ft.Theme(font_family='Outfit', color_scheme_seed=self.colors['play'])
        self.page.theme_mode = ft.ThemeMode.DARK if self.skin == 'unicorno' else ft.ThemeMode.LIGHT
        self.page.padding = 16
        self.page.bgcolor = self.colors['background']
        self.page.window.width, self.page.window.height = 440, 800
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
        if self.language != 'en':
            return text
        from localization import translate
        return EN.get(text, translate(text, 'en'))

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
        self.status_card = self.card(ft.Column([
            ft.Row([ft.Column([ft.Row([self.dot, self.status]), self.message], expand=True), self.mascot]),
            ft.Row([ft.Column([self.text('Eventi',16,muted=True), self.event_count], expand=True),
                    ft.Column([self.text('Durata',16,muted=True), self.duration], expand=True)]),
        ], spacing=14))
        self.record = self.button('Registra', self.record_clicked, self.colors['record'],
                                  ft.Icons.FIBER_MANUAL_RECORD, tooltip='F9')
        self.play = self.button('Riproduci', self.play_clicked, self.colors['play'],
                                ft.Icons.PLAY_ARROW_ROUNDED, tooltip='F10')
        self.record.height = self.play.height = 64
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
        self.speed = 1.0
        self.next_tab = ft.Switch(value=False, on_change=self.option_changed)
        self.slow = ft.Switch(value=False, on_change=self.option_changed)
        self.varied = ft.Switch(value=False, on_change=self.option_changed)
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
        self.update_button = self.button('Controlla aggiornamenti', self.check_update, icon=ft.Icons.SYSTEM_UPDATE)
        self.options = self.card(ft.Column([
            self.text('Opzioni',24,True), self.preset, self.text('Velocità',18,True),
            ft.Row([self.normal,self.rapid]),
            setting('Cambia scheda','Ctrl+Tab tra un giro e l’altro',self.next_tab),
            setting('Pagine lente','Aggiunge pause tra i clic',self.slow),
            setting('Pause variabili','Varia le pause, conserva i movimenti',self.varied),
            ft.Divider(color=self.colors['border']), self.mode,self.minutes,self.double_click,
            self.skin_choice,self.update_button,
        ],spacing=16,scroll=ft.ScrollMode.AUTO),expand=True,visible=False)
        self.main_column = ft.Column([
            ft.Column([self.text('Mouse Macro',24,True),self.text('Stocazz Superpower',18,muted=True)]),
            self.status_card,self.record,self.play,
            self.card(ft.Row([self.text('Ripetizioni',18,True,expand=True),self.minus,self.repeat,self.plus])),
            ft.Row([self.save,self.load]), self.option_button,self.mouse,self.refresh,self.device_hint,
        ],spacing=12,expand=True,scroll=ft.ScrollMode.AUTO)
        self.normal_view = ft.Row([self.main_column,self.options],spacing=16,expand=True)
        self.activity_status = self.text('Registrazione',22,True)
        self.activity_count = self.text('',16,muted=True)
        self.stop = self.button('Stop',self.stop_clicked,self.colors['record'],ft.Icons.STOP_ROUNDED,width=120)
        self.progress = ft.ProgressBar(value=0,color=self.colors['play'],bgcolor=self.colors['border'],visible=False)
        self.activity_view = ft.Column([
            ft.Row([ft.Column([self.activity_status,self.activity_count],expand=True),self.stop]),self.progress,
        ],spacing=10,visible=False)
        self.footer = ft.Row([
            self.button('Guida',self.help,icon=ft.Icons.HELP_OUTLINE),
            self.button('Emergenza',self.emergency,icon=ft.Icons.WARNING_AMBER_ROUNDED,expand=True,
                        tooltip='Ctrl+Alt+F11'),
        ])
        self.shortcut_hint = self.text('F9 · F10 · Ctrl+Alt+F11',16,muted=True)
        self.root = ft.Column([self.normal_view,self.activity_view,self.footer,self.shortcut_hint],
                              spacing=12,expand=True)

    def valid_macro(self):
        try:
            validate_gestures(self.session.macro.events)
            return True
        except ValueError:
            return False

    def render(self):
        state = self.session.state
        active = state in ACTIVE
        if active != self.active_view:
            self.active_view = active
            self.page.window.min_height = 190 if active else 380
            self.page.window.width = 520 if active else 840 if self.expanded else 440
            self.page.window.height = 210 if active else 800
            self.started = time.monotonic() if active else None
        label = {State.READY:'Pronto',State.RECORDING:'Registrazione',State.PLAYING:'Riproduzione',
                 State.STOPPING:'Arresto…',State.ERROR:'Errore',State.CLOSED:'Pronto'}[state]
        self.status.value = self.activity_status.value = self.tr(label)
        self.message.value = self.tr(self.session.message)
        self.dot.bgcolor = self.colors['record' if state==State.RECORDING else 'play' if active else
                                       'error' if state==State.ERROR else 'ready']
        horse_state = 'registrazione' if state==State.RECORDING else 'riproduzione' if active else 'errore' if state==State.ERROR else 'pronto'
        self.mascot.content = self.horse(horse_state)
        recorder = self.session.recorder
        count = recorder.current_event_count if recorder and state==State.RECORDING else len(self.session.macro.events)
        seconds = (time.monotonic()-self.started if active and self.started else
                   self.session.macro.events[-1].t if self.session.macro.events else 0)
        self.event_count.value,self.duration.value = str(count),duration_text(seconds)
        self.activity_count.value = (f'{count} {"events" if self.language=="en" else "eventi"} · {duration_text(seconds)}'
                                    if state==State.RECORDING else self.tr(self.session.message))
        self.normal_view.visible,self.activity_view.visible = not active,active
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
        self.page.update()

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
        self.render()

    async def pump(self):
        while not self.closed:
            while not self.commands.empty():
                command = self.commands.get()
                if not self.dialog_open or command=='emergency':
                    await self.dispatch(command)
            if self.dirty.is_set() or self.session.state in ACTIVE:
                self.dirty.clear()
                self.render()
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
        command = 'emergency' if e.key=='F11' and e.ctrl and e.alt else {'F9':'record','F10':'play'}.get(e.key)
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
                    options = playback_options(self.repeat.value,self.speed,self.slow.value,self.varied.value,
                                               self.mode.value,self.minutes.value,self.double_click.value)
                    await asyncio.to_thread(self.session.toggle_play,options,self.next_tab.value)
            elif command=='emergency':
                self.session.request_stop()
                if self.session.state==State.RECORDING:
                    await asyncio.to_thread(self.session.toggle_record,mouse_stop)
        except (OSError,ValueError) as error:
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

    def mode_changed(self,e=None):
        self.minutes.visible=self.mode.value=='duration'
        self.render()

    def toggle_options(self,e=None):
        self.expanded=not self.expanded
        self.page.window.width=840 if self.expanded else 440
        self.render()

    def mouse_changed(self,e=None):
        self.settings['device']=self.mouse.value
        self.preference_changed()

    def preference_changed(self,e=None):
        self.settings['double_click_ms']=self.double_click.value
        if not write_settings(self.path,self.settings):
            self.session.message='Impossibile salvare le preferenze.'
        self.render()

    def skin_changed(self,e=None):
        self.skin=self.skin_choice.value
        self.settings['skin']=self.skin
        write_settings(self.path,self.settings)
        # Rebuild controls together so a skin cannot leave mixed colors behind.
        repeats,mode,minutes=self.repeat.value,self.mode.value,self.minutes.value
        speed,next_tab,slow,varied=self.speed,self.next_tab.value,self.slow.value,self.varied.value
        self.colors=SKINS[self.skin]
        self.page.bgcolor=self.colors['background']
        self.page.theme_mode=ft.ThemeMode.DARK if self.skin=='unicorno' else ft.ThemeMode.LIGHT
        self.page.theme=ft.Theme(font_family='Outfit',color_scheme_seed=self.colors['play'])
        self.build()
        self.repeat.value,self.mode.value,self.minutes.value=repeats,mode,minutes
        self.speed,self.next_tab.value,self.slow.value,self.varied.value=speed,next_tab,slow,varied
        self.minutes.visible=mode=='duration'
        self.mouse.options=[ft.DropdownOption(key=p,text=n) for p,n in self.devices]
        self.mouse.value=self.settings.get('device')
        self.page.controls.clear()
        self.page.add(self.root)
        self.render()

    async def refresh_devices(self,e=None):
        self.devices=await asyncio.to_thread(list_mice)
        self.mouse.options=[ft.DropdownOption(key=p,text=n) for p,n in self.devices]
        paths={p for p,n in self.devices}
        if self.mouse.value not in paths:
            self.mouse.value=self.devices[0][0] if self.devices else None
        self.device_hint.value=('Parti sempre dalla stessa posizione del cursore.' if self.devices else
                                self.tr('Permessi mouse insufficienti. Vedi la Guida e aggiorna l’elenco.'))
        if self.language=='en' and self.devices:
            self.device_hint.value='Start from the same cursor position each time.'
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

    async def check_update(self,e=None):
        try:
            release=await asyncio.to_thread(updater.fetch_latest)
            linux=[name for name in release['assets'] if 'Linux' in name]
            self.session.message=(f'Release {release["version"]}: consulta i pacchetti Linux su GitHub.' if linux else
                                  'La release corrente su GitHub non contiene un pacchetto Linux aggiornato.')
        except updater.UpdateError as error:
            self.session.message=str(error)
        self.render()

    def help(self,e=None):
        message=('F9: registra/ferma. F10: riproduci/ferma. Ctrl+Alt+F11: emergenza.\n\n'
                 'Su Linux i movimenti sono relativi: parti dalla stessa posizione del cursore e mantieni '
                 'scala e accelerazione del mouse. Cambia scheda invia Ctrl+Tab soltanto tra i giri.\n\n'
                 'Pause variabili cambia soltanto i tempi; non altera i percorsi.\n\n'
                 'Servono accesso al mouse e, per i tasti globali, alla tastiera. La configurazione '
                 'mirata è in scripts/setup-linux-input.sh; dopo il login aggiorna l’elenco. '
                 'Non eseguire tutta l’app come root.')
        if self.language=='en':
            message=('F9 records/stops; F10 plays/stops; Ctrl+Alt+F11 stops immediately.\n\n'
                     'Linux uses relative movements. Start from the same cursor position; keep mouse '
                     'acceleration and display scale unchanged. Next tab sends Ctrl+Tab only between cycles.\n\n'
                     'Vary pauses changes timing only. Mouse access and keyboard access for global shortcuts '
                     'are required. See scripts/setup-linux-input.sh, then log in again and refresh devices. '
                     'Do not run the entire app as root.')
        self.page.show_dialog(ft.AlertDialog(title=self.text('Guida',22,True),
            content=ft.Container(self.text(message,16),width=520),
            actions=[self.button('OK',lambda e:self.page.pop_dialog())]))

    async def window_event(self,e):
        if e.type==ft.WindowEventType.CLOSE:
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


def run(language='it'):
    async def start(page):
        await main(page,language)
    ft.run(start,assets_dir=str(Path(__file__).resolve().parent/'assets'))
