"""Presentation-only English translations; macro data and settings stay unchanged."""
from __future__ import annotations

import re
import flet as ft


EN = {
    "Pronto": "Ready",
    "Registra i movimenti del mouse per iniziare.": "Record your mouse movements to get started.",
    "REGISTRA  (F9)": "RECORD  (F9)",
    "RIPRODUCI  (F10)": "PLAY  (F10)",
    "INTERROMPI  (F9)": "STOP  (F9)",
    "INTERROMPI  (F10)": "STOP  (F10)",
    "Salva macro": "Save macro",
    "Carica macro": "Load macro",
    "Salva la macro in un file .mmr": "Save the macro to an .mmr file",
    "Apri una macro .mmr o .json": "Open an .mmr or .json macro",
    "EVENTI": "EVENTS",
    "DURATA": "DURATION",
    "RIPETIZIONE": "REPEAT",
    "Infinito": "Unlimited",
    "N volte": "N times",
    "Durata": "Duration",
    "volte": "times",
    "minuti": "minutes",
    "Ripete la macro finché non la fermi con F10.": "Repeats the macro until you stop it with F10.",
    "Ripete la macro il numero di volte indicato. Con le schede dei cavalli: metti quante schede hai aperto (un giro = un cavallo).": "Repeats the macro the number of times you choose. For horse tabs, enter the number of open tabs (one cycle per horse).",
    "Continua a ripetere per i minuti indicati; il giro in corso viene sempre finito.": "Repeats for the selected number of minutes, finishing the current cycle before stopping.",
    "VELOCITÀ DI RIPRODUZIONE": "PLAYBACK SPEED",
    "Durata minima di click e pause": "Minimum click and pause duration",
    "Protegge la pressione e la pausa tra i click a qualsiasi velocità. Lascia 150 ms; se ne perde ancora, prova 200 ms.": "Keeps clicks and the pauses between them long enough at any speed. Start at 150 ms; try 200 ms if clicks are still missed.",
    "Impostazioni": "Settings",
    "Fatto": "Done",
    "SCHEDE DEL BROWSER": "BROWSER TABS",
    "A fine giro chiudi la scheda (Ctrl+W)": "Close the tab after each cycle (Ctrl+W)",
    "Dopo ogni giro chiude la scheda del cavallo appena fatto e il browser passa da solo alla successiva. Più affidabile che cliccare la X della scheda, che si sposta man mano che le schede diminuiscono. Attivalo solo se durante la registrazione NON hai chiuso la scheda. Dopo l'ultimo giro non chiude nulla.": "Closes the completed tab between cycles so the browser moves to the next one. This is more reliable than clicking a tab's X, which moves as tabs close. Enable this only if you did NOT close the tab while recording. The last tab stays open.",
    "ATTESA PAGINA": "WAIT FOR PAGE",
    "Aspetta che la pagina sia pronta prima di cliccare": "Wait until the page is ready before clicking",
    "Prima di ogni click aspetta che il pulsante sia com'era in registrazione, poi clicca subito: se la pagina è già pronta non perde tempo. Serve con le schede aperte in background e con le pagine che si aggiornano dopo ogni click. Foto e nome del cavallo attorno al pulsante possono cambiare. Si attiva e disattiva dalla schermata principale.": "Before each click, waits until the button looks as it did while recording, then clicks at once: no time is lost when the page is already ready. It helps with tabs opened in the background and with pages that update after every click. The horse's picture and name around the button may change. Turn it on or off from the main screen.",
    "Attesa massima per ogni click": "Maximum wait per click",
    "Se dopo questo tempo il punto non è ancora pronto, la riproduzione si ferma invece di cliccare a vuoto.": "Stops playback if the target is still not ready after this time.",
    "Confronto": "Matching",
    "Preciso": "Strict",
    "Normale": "Normal",
    "Tollerante": "Tolerant",
    "Preciso: il punto deve essere quasi identico. Rischia di fermarsi per differenze minime.": "Strict: the target must look almost identical; small changes may stop playback.",
    "Normale: va bene nella maggior parte dei casi.": "Normal: suitable for most cases.",
    'Tollerante: usalo se si ferma dicendo "pagina non pronta" anche quando la pagina è a posto (es. il pulsante cambia un po\' colore o ha un\'animazione).': 'Tolerant: use this if playback reports "page not ready" when it is ready, for example when the button changes colour slightly or is animated.',
    "MODALITÀ SPERIMENTALE": "EXPERIMENTAL MODE",
    "Varia i tempi a ogni giro": "Vary timing each cycle",
    "Pausa casuale massima prima di un click": "Maximum random pause before a click",
    "Da 1 a 1000 ms. Prova 120 ms: aggiunge da 0 a 120 ms prima di un click, fino a 30 ms alla pressione e fino a 360 ms tra due giri.": "From 1 to 1000 ms. Try 120 ms: adds 0–120 ms before a click, up to 30 ms to its hold and up to 360 ms between cycles.",
    "Aggiunge piccole pause casuali e varia la durata delle pressioni. I punti di click restano identici e il click minimo viene sempre rispettato. La macro diventa meno ripetitiva e un po' più lenta; non garantisce che un sito non riconosca l'automazione.": "Adds small random pauses and varies click hold times. Click positions stay the same and the minimum duration is respected. Playback becomes less repetitive and slightly slower; this does not guarantee that a website will not detect automation.",
    "VELOCITÀ E PAUSE": "SPEED AND PAUSES",
    "1x riproduce la velocità registrata. Le pause lunghe vengono accelerate al massimo di 1,5x per non cliccare prima del caricamento della pagina.": "1x uses the recorded speed. Long pauses are sped up by at most 1.5x to avoid clicking before a page has loaded.",
    "MOUSE DA REGISTRARE": "MOUSE TO RECORD",
    "Su Linux F9/F10 e lo stop di emergenza funzionano quando questa finestra è attiva.": "On Linux, F9/F10 and emergency stop work while this window has focus.",
    "Come si usa": "How to use",
    "Ho capito": "Got it",
    "Apri nel browser tutte le schede dei cavalli da gestire e mettiti sulla prima.": "Open all the horse tabs you want to process and switch to the first one.",
    "Premi F9 (funziona anche dal browser) e fai a mano i compiti su quel cavallo, con calma e con la pagina già caricata.": "Press F9 (also works from the browser) and perform the tasks manually, with the page fully loaded.",
    'Premi F9 per fermare. Se usi l\'opzione "A fine giro chiudi la scheda", non chiudere la scheda durante la registrazione: lo farà il programma.': 'Press F9 to stop. If you enable "Close the tab after each cycle", do not close the tab while recording: the app will do it for you.',
    'In "Ripetizione" scegli "N volte" e metti quante schede hai aperto.': 'Under "Repeat", choose "N times" and enter the number of open tabs.',
    "Torna sulla prima scheda da fare e premi F10. Per fermare: F10, oppure Ctrl+Alt+F11 in emergenza.": "Return to the first tab and press F10. Stop with F10, or Ctrl+Alt+F11 in an emergency.",
    "Per non sbagliare i click": "Keep clicks accurate",
    '• Non spostare, ridimensionare o zoomare il browser tra registrazione e riproduzione.\n• Durante la riproduzione non toccare il mouse.\n• Registra sempre con le pagine già caricate.\n• Salva la macro ("Salva macro") per riusarla i giorni successivi.': '• Keep the browser position, size and zoom unchanged between recording and playback.\n• Do not touch the mouse during playback.\n• Record with pages fully loaded.\n• Use "Save macro" to reuse the recording later.',
    "PULSANTE INUTILE": "USELESS BUTTON",
    "Il vero perché di questo programma": "Why this app really exists",
    "Sì, certo": "Yeah, sure",
    "Questo programma è nato perché non avevo un cazzo da fare.\n\nMa anche perché ti a... no no, in realtà non avevo proprio un cazzo da fare.\n\n(I cavallini nello sfondo sono lì a caso, eh.)": "This app exists because I had fuck all to do.\n\nAlso because I lo... nope, I really just had fuck all to do.\n\n(The little horses in the background are totally random, obviously.)",
    "Macro in uso": "Macro in use",
    "Ferma la registrazione o riproduzione prima di salvare.": "Stop recording or playback before saving.",
    "Ferma la registrazione o riproduzione prima di caricare.": "Stop recording or playback before loading.",
    "Nessuna macro": "No macro",
    "Registra o carica una macro prima di salvarla.": "Record or load a macro before saving.",
    "Registra o carica prima una macro.": "Record or load a macro first.",
    "Macro salvata": "Macro saved",
    "Macro caricata": "Macro loaded",
    "Macro non compatibile": "Incompatible macro",
    "Errore nel salvataggio": "Could not save macro",
    "Errore nel caricamento": "Could not load macro",
    "Nessun mouse selezionato": "No mouse selected",
    "Scegli un dispositivo dalla lista qui sopra.": "Choose a mouse from the list above.",
    "Permessi insufficienti": "Insufficient permissions",
    "Aggiungi il tuo utente al gruppo 'input' (sudo usermod -aG input $USER) e rifai il login.": "Add your user to the 'input' group (sudo usermod -aG input $USER) and sign in again.",
    "Errore all'avvio della registrazione": "Could not start recording",
    "Errore nel fermare la registrazione": "Could not stop recording",
    "Registrazione in corso...": "Recording...",
    "Muovi il mouse e clicca normalmente.": "Move the mouse and click normally.",
    "Ferma la registrazione prima di riprodurre.": "Stop recording before playback.",
    "Registrazione completata": "Recording complete",
    "Schermo diverso dalla registrazione": "Screen layout has changed",
    "Imposta il numero di giri": "Set the number of cycles",
    "Inserisci il numero di giri.": "Enter the number of cycles.",
    "Scrivi un numero intero maggiore di zero prima di riprodurre.": "Enter a whole number greater than zero before playback.",
    "Errore all'avvio della riproduzione": "Could not start playback",
    "Riproduzione in corso...": "Playing...",
    "In attesa della pagina...": "Waiting for the page...",
    "Errore durante la riproduzione": "Playback error",
    "Riproduzione terminata": "Playback finished",
    "Imposta un numero intero di giri maggiore di zero.": "Set a whole number of cycles greater than zero.",
    "Il file non contiene una macro Windows o Linux valida.": "The file does not contain a valid Windows or Linux macro.",
    "Le dimensioni dello schermo nella macro non sono valide.": "The macro contains an invalid screen layout.",
    "La macro deve contenere una lista di eventi.": "The macro must contain a list of events.",
    "La macro contiene coordinate o tempi non validi.": "The macro contains invalid coordinates or timestamps.",
    "Gli eventi della macro devono avere tempi crescenti o uguali.": "Macro timestamps must be in non-decreasing order.",
    "La macro contiene un tipo di evento non valido.": "The macro contains an invalid event type.",
    "F9 registra/stop · F10 riproduci/stop · Ctrl+Alt+F11 stop di emergenza": "F9 record/stop · F10 play/stop · Ctrl+Alt+F11 emergency stop",
    "F9 registra/stop · F10 riproduci/stop · Ctrl+Alt+F11 stop di emergenza — funzionano anche dal browser": "F9 record/stop · F10 play/stop · Ctrl+Alt+F11 emergency stop — also work from the browser",
}


