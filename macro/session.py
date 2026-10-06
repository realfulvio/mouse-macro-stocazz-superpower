"""Serialized recording/playback lifecycle shared by the native panel and tests."""
from __future__ import annotations

import threading
from enum import Enum
from .events import Macro, BUTTON_OF_DOWN, BUTTON_OF_UP
from .engine import play, PlaybackEnd, PlaybackOptions

VERSION = '1.0.0'


class State(Enum):
    READY = 'pronto'
    RECORDING = 'registrazione'
    PLAYING = 'riproduzione'
    STOPPING = 'arresto'
    ERROR = 'errore'
    CLOSED = 'chiuso'


def validate_gestures(events):
    held = set()
    for event in events:
        if event.kind in BUTTON_OF_DOWN:
            name = BUTTON_OF_DOWN[event.kind]
            if name in held:
                raise ValueError('La macro contiene una pressione duplicata. Registra di nuovo.')
            held.add(name)
        elif event.kind in BUTTON_OF_UP:
            name = BUTTON_OF_UP[event.kind]
            if name not in held:
                raise ValueError('La macro contiene un rilascio senza pressione. Registra di nuovo.')
            held.remove(name)
    if held:
        raise ValueError('Registrazione fermata con un pulsante premuto. Registra di nuovo il gesto completo.')
    if not any(e.kind in BUTTON_OF_DOWN or e.kind == 'wheel' for e in events):
        raise ValueError('Nessun clic o rotella nella macro. Registra i gesti del mouse.')


class Session:
    def __init__(self, recorder_factory, player_factory, notify=lambda: None, screen=lambda: []):
        self.recorder_factory = recorder_factory
        self.player_factory = player_factory
        self.notify = notify
        self.screen = screen
        self.state = State.READY
        self.message = 'Registra i gesti del mouse.'
        self.macro = Macro('windows')
        self.stop_event = threading.Event()
        self.recorder = None
        self.worker = None
        self.player = None
        self.lock = threading.RLock()
        self.completed = 0
        self.target = ''
        self.last_trace = []

    def error(self, error):
        with self.lock:
            if self.state == State.CLOSED:
                return
            self.state = State.ERROR
            self.message = str(error)
        self.notify()

    def toggle_record(self):
        with self.lock:
            if self.state in (State.PLAYING, State.STOPPING, State.CLOSED) or (self.worker and self.worker.is_alive()):
                return
            if self.state != State.RECORDING:
                try:
                    recorder = self.recorder_factory()
                    recorder.start()
                except Exception as error:
                    self.error(error)
                    return
                self.recorder = recorder
                self.state = State.RECORDING
                self.message = 'Esegui i gesti del mouse, poi F9.'
            else:
                self.state = State.STOPPING
                recorder = self.recorder
                try:
                    events = recorder.stop()
                    if getattr(recorder, 'error', ''):
                        raise ValueError(recorder.error)
                    validate_gestures(events)
                    # Remove only the initial idle cursor path, never a drag or
                    # an arbitrary suffix; app gestures were excluded at source.
                    first = next(i for i, e in enumerate(events) if e.kind in BUTTON_OF_DOWN or e.kind == 'wheel')
                    events = events[first:]
                    base = events[0].t
                    for event in events:
                        event.t -= base
                    self.macro = Macro('windows', events, self.screen(), getattr(recorder, 'layout', {}))
                    self.state = State.READY
                    self.message = 'Macro pronta. Ripristina lo stato iniziale, poi F10.'
                except Exception as error:
                    self.error(error)
                finally:
                    self.recorder = None
        self.notify()

    def toggle_play(self, options: PlaybackOptions, next_tab=True, preflight=lambda macro: None):
        with self.lock:
            if self.state in (State.PLAYING, State.STOPPING):
                self.request_stop()
                return
            if self.state in (State.RECORDING, State.CLOSED):
                return
            if self.worker and self.worker.is_alive():
                return
            player = None
            try:
                validate_gestures(self.macro.events)
                preflight(self.macro)
                player = self.player_factory()
                # Mouse macros may span applications, browser chrome and the desktop.
                # Do not bind playback to a browser or a single foreground window.
                target = 'Mouse'
                if options.repeat_count is None or not 1 <= options.repeat_count <= 999:
                    raise ValueError('Imposta da 1 a 999 ripetizioni.')
            except Exception as error:
                if player:
                    player.close()
                self.error(error)
                return
            self.stop_event = threading.Event()
            self.player = player
            self.state = State.PLAYING
            self.target = target
            self.completed = 0
            self.last_trace = []
            self.message = f'{target}: giro 1/{options.repeat_count}'
            events = list(self.macro.events)
            self.worker = threading.Thread(target=self._run, args=(events, options, next_tab), name='macro-player')
            self.worker.start()
        self.notify()

    def _run(self, events, options, next_tab):
        end, error = PlaybackEnd.STOPPED, None
        player, stop = self.player, self.stop_event
        def progress(status):
            with self.lock:
                self.completed = status.completed_loops
                if self.state == State.PLAYING:
                    self.message = f'{self.target}: {self.completed}/{options.repeat_count} completati'
            self.notify()
        try:
            end = play(events, options, player.apply_event, player.release_held, progress, stop,
                       between_cycles=(lambda: player.next_tab(stop)) if next_tab else None,
                       trace=self.last_trace.append)
        except Exception as caught:
            error = caught
            self.last_trace.append({'type':'error', 'exception':type(caught).__name__, 'message':str(caught)})
        finally:
            try:
                player.close()
            except Exception as caught:
                error = error or caught
            with self.lock:
                self.player = None
                if self.state != State.CLOSED:
                    self.state = State.ERROR if error else State.READY
                    self.message = (str(error) if error else
                                    'Fermato. Controlla la pagina prima di ripartire.' if end == PlaybackEnd.STOPPED else
                                    f'Completati {self.completed} giri.')
            self.notify()

    def request_stop(self):
        # Event.set is safe and immediate even when the UI queue is busy.
        self.stop_event.set()
        with self.lock:
            if self.state == State.PLAYING:
                self.state = State.STOPPING
                self.message = 'Arresto in corso…'
        self.notify()

    def load(self, path):
        with self.lock:
            if self.state not in (State.READY, State.ERROR):
                return False
            try:
                candidate = Macro.load(str(path))
                if candidate.platform != 'windows':
                    raise ValueError('Questa macro è Linux. Registra una macro Windows.')
                validate_gestures(candidate.events)
            except Exception as error:
                self.error(error)
                return False
            self.macro = candidate
            self.state = State.READY
            self.message = 'Macro caricata. Ripristina lo stato iniziale e premi F10.'
        self.notify()
        return True

    def save(self, path):
        with self.lock:
            if self.state not in (State.READY, State.ERROR):
                return False
            try:
                validate_gestures(self.macro.events)
                self.macro.save(str(path))
            except Exception as error:
                self.error(error)
                return False
            self.message = 'Macro salvata.'
        self.notify()
        return True

    def close(self):
        self.stop_event.set()
        with self.lock:
            self.state = State.CLOSED
            recorder = self.recorder
            self.recorder = None
            worker = self.worker
        if recorder:
            recorder.stop()
        if worker and worker is not threading.current_thread():
            worker.join(timeout=2)
            if worker.is_alive():
                raise RuntimeError('Il player non si è arrestato entro 2 secondi.')
