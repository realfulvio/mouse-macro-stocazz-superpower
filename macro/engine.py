"""Motore di riproduzione generico: rispetta i tempi originali della registrazione con
precisione sub-millisecondo (attesa ibrida sleep + spin-wait) ed è indipendente dal
backend di sistema (Linux/Windows) usato per registrare e iniettare gli eventi.
"""
from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Iterable

from .events import BUTTON_OF_DOWN, BUTTON_OF_UP, MOVE_ABS, WHEEL, MacroEvent


class LoopMode(Enum):
    INFINITE = "infinite"
    REPEAT_COUNT = "repeat_count"
    DURATION = "duration"


@dataclass
class PlaybackOptions:
    mode: LoopMode = LoopMode.REPEAT_COUNT
    repeat_count: int | None = None
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
    min_click_hold_seconds: float = 0.15
    # Attesa minima dopo il rilascio, indipendente dalla pressione e dalla velocità.
    min_action_gap_seconds: float = 0.15
    # Modalità opzionale: aggiunge attese casuali senza cambiare le coordinate.
    # Zero mantiene esattamente il comportamento precedente.
    timing_variation_seconds: float = 0.0
    # Modalita' opzionale "movimento umano" (spenta di default): a ogni giro i tragitti
    # fra due gesti seguono una curva leggermente diversa e con velocita' non uniforme,
    # e le pause variano. Pressioni, rilasci e rotella restano esattamente dove
    # sono stati registrati; solo i movimenti liberi del cursore cambiano.
    humanize: bool = False
    # Windows panel enables explicit double-click preservation; legacy callers
    # keep their original timing policy.
    double_click_seconds: float = 0.0
    double_click_gap_seconds: float = 0.08
    protect_wheel_actions: bool = False


def _double_click_indices(events: list[MacroEvent], options: PlaybackOptions) -> set[int]:
    pairs: set[int] = set()
    previous_down = None
    released = False
    for i, event in enumerate(events):
        if event.kind in BUTTON_OF_DOWN:
            if (previous_down is not None and released and options.double_click_seconds > 0
                    and event.kind == previous_down.kind
                    and 0 < event.t - previous_down.t <= options.double_click_seconds
                    and abs(event.x - previous_down.x) <= 4
                    and abs(event.y - previous_down.y) <= 4):
                pairs.add(i)
                previous_down = None  # three clicks are not two overlapping pairs
            else:
                previous_down = event
            released = False
        elif event.kind in BUTTON_OF_UP:
            released = previous_down is not None and BUTTON_OF_UP[event.kind] == BUTTON_OF_DOWN[previous_down.kind]
        elif event.kind == WHEEL or (event.kind == "move_abs" and previous_down is not None
                and (abs(event.x - previous_down.x) > 4 or abs(event.y - previous_down.y) > 4)):
            previous_down = None
            released = False
    return pairs


HUMAN_PAUSE_SECONDS = 0.25   # variazione massima delle pause con il movimento umano
HUMAN_MAX_DEVIATION = 28.0   # px: scostamento massimo dal tragitto registrato
HUMAN_MIN_CHORD = 12.0       # px: tragitti piu' corti restano identici


def _smoothstep(u: float) -> float:
    return u * u * (3.0 - 2.0 * u)


def _humanize_cycle(events: list[MacroEvent], times: list[float],
                    rng: random.Random) -> tuple[list[MacroEvent], list[float]]:
    """Restituisce una copia del giro con percorsi e velocita' dei soli movimenti liberi
    (cursore senza tasti premuti) variati. Non cambia numero, ordine, tipo e tempo di
    pressioni/rilasci/rotella; primo e ultimo punto di ogni tragitto restano esatti,
    quindi i clic arrivano sempre sulle stesse coordinate."""
    out = [replace(e) for e in events]
    new_times = list(times)
    held: set[str] = set()
    i = 0
    n = len(events)
    while i < n:
        evt = events[i]
        if evt.kind in BUTTON_OF_DOWN:
            held.add(BUTTON_OF_DOWN[evt.kind])
        elif evt.kind in BUTTON_OF_UP:
            held.discard(BUTTON_OF_UP[evt.kind])
        if evt.kind != MOVE_ABS or held:
            i += 1
            continue
        j = i
        while j + 1 < n and events[j + 1].kind == MOVE_ABS:
            j += 1
        _humanize_run(events, out, times, new_times, i, j, rng)
        i = j + 1
    return out, new_times