EN.update({
    "La chiusura schede richiede una macro con click.": "Closing tabs requires a macro with clicks.",
    "Durata minima della pressione": "Minimum press duration",
    "Pausa minima tra azioni": "Minimum pause between actions",
    "Parti da 150 ms per entrambi. Se perde click, aumenta soltanto la pausa tra azioni. La pausa protegge anche l'ultima azione prima di chiudere la scheda.": "Start at 150 ms for both. If clicks are missed, increase only the pause between actions. This pause also protects the last action before closing the tab.",
    "Confronta il pulsante prima di cliccare": "Match the button before clicking",
    "Confronta il pulsante con la registrazione. Un pulsante uguale non conferma che il sito abbia finito l'azione precedente: regola anche la pausa tra azioni. I click senza riferimento visivo usano soltanto le attese temporali.": "Matches the button against the recording. A matching button does not confirm that the site has finished the previous action: adjust the pause between actions too. Clicks without a visual reference use timing waits only.",
    "Le attese oltre 350 ms tra azioni vengono accelerate al massimo di 1,5x, anche se muovi il mouse. Pressione e pausa minima restano indipendenti dalla velocità.": "Waits longer than 350 ms between actions are sped up by at most 1.5x, even with mouse movements. Minimum press and pause durations are independent of speed.",
    "COLLAUDO": "TESTING",
    "Registra i tempi della riproduzione": "Record playback timings",
    "Salva un registro locale a fine riproduzione. Conta gli input inviati, non le azioni completate sul sito. Non salva immagini o indirizzi web.": "Saves a local report after playback. Counts inputs sent, not completed website actions. Does not save images or web addresses.",
    "Riproduzione interrotta": "Playback stopped",
    "Controlla il sito prima di avviare un altro giro.": "Check the site before starting another cycle.",
    "Impossibile salvare il registro dei tempi.": "Could not save the timing report.",
    "Torna sulla finestra del browser e avvia con F10.": "Return to the browser window and start with F10.",
    "La finestra destinataria non è più in primo piano. Riproduzione fermata.": "The target window has lost focus. Playback stopped.",
    "Il punto del click non appartiene alla finestra destinataria. Riproduzione fermata.": "The click target is outside the target window. Playback stopped.",
})

