"""Motore di riproduzione generico: rispetta i tempi originali della registrazione con
precisione sub-millisecondo (attesa ibrida sleep + spin-wait) ed è indipendente dal
backend di sistema (Linux/Windows) usato per registrare e iniettare gli eventi.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

from .events import BUTTON_OF_DOWN, BUTTON_OF_UP, MacroEvent


class LoopMode(Enum):
    INFINITE = "infinite"
    REPEAT_COUNT = "repeat_count"
    DURATION = "duration"


@dataclass
class PlaybackOptions:
    mode: LoopMode = LoopMode.INFINITE
    repeat_count: int = 1
    duration_seconds: float = 60.0
    speed: float = 1.0
    # Le pause più lunghe di questa soglia (secondi) vengono considerate "attese reali"
    # (es. il tempo per cui, registrando, si è aspettato che una pagina web si caricasse)
    # e non vengono compresse dalla velocità oltre max_pause_speedup, per evitare che un
    # click parta prima che la pagina/finestra di destinazione sia pronta.
    pause_threshold_seconds: float = 0.35
    max_pause_speedup: float = 1.5
    # Durata minima (secondi) tra la pressione e il rilascio dello stesso tasto,
    # indipendentemente dalla velocità: evita che, accelerando la riproduzione, un
    # click diventi così breve da non essere più rilevato dall'applicazione di
    # destinazione (molti giochi/programmi campionano l'input a intervalli fissi).
    min_click_hold_seconds: float = 0.03


@dataclass
class PlaybackStatus:
    completed_loops: int
    elapsed_seconds: float


def _wait_until(deadline: Callable[[], float], stop_event: threading.Event) -> bool:
    """Attende con precisione sub-millisecondo fino all'istante target (in secondi,
    stessa base di time.perf_counter()). Ritorna False se interrotta da stop_event."""
    while True:
        remaining = deadline() - time.perf_counter()
        if remaining <= 0:
            return True
        if stop_event.is_set():
            return False
        if remaining > 0.003:
            time.sleep(remaining - 0.002)
        elif remaining > 0.00005:
            pass  # spin-wait: busy loop finale per la precisione
        else:
            return True


def _compute_scaled_times(events: list[MacroEvent], options: PlaybackOptions) -> list[float]:
    """Calcola per ogni evento l'istante (in secondi, relativo all'inizio di un ciclo)
    a cui va eseguito, applicando la velocità in modo "intelligente": gli intervalli
    brevi (gesti, movimenti) vengono scalati per intero dalla velocità scelta, mentre
    le pause più lunghe della soglia (verosimilmente attese per un caricamento pagina)
    vengono accelerate al massimo di max_pause_speedup, per non anticipare un click
    prima che la destinazione sia pronta.
    """
    speed = max(0.05, min(20.0, options.speed))
    scaled = [0.0]
    for i in range(1, len(events)):
        gap = events[i].t - events[i - 1].t
        effective_speed = min(speed, options.max_pause_speedup) if gap > options.pause_threshold_seconds else speed
        scaled.append(scaled[-1] + gap / effective_speed)
    _enforce_min_click_hold(events, scaled, options.min_click_hold_seconds)
    return scaled


def _enforce_min_click_hold(events: list[MacroEvent], scaled: list[float], min_hold: float) -> None:
    """Allunga, se necessario, la distanza tra un evento di pressione e il corrispondente
    rilascio dello stesso tasto fino a min_hold, spostando in avanti (in-place) quel
    rilascio e tutti gli eventi successivi. Così un click resta sempre "vedibile" da chi
    lo riceve, anche quando la velocità di riproduzione lo comprimerebbe sotto la soglia."""
    if min_hold <= 0:
        return
    down_time: dict[str, float] = {}
    shift = 0.0
    for i, evt in enumerate(events):
        scaled[i] += shift
        if evt.kind in BUTTON_OF_DOWN:
            down_time[BUTTON_OF_DOWN[evt.kind]] = scaled[i]
        elif evt.kind in BUTTON_OF_UP:
            t0 = down_time.pop(BUTTON_OF_UP[evt.kind], None)
            if t0 is not None and (scaled[i] - t0) < min_hold:
                extra = min_hold - (scaled[i] - t0)
                scaled[i] += extra
                shift += extra


def play(
    events: Iterable[MacroEvent],
    options: PlaybackOptions,
    apply_event: Callable[[MacroEvent], None],
    release_held: Callable[[set[str]], None],
    progress: Callable[[PlaybackStatus], None] | None,
    stop_event: threading.Event,
) -> None:
    """Riproduce la sequenza di eventi rispettando le opzioni di ripetizione/velocità.

    apply_event: esegue un singolo evento tramite il backend di sistema.
    release_held: rilascia i tasti eventualmente rimasti "premuti" se la riproduzione
                  viene interrotta a metà (evita di lasciare il mouse in uno stato bloccato).
    """
    events = list(events)
    if not events:
        return

    scaled_times = _compute_scaled_times(events, options)
    cycle_seconds = scaled_times[-1]

    start = time.perf_counter()
    held: set[str] = set()
    loop = 0

    try:
        while True:
            if stop_event.is_set():
                break
            if options.mode == LoopMode.DURATION and (time.perf_counter() - start) >= options.duration_seconds:
                break
            if options.mode == LoopMode.REPEAT_COUNT and loop >= options.repeat_count:
                break

            loop_start_offset = loop * cycle_seconds

            for evt, relative in zip(events, scaled_times):
                if stop_event.is_set():
                    break

                target = start + loop_start_offset + relative

                ok = _wait_until(lambda: target, stop_event)
                if not ok:
                    break

                apply_event(evt)
                if evt.kind in BUTTON_OF_DOWN:
                    held.add(BUTTON_OF_DOWN[evt.kind])
                elif evt.kind in BUTTON_OF_UP:
                    held.discard(BUTTON_OF_UP[evt.kind])

            loop += 1
            if progress is not None:
                progress(PlaybackStatus(completed_loops=loop, elapsed_seconds=time.perf_counter() - start))

            if options.mode == LoopMode.REPEAT_COUNT and loop >= options.repeat_count:
                break
    finally:
        if held:
            release_held(held)