def _humanize_run(events, out, times, new_times, a, b, rng) -> None:
    """Varia i movimenti a..b (consecutivi, senza tasti premuti)."""
    if b - a < 2:
        return
    x0, y0, x1, y1 = events[a].x, events[a].y, events[b].x, events[b].y
    chord = math.hypot(x1 - x0, y1 - y0)
    if chord < HUMAN_MIN_CHORD:
        return
    # Velocita': il tragitto parte piano, accelera e rallenta vicino al bersaglio, e puo'
    # finire un po' prima del momento registrato (poi il cursore resta fermo fino al gesto).
    anchor = times[a - 1] if a > 0 else times[a]
    span = times[b] - anchor
    ease = rng.uniform(0.3, 0.8)
    pace = rng.uniform(0.8, 1.0)
    # Percorso: arco laterale piu' una leggera "S", nulli agli estremi.
    nx, ny = -(y1 - y0) / chord, (x1 - x0) / chord
    arc = min(HUMAN_MAX_DEVIATION, chord * rng.uniform(0.02, 0.08)) * rng.choice((-1, 1))
    wave = min(HUMAN_MAX_DEVIATION / 3, chord * rng.uniform(0.0, 0.03)) * rng.choice((-1, 1))
    for k in range(a, b + 1):
        u = (k - a) / (b - a)
        if 0 < k - a < b - a:
            d = arc * math.sin(math.pi * u) + wave * math.sin(2.0 * math.pi * u)
            out[k].x = int(round(events[k].x + nx * d + rng.uniform(-0.8, 0.8)))
            out[k].y = int(round(events[k].y + ny * d + rng.uniform(-0.8, 0.8)))
        if span > 0:
            tu = (times[k] - anchor) / span
            eased = tu + ease * (_smoothstep(tu) - tu)
            new_times[k] = anchor + span * pace * eased
    # I tempi restano non decrescenti anche con il rumore numerico.
    for k in range(a + 1, b + 1):
        new_times[k] = max(new_times[k], new_times[k - 1])


@dataclass
class PlaybackStatus:
    completed_loops: int
    elapsed_seconds: float


def _wait_until(deadline: Callable[[], float], stop_event: threading.Event) -> bool:
    """Attende con precisione sub-millisecondo fino all'istante target (in secondi,
    stessa base di time.perf_counter()). Ritorna False se interrotta da stop_event."""
    while True:
        if stop_event.is_set():
            return False
        remaining = deadline() - time.perf_counter()
        if remaining <= 0:
            return True
        if stop_event.is_set():
            return False
        if remaining > 0.003:
            if stop_event.wait(remaining - 0.002):
                return False
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
    # I movimenti del cursore non devono spezzare un'attesa fra due azioni.
    # Manteniamo il percorso rapido e aggiungiamo l'eventuale attesa al gesto seguente.
    idle_start = None
    held: set[str] = set()
    shift = 0.0
    for i, evt in enumerate(events):
        scaled[i] += shift
        if evt.kind in BUTTON_OF_DOWN:
            if not held and idle_start is not None:
                gap = evt.t - events[idle_start].t
                if gap > options.pause_threshold_seconds:
                    required = gap / min(speed, options.max_pause_speedup)
                    extra = max(0.0, required - (scaled[i] - scaled[idle_start]))
                    scaled[i] += extra
                    shift += extra
            held.add(BUTTON_OF_DOWN[evt.kind])
            idle_start = None
        elif evt.kind in BUTTON_OF_UP:
            held.discard(BUTTON_OF_UP[evt.kind])
            if not held:
                idle_start = i
        elif evt.kind == WHEEL:
            idle_start = i if options.protect_wheel_actions and not held else None
    _enforce_min_click_hold(events, scaled, options.min_click_hold_seconds,
                            options.min_action_gap_seconds, _double_click_indices(events, options),
                            options.double_click_gap_seconds, options.protect_wheel_actions)
    return scaled


def _vary_times(
    events: list[MacroEvent], scaled: list[float], maximum: float, rng: random.Random,
) -> list[float]:
    """Aggiunge pause ai gesti completi; non altera percorsi o combinazioni di tasti."""
    maximum = max(0.0, min(1.0, maximum))
    if maximum == 0:
        return scaled
    varied = []
    shift = 0.0
    held: set[str] = set()
    for evt, relative in zip(events, scaled):
        if evt.kind in BUTTON_OF_DOWN:
            if not held:
                shift += rng.uniform(0.0, maximum)
            held.add(BUTTON_OF_DOWN[evt.kind])
        elif evt.kind in BUTTON_OF_UP:
            button = BUTTON_OF_UP[evt.kind]
            if held == {button}:
                shift += rng.uniform(0.0, maximum / 4.0)
            held.discard(button)
        varied.append(relative + shift)
    return varied