TEMPLATES = [
    (r"Registro: (.+)", r"Timing report: \1"),
    (r"(\d+) click senza riferimento visivo\.", r"\1 clicks without a visual reference."),
    (r"(\d+) eventi da (.+)", r"\1 events from \2"),
    (r"(\d+) eventi in (.+)", r"\1 events in \2"),
    (r"(\d+) eventi nella macro\.", r"\1 events in the macro."),
    (r"(\d+) eventi, (\d+) click\. Premi F10 per riprodurla\.", r"\1 events, \2 clicks. Press F10 to play."),
    (r"cicli completati: (\d+) · (.+)", r"completed cycles: \1 · \2"),
    (r"Il punto del click n° (\d+) non è ancora pronto\.", r"The target for click #\1 is not ready yet."),
    (r"Fermato: pagina non pronta al click n° (\d+)", r"Stopped: page not ready for click #\1"),
    (r"Questa macro è stata registrata su (.+)\. Registrala di nuovo su (.+): i movimenti vengono salvati in modo diverso\.", r"This macro was recorded on \1. Record it again on \2: the platforms store movements differently."),
    (r"La macro è stata registrata con uno schermo di (.+) \(o con monitor disposti diversamente\): i click finirebbero nei punti sbagliati\. Rimetti la stessa risoluzione/monitor o registrala di nuovo\.", r"The macro was recorded with a \1 screen or a different monitor layout. Restore that layout or record again to keep click positions accurate."),
    (r'Dopo (\d+) s quel punto non era ancora com\'era in registrazione\. Controlla la pagina; se era a posto, scegli il confronto "Tollerante" o aumenta l\'attesa massima\.', r'After \1 s the target still did not match the recording. Check the page; if it was ready, choose "Tolerant" matching or increase the maximum wait.'),
    (r"Tasti già usati da un altro programma: (.+) \(funzionano solo con la finestra dell'app attiva\)\.", r"Shortcuts used by another app: \1 (only work when this app has focus)."),
]


