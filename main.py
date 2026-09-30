"""Mouse Macro Stocazz Superpower — registra i movimenti e i click del mouse e li
riproduce con precisione, all'infinito o per un tempo/numero di ripetizioni scelto.
Funziona su Linux (X11/Wayland, via evdev/uinput) e su Windows (via pynput)."""
from __future__ import annotations

import random
import threading
import time

import flet as ft

from macro.backend import current_platform, list_mice, make_player, make_recorder
from macro.engine import LoopMode, PlaybackEnd, PlaybackOptions, PlaybackStatus, play
from macro.events import BUTTON_OF_DOWN, LEFT_DOWN, Macro, MacroEvent

# Palette viola-prugna di sfondo, rosa
# come colore principale, verde/giallo per gli stati, cavallini come decorazione).
ACCENT_1 = "#FF4F9A"   # rosa
ACCENT_2 = "#E8B400"   # giallo
BG_TOP = "#241226"
BG_BOTTOM = "#2E1730"
CARD_BG = "#3A1F3D"
CARD_BORDER = "#6B566D"
FIELD_BG = "#241226"
TEXT_MUTED = "#CBB3C9"
DANGER = "#D6357C"
SUCCESS = "#3FA66B"
VERSION = "v0.4 beta"


def main(page: ft.Page):
    page.title = "Mouse Macro Stocazz Superpower"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 560
    page.window.height = 900
    page.window.min_width = 480
    page.window.min_height = 640
    page.window.icon = "icon.ico"
    page.padding = 0
    page.bgcolor = BG_TOP
    page.fonts = {
        "Outfit": "https://fonts.gstatic.com/s/outfit/v11/QGYyz_MVSrGYuFEspgzsQ.ttf",
    }
    page.theme = ft.Theme(font_family="Outfit")

    platform = current_platform()

    # --- stato applicativo ---
    state = {
        "macro": Macro(platform=platform, events=[]),
        "recorder": None,
        "player": None,
        "recording": False,
        "playing": False,
        "stop_event": None,
        "selected_device": None,
    }

    # ================= Header =================
    rec_dot = ft.Container(
        width=12, height=12, border_radius=6, bgcolor=DANGER,
        animate_opacity=300,
        opacity=0.3,
    )

    title = ft.Column(
        [
            ft.Text("MOUSE MACRO", size=19, weight=ft.FontWeight.W_800,
                     color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=1.2)),
            ft.Text("STOCAZZ SUPERPOWER", size=13, weight=ft.FontWeight.W_800,
                     color=ACCENT_1, style=ft.TextStyle(letter_spacing=1.0)),
            ft.Text(f"backend: {platform}", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
        ],
        spacing=2,
    )

    def help_step(n: str, text: str):
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(n, size=12, weight=ft.FontWeight.W_800, color=ft.Colors.WHITE),
                    width=24, height=24, border_radius=12, bgcolor=ACCENT_1,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(text, size=13, expand=True),
            ],
            spacing=10, vertical_alignment=ft.CrossAxisAlignment.START,
        )

    help_dialog = ft.AlertDialog(
        modal=False,
        title=ft.Text("Come si usa"),
        content=ft.Column(
            [
                help_step("1", "Apri nel browser tutte le schede dei cavalli da gestire e mettiti sulla prima."),
                help_step("2", "Premi F9 (funziona anche dal browser) e fai a mano i compiti su quel cavallo, "
                               "con calma e con la pagina già caricata."),
                help_step("3", "Premi F9 per fermare. Se usi l'opzione \"A fine giro chiudi la scheda\", "
                               "non chiudere la scheda durante la registrazione: lo farà il programma."),
                help_step("4", "In \"Ripetizione\" scegli \"N volte\" e metti quante schede hai aperto."),
                help_step("5", "Torna sulla prima scheda da fare e premi F10. Per fermare: F10, "
                               "oppure Ctrl+Alt+F11 in emergenza."),
                ft.Container(height=4),
                ft.Text("Per non sbagliare i click", size=13, weight=ft.FontWeight.W_700),
                ft.Text(
                    "• Non spostare, ridimensionare o zoomare il browser tra registrazione e riproduzione.\n"
                    "• Durante la riproduzione non toccare il mouse.\n"
                    "• Registra sempre con le pagine già caricate.\n"
                    "• Salva la macro (\"Salva macro\") per riusarla i giorni successivi.",
                    size=12,
                ),
            ],
            tight=True, spacing=10, width=420, scroll=ft.ScrollMode.AUTO,
        ),
        actions=[ft.TextButton("Ho capito", on_click=lambda e: page.pop_dialog())],
    )

    help_button = ft.IconButton(
        ft.Icons.HELP_OUTLINE_ROUNDED, icon_color=TEXT_MUTED, tooltip="Come si usa",
        on_click=lambda e: page.show_dialog(help_dialog),
    )

    header = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Image(src="icon.png", width=48, height=48, fit=ft.BoxFit.CONTAIN),
                    width=48, height=48, border_radius=14,
                    shadow=ft.BoxShadow(blur_radius=18, color="#40FF4F9A", spread_radius=-2),
                ),
                title,
                ft.Container(expand=True),
                help_button,
                rec_dot,
            ],
            spacing=14,
        ),
        padding=ft.Padding.only(left=24, right=24, top=26, bottom=10),
    )

    # ================= Status card (telemetria) =================
    status_title = ft.Text("Pronto", size=15, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE)
    status_sub = ft.Text("Registra i movimenti del mouse per iniziare.", size=12, color=TEXT_MUTED)
    stat_events = ft.Text("0", size=20, weight=ft.FontWeight.W_700, color=ACCENT_2, font_family="Roboto Mono")
    stat_time = ft.Text("00:00.00", size=20, weight=ft.FontWeight.W_700, color=ACCENT_1, font_family="Roboto Mono")

    def stat_block(label: str, value_ctrl: ft.Text):
        return ft.Column(
            [value_ctrl, ft.Text(label, size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_600)],
            spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    status_card = ft.Container(
        content=ft.Column(
            [
                ft.Row([status_title], ),
                status_sub,
                ft.Container(height=14),
                ft.Row(
                    [stat_block("EVENTI", stat_events), ft.Container(width=1, height=36, bgcolor=CARD_BORDER),
                     stat_block("DURATA", stat_time)],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                ),
            ],
        ),
        padding=20, border_radius=20, bgcolor=CARD_BG,
        border=ft.Border.all(1, CARD_BORDER),
    )

    # ================= Pulsanti REC / PLAY =================
    def make_action_button(icon, text, on_click, gradient_colors):
        return ft.Container(
            content=ft.Row(
                [ft.Icon(icon, color=ft.Colors.WHITE, size=20), ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700, size=14)],
                alignment=ft.MainAxisAlignment.CENTER, spacing=8,
            ),
            gradient=ft.LinearGradient(colors=gradient_colors),
            border_radius=16, padding=ft.Padding.symmetric(vertical=16),
            on_click=on_click, ink=True, expand=True,
            shadow=ft.BoxShadow(blur_radius=16, color="#40FF4F9A", spread_radius=-4, offset=ft.Offset(0, 6)),
            animate_scale=150,
        )

    btn_record = make_action_button(ft.Icons.FIBER_MANUAL_RECORD, "REGISTRA  (F9)", None, [DANGER, ACCENT_1])
    btn_play = make_action_button(ft.Icons.PLAY_ARROW_ROUNDED, "RIPRODUCI  (F10)", None, [SUCCESS, ACCENT_2])
    btn_play.opacity = 0.4

    # ================= Opzioni ripetizione =================
    def chip(icon, label, selected=False):
        return ft.Container(
            content=ft.Row([ft.Icon(icon, size=16, color=ft.Colors.WHITE if selected else TEXT_MUTED),
                             ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                                     color=ft.Colors.WHITE if selected else TEXT_MUTED)],
                            spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(vertical=10, horizontal=6),
            border_radius=12, expand=True,
            gradient=ft.LinearGradient(colors=[ACCENT_1, ACCENT_2]) if selected else None,
            bgcolor=None if selected else FIELD_BG,
            animate=150,
        )

    loop_mode = {"value": "infinite"}

    num_count = ft.TextField(value="5", width=64, height=42, text_align=ft.TextAlign.CENTER,
                              bgcolor=FIELD_BG, border_color=CARD_BORDER, border_radius=10,
                              color=ft.Colors.WHITE, text_size=13, content_padding=6)
    num_minutes = ft.TextField(value="10", width=64, height=42, text_align=ft.TextAlign.CENTER,
                                bgcolor=FIELD_BG, border_color=CARD_BORDER, border_radius=10,
                                color=ft.Colors.WHITE, text_size=13, content_padding=6)

    chip_infinite = chip(ft.Icons.ALL_INCLUSIVE_ROUNDED, "Infinito", True)
    chip_count = chip(ft.Icons.REPEAT_ROUNDED, "N volte", False)
    chip_duration = chip(ft.Icons.TIMER_ROUNDED, "Durata", False)

    row_count = ft.Row([num_count, ft.Text("volte", size=12, color=TEXT_MUTED)], spacing=8, visible=False)
    row_duration = ft.Row([num_minutes, ft.Text("minuti", size=12, color=TEXT_MUTED)], spacing=8, visible=False)

    LOOP_HINTS = {
        "infinite": "Ripete la macro finché non la fermi con F10.",
        "count": "Ripete la macro il numero di volte indicato. Con le schede dei cavalli: "
                 "metti quante schede hai aperto (un giro = un cavallo).",
        "duration": "Continua a ripetere per i minuti indicati; il giro in corso viene sempre finito.",
    }
    loop_hint = ft.Text(LOOP_HINTS["infinite"], size=10, color=TEXT_MUTED)

    def select_loop(mode: str):
        loop_hint.value = LOOP_HINTS[mode]
        loop_mode["value"] = mode
        chip_infinite.gradient = ft.LinearGradient(colors=[ACCENT_1, ACCENT_2]) if mode == "infinite" else None
        chip_infinite.bgcolor = None if mode == "infinite" else FIELD_BG
        chip_count.gradient = ft.LinearGradient(colors=[ACCENT_1, ACCENT_2]) if mode == "count" else None
        chip_count.bgcolor = None if mode == "count" else FIELD_BG
        chip_duration.gradient = ft.LinearGradient(colors=[ACCENT_1, ACCENT_2]) if mode == "duration" else None
        chip_duration.bgcolor = None if mode == "duration" else FIELD_BG
        for c, sel in ((chip_infinite, mode == "infinite"), (chip_count, mode == "count"), (chip_duration, mode == "duration")):
            c.content.controls[0].color = ft.Colors.WHITE if sel else TEXT_MUTED
            c.content.controls[1].color = ft.Colors.WHITE if sel else TEXT_MUTED
        row_count.visible = mode == "count"
        row_duration.visible = mode == "duration"
        page.update()

    chip_infinite.on_click = lambda e: select_loop("infinite")
    chip_count.on_click = lambda e: select_loop("count")
    chip_duration.on_click = lambda e: select_loop("duration")

    speed_slider = ft.Slider(min=0.1, max=3.0, value=1.0, divisions=29, active_color=ACCENT_2,
                              inactive_color=CARD_BORDER, expand=True)
    speed_label = ft.Text("1.00x", size=13, weight=ft.FontWeight.W_700, color=ACCENT_2, width=52)

    def speed_norm(value: float) -> float:
        return (value - speed_slider.min) / (speed_slider.max - speed_slider.min)

    # Cavallo che galoppa lungo lo slider: la sua posizione segue il valore scelto,
    # più veloce è la riproduzione più il cavallo corre in avanti (e si inclina di più).
    speed_horse = ft.Text("🐎", size=15, rotate=ft.Rotate(angle=0.0))
    horse_holder = ft.Container(
        content=speed_horse, top=-15, left=6, right=6, height=16,
        alignment=ft.Alignment(speed_norm(speed_slider.value) * 2 - 1, 0),
    )
    speed_track = ft.Stack(
        [
            speed_slider,
            horse_holder,
        ],
        expand=True,
    )

    def on_speed_change(e):
        speed_label.value = f"{speed_slider.value:.2f}x"
        norm = speed_norm(speed_slider.value)
        horse_holder.alignment = ft.Alignment(norm * 2 - 1, 0)
        speed_horse.rotate = ft.Rotate(angle=norm * 0.25)
        page.update()

    speed_slider.on_change = on_speed_change

    min_click_ms = ft.TextField(value="30", width=64, height=42, text_align=ft.TextAlign.CENTER,
                                 bgcolor=FIELD_BG, border_color=CARD_BORDER, border_radius=10,
                                 color=ft.Colors.WHITE, text_size=13, content_padding=6)

    def section_title(text: str):
        return ft.Text(text, size=11, weight=ft.FontWeight.W_700, color=TEXT_MUTED, style=ft.TextStyle(letter_spacing=1.2))

    def hint(text: str):
        return ft.Text(text, size=10, color=TEXT_MUTED)

    # --- Browser: chiusura scheda a fine giro (solo Windows) ---
    tab_switch = ft.Switch(value=False, active_color=ACCENT_1)
    browser_section = ft.Column(
        [
            ft.Container(height=6),
            section_title("SCHEDE DEL BROWSER"),
            ft.Row(
                [
                    ft.Icon(ft.Icons.TAB_ROUNDED, size=18, color=TEXT_MUTED),
                    ft.Text("A fine giro chiudi la scheda (Ctrl+W)", size=12, color=TEXT_MUTED, expand=True),
                    tab_switch,
                ],
                spacing=8,
            ),
            hint(
                "Dopo ogni giro chiude la scheda del cavallo appena fatto e il browser passa da solo alla successiva. "
                "Più affidabile che cliccare la X della scheda, che si sposta man mano che le schede diminuiscono. "
                "Attivalo solo se durante la registrazione NON hai chiuso la scheda. Dopo l'ultimo giro non chiude nulla."
            ),
        ],
        spacing=10,
        visible=(platform == "windows"),
    )

    # --- Attesa pagina (solo Windows): prima di ogni click confronta il punto dello
    # schermo con il ritaglio salvato in registrazione ---
    sync_switch = ft.Switch(value=False, active_color=ACCENT_1)
    sync_timeout = ft.TextField(value="20", width=64, height=42, text_align=ft.TextAlign.CENTER,
                                 bgcolor=FIELD_BG, border_color=CARD_BORDER, border_radius=10,
                                 color=ft.Colors.WHITE, text_size=13, content_padding=6)

    tolerance = {"value": "normal"}
    TOLERANCE_HINTS = {
        "strict": "Preciso: il punto deve essere quasi identico. Rischia di fermarsi per differenze minime.",
        "normal": "Normale: va bene nella maggior parte dei casi.",
        "loose": "Tollerante: usalo se si ferma dicendo \"pagina non pronta\" anche quando la pagina è a posto "
                 "(es. attorno al pulsante cambiano nome o foto del cavallo).",
    }
    tol_strict = chip(ft.Icons.CENTER_FOCUS_STRONG_ROUNDED, "Preciso", False)
    tol_normal = chip(ft.Icons.CENTER_FOCUS_WEAK_ROUNDED, "Normale", True)
    tol_loose = chip(ft.Icons.BLUR_ON_ROUNDED, "Tollerante", False)
    tol_hint = hint(TOLERANCE_HINTS["normal"])

    def select_tolerance(level: str):
        tolerance["value"] = level
        for c, key in ((tol_strict, "strict"), (tol_normal, "normal"), (tol_loose, "loose")):
            sel = key == level
            c.gradient = ft.LinearGradient(colors=[ACCENT_1, ACCENT_2]) if sel else None
            c.bgcolor = None if sel else FIELD_BG
            c.content.controls[0].color = ft.Colors.WHITE if sel else TEXT_MUTED
            c.content.controls[1].color = ft.Colors.WHITE if sel else TEXT_MUTED
        tol_hint.value = TOLERANCE_HINTS[level]
        page.update()

    tol_strict.on_click = lambda e: select_tolerance("strict")
    tol_normal.on_click = lambda e: select_tolerance("normal")
    tol_loose.on_click = lambda e: select_tolerance("loose")

    sync_details = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.TIMER_OFF_ROUNDED, size=18, color=TEXT_MUTED),
                    ft.Text("Attesa massima per ogni click", size=12, color=TEXT_MUTED, expand=True),
                    sync_timeout,
                    ft.Text("s", size=12, color=TEXT_MUTED),
                ],
                spacing=8,
            ),
            hint("Se dopo questo tempo il punto non è ancora pronto, la riproduzione si ferma invece di cliccare a vuoto."),
            ft.Text("Confronto", size=12, color=TEXT_MUTED),
            ft.Row([tol_strict, tol_normal, tol_loose], spacing=8),
            tol_hint,
        ],
        spacing=10,
        visible=False,
    )

    def on_sync_change(e):
        sync_details.visible = bool(sync_switch.value)
        page.update()

    sync_switch.on_change = on_sync_change

    sync_section = ft.Column(
        [
            ft.Container(height=6),
            section_title("ATTESA PAGINA"),
            ft.Row(
                [
                    ft.Icon(ft.Icons.HOURGLASS_TOP_ROUNDED, size=18, color=TEXT_MUTED),
                    ft.Text("Aspetta che la pagina sia pronta prima di cliccare", size=12, color=TEXT_MUTED, expand=True),
                    sync_switch,
                ],
                spacing=8,
            ),
            hint(
                "Prima di ogni click controlla che quel punto dello schermo sia com'era in registrazione "
                "(pagina caricata, pulsante comparso). Se apri prima tutte le schede puoi lasciarla spenta; "
                "accendila se il sito a volte è lento e la macro clicca prima che la pagina sia pronta."
            ),
            sync_details,
        ],
        spacing=10,
        visible=(platform == "windows"),
    )

    options_card = ft.Container(
        content=ft.Column(
            [
                section_title("RIPETIZIONE"),
                ft.Row([chip_infinite, chip_count, chip_duration], spacing=8),
                ft.Row([row_count, row_duration], spacing=20),
                loop_hint,
                ft.Container(height=6),
                section_title("VELOCITÀ DI RIPRODUZIONE"),
                ft.Row([ft.Icon(ft.Icons.SPEED_ROUNDED, size=18, color=TEXT_MUTED), speed_track, speed_label]),
                hint(
                    "1x = stessa velocità della registrazione. Accelerando, le pause lunghe (es. mentre aspettavi "
                    "una pagina) vengono accelerate al massimo di 1,5x, per non cliccare prima del tempo."
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ADS_CLICK_ROUNDED, size=18, color=TEXT_MUTED),
                        ft.Text("Durata minima di click e pause", size=12, color=TEXT_MUTED, expand=True),
                        min_click_ms,
                        ft.Text("ms", size=12, color=TEXT_MUTED),
                    ],
                    spacing=8,
                ),
                hint(
                    "Evita i click persi quando acceleri: anche a velocità alte ogni click resta premuto almeno "
                    "questo tempo, e tra un click e il successivo passa almeno questo tempo. Lascia 30 ms; "
                    "se a velocità alte il sito perde ancora qualche click, alzalo a 50-80 ms."
                ),
                browser_section,
                sync_section,
            ],
            spacing=10,
        ),
        padding=20, border_radius=20, bgcolor=CARD_BG, border=ft.Border.all(1, CARD_BORDER),
    )

    # ================= Dispositivo mouse (solo Linux) =================
    device_dropdown = ft.Dropdown(
        options=[], bgcolor=FIELD_BG, border_color=CARD_BORDER, border_radius=10,
        color=ft.Colors.WHITE, text_size=13, content_padding=10, expand=True,
    )

    def refresh_devices(_=None):
        mice = list_mice()
        device_dropdown.options = [ft.dropdown.Option(key=path, text=name) for path, name in mice]
        if mice:
            device_dropdown.value = mice[0][0]
            state["selected_device"] = mice[0][0]
        else:
            device_dropdown.value = None
        page.update()

    def on_device_change(e):
        state["selected_device"] = device_dropdown.value

    device_dropdown.on_change = on_device_change

    device_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("MOUSE DA REGISTRARE", size=11, weight=ft.FontWeight.W_700, color=TEXT_MUTED, style=ft.TextStyle(letter_spacing=1.2)),
                ft.Row([device_dropdown, ft.IconButton(ft.Icons.REFRESH_ROUNDED, icon_color=TEXT_MUTED, on_click=refresh_devices)]),
            ],
            spacing=8,
        ),
        padding=20, border_radius=20, bgcolor=CARD_BG, border=ft.Border.all(1, CARD_BORDER),
        visible=(platform == "linux"),
    )

    # ================= Salva / Carica =================
    def save_result(e: ft.FilePickerResultEvent):
        if e.path:
            state["macro"].save(e.path)
            set_status(f"Macro salvata in {e.path}", f"{len(state['macro'].events)} eventi")

    def load_result(e: ft.FilePickerResultEvent):
        if e.files:
            try:
                loaded = Macro.load(e.files[0].path)
                if loaded.platform != platform:
                    set_status("Attenzione", f"Macro registrata su {loaded.platform}, potrebbe non funzionare qui.")
                state["macro"] = loaded
                stat_events.value = str(len(loaded.events))
                btn_play.opacity = 1.0
                set_status("Macro caricata", f"{len(loaded.events)} eventi da {e.files[0].name}")
            except Exception as ex:
                set_status("Errore nel caricamento", str(ex))
        page.update()

    save_picker = ft.FilePicker(on_result=save_result)
    load_picker = ft.FilePicker(on_result=load_result)
    page.services.extend([save_picker, load_picker])

    btn_save = ft.OutlinedButton(
        "Salva macro", icon=ft.Icons.SAVE_ROUNDED,
        on_click=lambda e: save_picker.save_file(file_name="macro.mmr"),
        style=ft.ButtonStyle(color=ft.Colors.WHITE),
        disabled=True, expand=True,
    )
    btn_load = ft.OutlinedButton(
        "Carica macro", icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        on_click=lambda e: load_picker.pick_files(allow_multiple=False),
        style=ft.ButtonStyle(color=ft.Colors.WHITE), expand=True,
    )

    hotkey_info = ft.Text(
        "F9 registra/stop · F10 riproduci/stop · Ctrl+Alt+F11 stop di emergenza",
        size=11, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER,
    )

    # ================= Logica =================
    def set_status(title_text: str, sub_text: str):
        status_title.value = title_text
        status_sub.value = sub_text
        page.update()

    def pulse_rec_dot():
        while state["recording"]:
            rec_dot.opacity = 1.0
            page.update()
            time.sleep(0.5)
            rec_dot.opacity = 0.25
            page.update()
            time.sleep(0.5)
        rec_dot.opacity = 0.3
        page.update()

    def poll_recording():
        start = time.perf_counter()
        while state["recording"] and state["recorder"] is not None:
            n = state["recorder"].current_event_count
            elapsed = time.perf_counter() - start
            stat_events.value = str(n)
            stat_time.value = format_time(elapsed)
            page.update()
            time.sleep(0.15)

    def format_time(seconds: float) -> str:
        m = int(seconds // 60)
        s = seconds - m * 60
        return f"{m:02d}:{s:05.2f}"

    def toggle_record(e=None):
        if state["playing"]:
            return
        if not state["recording"]:
            if platform == "linux" and not state["selected_device"]:
                set_status("Nessun mouse selezionato", "Scegli un dispositivo dalla lista qui sopra.")
                return
            try:
                recorder = make_recorder(state["selected_device"])
                recorder.start()
            except PermissionError:
                set_status(
                    "Permessi insufficienti",
                    "Aggiungi il tuo utente al gruppo 'input' (sudo usermod -aG input $USER) e rifai il login.",
                )
                return
            except Exception as ex:
                set_status("Errore all'avvio della registrazione", str(ex))
                return
            state["recorder"] = recorder
            state["recording"] = True
            btn_record.content.controls[1].value = "INTERROMPI  (F9)"
            btn_play.opacity = 0.4
            btn_save.disabled = True
            set_status("Registrazione in corso...", "Muovi il mouse e clicca normalmente.")
            threading.Thread(target=pulse_rec_dot, daemon=True).start()
            threading.Thread(target=poll_recording, daemon=True).start()
        else:
            events = state["recorder"].stop()
            if e is not None:
                # Fermata col pulsante dell'app: l'ultimo click registrato è proprio quello
                # su "INTERROMPI" e non deve finire nella macro (in riproduzione andrebbe a
                # cliccare sull'app). Con F9 non serve.
                last_down = max((i for i, ev in enumerate(events) if ev.kind == LEFT_DOWN), default=None)
                if last_down is not None:
                    events = events[:last_down]
            state["recording"] = False
            state["macro"] = Macro(platform=platform, events=events, screen=current_screen())
            btn_record.content.controls[1].value = "REGISTRA  (F9)"
            has_events = len(events) > 0
            btn_play.opacity = 1.0 if has_events else 0.4
            btn_save.disabled = not has_events
            clicks = sum(1 for ev in events if ev.kind in BUTTON_OF_DOWN)
            set_status("Registrazione completata", f"{len(events)} eventi, {clicks} click. Premi F10 per riprodurla.")
        page.update()

    def current_screen() -> list[int]:
        if platform != "windows":
            return []
        from macro.windows_backend import screen_geometry
        return screen_geometry()

    def parse_int(field: ft.TextField, default: int) -> int:
        try:
            return max(1, int(float(field.value)))
        except (ValueError, TypeError):
            return default

    def toggle_play(e=None):
        if state["playing"]:
            if state["stop_event"] is not None:
                state["stop_event"].set()
            return

        if not state["macro"].events:
            set_status("Nessuna macro", "Registra o carica prima una macro.")
            page.update()
            return

        recorded_screen = state["macro"].screen
        if recorded_screen and recorded_screen != current_screen():
            w, h = recorded_screen[2], recorded_screen[3]
            set_status(
                "Schermo diverso dalla registrazione",
                f"La macro è stata registrata con uno schermo di {w}×{h} (o con monitor disposti diversamente): "
                "i click finirebbero nei punti sbagliati. Rimetti la stessa risoluzione/monitor o registrala di nuovo.",
            )
            return

        mode_map = {"infinite": LoopMode.INFINITE, "count": LoopMode.REPEAT_COUNT, "duration": LoopMode.DURATION}
        options = PlaybackOptions(
            mode=mode_map[loop_mode["value"]],
            repeat_count=parse_int(num_count, 5),
            duration_seconds=parse_int(num_minutes, 10) * 60.0,
            speed=speed_slider.value,
            min_click_hold_seconds=parse_int(min_click_ms, 30) / 1000.0,
        )

        player = make_player()
        state["player"] = player
        state["playing"] = True
        state["stop_event"] = threading.Event()
        btn_play.content.controls[0].name = ft.Icons.STOP_ROUNDED
        btn_play.content.controls[1].value = "INTERROMPI  (F10)"
        btn_record.opacity = 0.4
        set_status("Riproduzione in corso...", "")
        page.update()

        def on_progress(status: PlaybackStatus):
            set_status("Riproduzione in corso...", f"cicli completati: {status.completed_loops} · {format_time(status.elapsed_seconds)}")

        stop_event = state["stop_event"]
        events = state["macro"].events
        timeout_s = float(parse_int(sync_timeout, 20))
        failed_click = {"n": 0}
        wait_ready = None
        if platform == "windows" and sync_switch.value:
            from macro.windows_backend import TOLERANCE_LOOSE, TOLERANCE_NORMAL, TOLERANCE_STRICT
            tol = {"strict": TOLERANCE_STRICT, "normal": TOLERANCE_NORMAL, "loose": TOLERANCE_LOOSE}[tolerance["value"]]
            click_number = {}
            for ev in events:
                if ev.kind in BUTTON_OF_DOWN:
                    click_number[id(ev)] = len(click_number) + 1

            def wait_ready(evt: MacroEvent) -> bool:
                n = click_number.get(id(evt), 0)
                ok = player.wait_until_ready(
                    evt, timeout_s, stop_event, tol,
                    on_waiting=lambda: set_status("In attesa della pagina...", f"Il punto del click n° {n} non è ancora pronto."),
                )
                if ok:
                    set_status("Riproduzione in corso...", "")
                else:
                    failed_click["n"] = n
                return ok

        between_cycles = None
        if platform == "windows" and tab_switch.value:
            def between_cycles():
                player.close_tab()
                # tempo per far comparire la scheda successiva
                stop_event.wait(1.0)

        def run():
            end = PlaybackEnd.STOPPED
            try:
                end = play(events, options, player.apply_event, player.release_held,
                           on_progress, stop_event, wait_ready, between_cycles)
            finally:
                player.close()
                state["playing"] = False
                btn_play.content.controls[0].name = ft.Icons.PLAY_ARROW_ROUNDED
                btn_play.content.controls[1].value = "RIPRODUCI  (F10)"
                btn_record.opacity = 1.0
                if end == PlaybackEnd.SYNC_TIMEOUT:
                    set_status(
                        f"Fermato: pagina non pronta al click n° {failed_click['n']}",
                        f"Dopo {int(timeout_s)} s quel punto non era ancora com'era in registrazione. "
                        "Controlla la pagina; se era a posto, scegli il confronto \"Tollerante\" o aumenta l'attesa massima.",
                    )
                else:
                    set_status("Riproduzione terminata", f"{len(state['macro'].events)} eventi nella macro.")
                page.update()

        threading.Thread(target=run, daemon=True).start()

    btn_record.on_click = toggle_record
    btn_play.on_click = toggle_play

    # ================= Tasti rapidi =================
    def emergency_stop():
        if state["recording"]:
            toggle_record()
        if state["stop_event"] is not None:
            state["stop_event"].set()

    global_hotkeys = None
    if platform == "windows":
        # Su Windows sono globali: funzionano anche col focus sul browser, così si può
        # fermare la registrazione senza tornare sull'app (e senza registrare quel click).
        from macro.windows_backend import (
            HOTKEY_EMERGENCY, HOTKEY_PLAY, HOTKEY_RECORD, GlobalHotkeys,
        )

        def on_hotkey(hk_id: int):
            if hk_id == HOTKEY_RECORD and not state["playing"]:
                toggle_record()
            elif hk_id == HOTKEY_PLAY and not state["recording"]:
                toggle_play()
            elif hk_id == HOTKEY_EMERGENCY:
                emergency_stop()

        global_hotkeys = GlobalHotkeys(on_hotkey)
        global_hotkeys.start()
        if global_hotkeys.failed:
            hotkey_info.value = (
                f"Tasti già usati da un altro programma: {', '.join(global_hotkeys.failed)} "
                "(funzionano solo con la finestra dell'app attiva)."
            )
        else:
            hotkey_info.value = (
                "F9 registra/stop · F10 riproduci/stop · Ctrl+Alt+F11 stop di emergenza — "
                "funzionano anche dal browser"
            )

    def on_keyboard(e: ft.KeyboardEvent):
        if global_hotkeys is not None and not global_hotkeys.failed:
            return
        if e.key == "F9" and not state["playing"]:
            toggle_record()
        elif e.key == "F10" and not state["recording"]:
            toggle_play()
        elif e.key == "F11" and e.ctrl and e.alt:
            emergency_stop()

    page.on_keyboard_event = on_keyboard

    if platform == "linux":
        refresh_devices()

    # ================= Cavallini decorativi (sfondo) =================
    # Stanno nei margini laterali (24px, sempre liberi dalle card) lungo tutta
    # l'altezza della finestra: trasparenti, dimensioni e rotazione casuali (ma con
    # seed fissa, così il layout non "salta" a ogni riavvio dell'app).
    def pony(top=None, left=None, right=None, bottom=None, size=20, angle_deg=0.0, flip=False, op=0.16):
        return ft.Text(
            "🐴", size=size, opacity=op,
            top=top, left=left, right=right, bottom=bottom,
            rotate=ft.Rotate(angle=angle_deg * 3.14159265 / 180),
            scale=ft.Scale(scale_x=-1 if flip else 1),
        )

    _pony_rng = random.Random(20240930)

    def random_pony(top: float, side: str):
        size = _pony_rng.uniform(14, 38)
        angle = _pony_rng.uniform(0, 360)
        flip = _pony_rng.random() < 0.5
        op = _pony_rng.uniform(0.07, 0.19)
        inset = _pony_rng.uniform(-4, 26 - size * 0.35)
        kwargs = {"left": inset} if side == "left" else {"right": inset}
        return pony(top=top, size=size, angle_deg=angle, flip=flip, op=op, **kwargs)

    deco = ft.Stack(
        [random_pony(top, side) for top, side in
         [(20, "left"), (60, "right"), (150, "left"), (210, "right"),
          (290, "left"), (350, "right"), (420, "left"), (480, "right"),
          (550, "left"), (600, "right"), (670, "left"), (720, "right")]],
        expand=True,
    )

    version_label = ft.Text(VERSION, size=10, color=TEXT_MUTED, opacity=0.6,
                             right=12, bottom=8)

    # ================= Pulsante inutile =================
    useless_dialog = ft.AlertDialog(
        modal=False,
        title=ft.Text("Il vero perché di questo programma"),
        content=ft.Text(
            "Questo programma è nato perché non avevo un cazzo da fare.\n\n"
            "Ma anche perché ti a... no no, in realtà non avevo proprio un cazzo da fare.\n\n"
            "(I cavallini nello sfondo sono lì a caso, eh.)",
            size=13,
        ),
        actions=[ft.TextButton("Sì, certo", on_click=lambda e: page.pop_dialog())],
    )

    useless_button = ft.Container(
        content=ft.Text("PULSANTE INUTILE", size=10, weight=ft.FontWeight.W_700,
                         color=ft.Colors.WHITE),
        bgcolor=ACCENT_1, border_radius=999,
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        rotate=ft.Rotate(angle=-4 * 3.14159265 / 180),
        left=8, bottom=6,
        on_click=lambda e: page.show_dialog(useless_dialog),
        ink=True,
        shadow=ft.BoxShadow(blur_radius=10, color="#40000000", offset=ft.Offset(0, 3)),
    )

    # ================= Layout =================
    page.add(
        ft.Stack(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            header,
                            ft.Container(
                                content=ft.Column(
                                    [
                                        status_card,
                                        ft.Row([btn_record, btn_play], spacing=12),
                                        device_card,
                                        options_card,
                                        ft.Row([btn_save, btn_load], spacing=12),
                                        hotkey_info,
                                        ft.Container(height=36),
                                    ],
                                    spacing=16,
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                                padding=ft.Padding.symmetric(horizontal=24),
                                expand=True,
                            ),
                        ],
                        spacing=6,
                    ),
                    expand=True,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
                        colors=[BG_TOP, BG_BOTTOM],
                    ),
                ),
                deco,
                version_label,
                useless_button,
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