def _enforce_min_click_hold(events: list[MacroEvent], scaled: list[float], min_hold: float,
                            min_gap: float = 0.15, double_indices: set[int] | None = None,
                            double_gap: float = 0.08, protect_wheel: bool = False) -> None:
    """Garantisce, spostando in avanti (in-place) l'evento e tutti i successivi, che:
    - tra la pressione e il rilascio dello stesso tasto passino almeno min_hold secondi;
    - tra un rilascio e la pressione successiva (di qualsiasi tasto) passino almeno
      min_gap secondi, senza spezzare combinazioni di pulsanti già premuti.
    Così, anche accelerando molto, ogni click resta "vedibile" da chi lo riceve e due
    click consecutivi non vengono fusi o scartati (tipica causa di click persi)."""
    min_hold, min_gap = max(0.0, min_hold), max(0.0, min_gap)
    if min_hold == 0 and min_gap == 0:
        return
    down_time: dict[str, float] = {}
    last_up: float | None = None
    shift = 0.0
    for i, evt in enumerate(events):
        scaled[i] += shift
        if evt.kind in BUTTON_OF_DOWN:
            gap = double_gap if double_indices and i in double_indices else min_gap
            if not down_time and last_up is not None and (scaled[i] - last_up) < gap:
                extra = gap - (scaled[i] - last_up)
                scaled[i] += extra
                shift += extra
            down_time[BUTTON_OF_DOWN[evt.kind]] = scaled[i]
        elif evt.kind in BUTTON_OF_UP:
            t0 = down_time.pop(BUTTON_OF_UP[evt.kind], None)
            if t0 is not None and (scaled[i] - t0) < min_hold:
                extra = min_hold - (scaled[i] - t0)
                scaled[i] += extra
                shift += extra
            last_up = scaled[i]
        elif evt.kind == WHEEL and protect_wheel and not down_time:
            if last_up is not None and scaled[i] - last_up < min_gap:
                extra = min_gap - (scaled[i] - last_up)
                scaled[i] += extra
                shift += extra
            last_up = scaled[i]


class PlaybackEnd(Enum):
    DONE = "done"
    STOPPED = "stopped"
    SYNC_TIMEOUT = "sync_timeout"