def translate(text: str, language: str) -> str:
    if language != "en" or not isinstance(text, str):
        return text
    if text in EN:
        return EN[text]
    # Riepilogo accanto a Impostazioni (l'attesa pagina ora è nella schermata principale).
    match = re.fullmatch(r"Chiusura schede: (ON|OFF) · Tempi: (fissi|variabili)", text)
    if match:
        tab, timing = match.groups()
        return f"Close tabs: {tab} · Timing: {'fixed' if timing == 'fissi' else 'varied'}"
    if text in ("Tempi: fissi", "Tempi: variabili"):
        return "Timing: fixed" if text.endswith("fissi") else "Timing: varied"
    for pattern, replacement in TEMPLATES:
        if re.fullmatch(pattern, text):
            return re.sub(pattern, replacement, text)
    return text


def localize_page(page, language: str):
    """Translate presentation controls only, including later updates and dialogs."""
    if language not in ("it", "en"):
        raise ValueError("Unsupported language")
    if language == "it":
        return

    def visit(control, seen):
        if not isinstance(control, ft.Control) or id(control) in seen:
            return
        seen.add(id(control))
        if isinstance(control, ft.Text):
            control.value = translate(control.value, language)
        for name in ("tooltip", "error_text", "hint_text"):
            value = getattr(control, name, None)
            if isinstance(value, str):
                setattr(control, name, translate(value, language))
        content = getattr(control, "content", None)
        if isinstance(content, str):
            control.content = translate(content, language)
        else:
            visit(content, seen)
        visit(getattr(control, "title", None), seen)
        for name in ("controls", "actions"):
            for child in getattr(control, name, []) or []:
                visit(child, seen)

    original_add = page.add
    original_update = page.update
    original_dialog = page.show_dialog

    def update(*args, **kwargs):
        seen = set()
        for control in list(page.controls) + list(getattr(page, "dialogs", []) or []):
            visit(control, seen)
        return original_update(*args, **kwargs)

    def show_dialog(dialog, *args, **kwargs):
        visit(dialog, set())
        return original_dialog(dialog, *args, **kwargs)

    def add(*controls):
        seen = set()
        for control in controls:
            visit(control, seen)
        return original_add(*controls)

    page.add = add
    page.update = update
    page.show_dialog = show_dialog