def play(
    events: Iterable[MacroEvent],
    options: PlaybackOptions,
    apply_event: Callable[[MacroEvent], None],
    release_held: Callable[[set[str]], None],
    progress: Callable[[PlaybackStatus], None] | None,
    stop_event: threading.Event,
    wait_ready: Callable[[MacroEvent], bool] | None = None,
    between_cycles: Callable[[], None] | None = None,
    trace: Callable[[dict], None] | None = None,
) -> PlaybackEnd:
    """Riproduce la sequenza di eventi rispettando le opzioni di ripetizione/velocità.

    apply_event: esegue un singolo evento tramite il backend di sistema.
    release_held: rilascia i tasti eventualmente rimasti "premuti" se la riproduzione
                  viene interrotta a metà (evita di lasciare il mouse in uno stato bloccato).
    wait_ready: se presente, viene chiamata prima di ogni pressione di tasto e blocca
                finché la destinazione non è pronta (False = timeout, la riproduzione si
                ferma). Il tempo atteso sposta in avanti tutti gli eventi successivi.
    between_cycles: se presente, viene chiamata tra un giro e il successivo (mai dopo
                    l'ultimo), es. per passare alla scheda successiva del browser.
    """
    events = list(events)
    if not events:
        return PlaybackEnd.DONE

    if options.mode == LoopMode.REPEAT_COUNT and (
        not isinstance(options.repeat_count, int)
        or isinstance(options.repeat_count, bool)
        or options.repeat_count <= 0
    ):
        raise ValueError("Imposta un numero intero di giri maggiore di zero.")

    scaled_times = _compute_scaled_times(events, options)
    variation = max(0.0, min(1.0, options.timing_variation_seconds))
    if options.humanize:
        variation = max(variation, HUMAN_PAUSE_SECONDS)
    rng = random.Random() if variation else None

    start = time.perf_counter()
    held: set[str] = set()
    actual_down: dict[str, float] = {}
    actual_last_up: float | None = None
    minimum = max(0.0, options.min_click_hold_seconds)
    action_gap = max(0.0, options.min_action_gap_seconds)
    double_indices = _double_click_indices(events, options)
    loop = 0
    extra_delay = 0.0
    loop_start_offset = 0.0
    end = PlaybackEnd.DONE

    def report(record_type: str, **details) -> None:
        if trace is not None:
            trace({"type": record_type, "elapsed_seconds": time.perf_counter() - start,
                   "cycle": loop + 1, **details})

    report("playback_start")

    try:
        while end == PlaybackEnd.DONE:
            if stop_event.is_set():
                end = PlaybackEnd.STOPPED
                break
            if options.mode == LoopMode.DURATION and (time.perf_counter() - start) >= options.duration_seconds:
                break
            if options.mode == LoopMode.REPEAT_COUNT and loop >= options.repeat_count:
                break

            cycle_events, base_times = events, scaled_times
            if options.humanize and rng:
                cycle_events, base_times = _humanize_cycle(events, scaled_times, rng)
            cycle_times = _vary_times(events, base_times, variation, rng) if rng else base_times

            click = 0
            for index, (evt, relative) in enumerate(zip(cycle_events, cycle_times)):
                if evt.kind in BUTTON_OF_DOWN:
                    click += 1
                target = start + loop_start_offset + relative + extra_delay
                # Se il backend o Windows ritarda, sposta tutto il seguito invece
                # di recuperare il ritardo inviando pressioni/rilasci in raffica.
                earliest = time.perf_counter()
                if (evt.kind in BUTTON_OF_DOWN or (options.protect_wheel_actions and evt.kind == WHEEL)) and not held and actual_last_up is not None:
                    gap = options.double_click_gap_seconds if index in double_indices else action_gap
                    earliest = max(earliest, actual_last_up + gap)
                elif evt.kind in BUTTON_OF_UP:
                    pressed_at = actual_down.get(BUTTON_OF_UP[evt.kind])
                    if pressed_at is not None:
                        earliest = max(earliest, pressed_at + minimum)
                late = max(0.0, earliest - target)
                target += late
                extra_delay += late
                if not _wait_until(lambda: target, stop_event):
                    end = PlaybackEnd.STOPPED
                    break

                if wait_ready is not None and evt.kind in BUTTON_OF_DOWN:
                    before = time.perf_counter()
                    ready = wait_ready(evt)
                    extra_delay += time.perf_counter() - before
                    report("visual_check", click=click,
                           waited_seconds=time.perf_counter() - before,
                           outcome=("reference_match" if evt.snap else "missing_reference")
                           if ready else ("stopped" if stop_event.is_set() else "timeout"))
                    if not ready:
                        end = PlaybackEnd.STOPPED if stop_event.is_set() else PlaybackEnd.SYNC_TIMEOUT
                        break

                if stop_event.is_set():
                    end = PlaybackEnd.STOPPED
                    break
                if evt.kind in BUTTON_OF_DOWN:
                    # Include a possibly partially injected press in cleanup even
                    # if the backend raises after sending it.
                    held.add(BUTTON_OF_DOWN[evt.kind])
                apply_event(evt)
                if evt.kind in BUTTON_OF_DOWN:
                    actual_down[BUTTON_OF_DOWN[evt.kind]] = time.perf_counter()
                    report("input_sent", click=click, kind=evt.kind,
                           since_last_release_seconds=None if actual_last_up is None
                           else actual_down[BUTTON_OF_DOWN[evt.kind]] - actual_last_up)
                elif evt.kind in BUTTON_OF_UP:
                    held.discard(BUTTON_OF_UP[evt.kind])
                    pressed_at = actual_down.pop(BUTTON_OF_UP[evt.kind], None)
                    actual_last_up = time.perf_counter()
                    report("input_sent", click=click, kind=evt.kind,
                           hold_seconds=None if pressed_at is None else actual_last_up - pressed_at)
                elif evt.kind == WHEEL and not held:
                    if options.protect_wheel_actions:
                        actual_last_up = time.perf_counter()
                    report("input_sent", click=click, kind=evt.kind)

            if end != PlaybackEnd.DONE:
                break

            # Protegge anche l'ultima azione, prima del cambio scheda e prima di dichiarare
            # il giro finito. È un'attesa temporale, non una conferma del sito.
            if actual_last_up is not None and not held:
                before = time.perf_counter()
                if not _wait_until(lambda: actual_last_up + action_gap, stop_event):
                    end = PlaybackEnd.STOPPED
                    break
                report("cycle_guard", waited_seconds=time.perf_counter() - before)

            loop += 1
            # Ogni giro ha tempi nuovi; l'offset cumulativo evita sovrapposizioni.
            loop_start_offset += cycle_times[-1] + action_gap
            if rng:
                loop_start_offset += rng.uniform(0.0, variation * 3.0)
            if progress is not None:
                progress(PlaybackStatus(completed_loops=loop, elapsed_seconds=time.perf_counter() - start))

            if between_cycles is not None and not stop_event.is_set():
                if options.mode == LoopMode.REPEAT_COUNT:
                    another = loop < options.repeat_count
                elif options.mode == LoopMode.DURATION:
                    another = (time.perf_counter() - start) < options.duration_seconds
                else:
                    another = True
                if another:
                    before = time.perf_counter()
                    between_cycles()
                    extra_delay += time.perf_counter() - before
    finally:
        if held:
            release_held(held)
            report("safety_release", buttons=sorted(held))
    report("playback_end", cycle=loop, outcome=end.value, completed_cycles=loop)
    return end
