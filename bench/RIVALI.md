# Scelta dei rivali (Windows)

Criterio: strumenti che **un utente reale sceglierebbe al posto del nostro** per far ripetere a Windows una sequenza di mouse e tastiera,
coprendo quattro famiglie. Ogni riga dice cosa c'è di verificato alla data 2026-11-16 e da quale fonte primaria; il resto è da verificare in VM.

| Strumento | Famiglia | Perché è nel confronto | Verificato (fonte primaria) | Da verificare in VM |
|---|---|---|---|---|
| **TinyTask** 1.77 | Registratore minimale | È il concorrente diretto: registra e riproduce in un file piccolissimo, è quello che l'utente non esperto scarica per primo | Pagina download ufficiale tinytask.net con 1.45…1.77; già letti support/faq/revision history (`analisi/confronto-tinytask.md`): hotkey Ctrl+Alt+Shift+R / Ctrl+Shift+Alt+P, loop dalla 1.50, velocità personalizzate dalla 1.62 | Peso reale, loop infinito, formato .rec, DPI misto |
| **AutoHotkey** v2.0.31 | Linguaggio di scripting | Il riferimento per l'esperto: tutto il resto della categoria ci è costruito sopra o lo imita | Release GitHub ufficiale: 2.0.31 del 2026-10-25, setup 2,9 MB e zip 3,01 MB, SHA-256 pubblicati; release firmate con GPG | Latenza di `Send`/`Click`, avvio, SendMode, comportamento DPI |
| **Pulover's Macro Creator** 5.4.1 | Registratore + generatore di script (su AHK) | È il registratore con interfaccia più completo sul motore AHK | Repo ufficiale: 100 % AutoHotkey, registratore integrato, esporta in AHK; ultima release **v5.4.1 del 2021-09-24**, ultimo commit 2021-09-22 ("Fixed virus warnings"); Windows 7–10 dichiarati | Funziona su Win 11? Peso, avvio (richiede AHK v1) |
| **Jitbit Macro Recorder** | Commerciale | Rappresenta l'offerta a pagamento: registratore con editor, compilazione in exe | Sito ufficiale: registra mouse e tastiera, cicli, hotkey, converte macro in EXE (da `jitbit.com/macro-recorder`). **Non dichiarati nel testo letto**: versione, prezzo, limiti di prova | Versione/licenza/limiti della prova, peso, firma del codice |
| **Mini Mouse Macro** | Registratore gratuito leggero | Stessa nicchia di TinyTask, interfaccia più ricca | **Non verificato**: dal container il dominio ufficiale non risolve (DNS). Da fissare in VM con la fonte da cui lo si scarica | Tutto |
| **OP Auto Clicker** | Auto-clicker | Chi vuole solo "clicca qui ogni N ms" non cerca un registratore: è il nostro concorrente per il caso d'uso più semplice | Sito ufficiale: gratuito e open source, clic su punto fisso o sul cursore, ripetizioni o infinito, hotkey cambiabili, portabile, "bassa CPU". **Non registra macro** | Peso, CPU, versione |
| **Actiona** 3.11.5 | Automazione visuale + JS | Alternativa open source con editor di azioni e scripting; ha una versione Windows ufficiale | Repo ufficiale: C++, GPLv3, release 3.11.5 del 2026-11-02, build Windows MSVC in CI, installer con firma del codice a pagamento; azioni: clic, tasti, rotella, percorso del mouse, ricerca immagine | Registra? (la descrizione parla di creare azioni da editor/JS), peso, avvio, DPI |

## Esclusi, con il motivo

- **xdotool / ydotool, libei, uinput, Wayland/X11, perf**: Linux è fuori perimetro (richiesta di Luca, 2026-11-16).
- **Strumenti cloud/RPA enterprise** (UiPath, Power Automate Desktop): non sono sostituti di un registratore da 12 MB, hanno altri ordini di grandezza di installazione e licenza.
- **Macro del mouse dei produttori** (Logitech G Hub, Razer Synapse): legate all'hardware.

## Come si verifica ogni rivale (regole)

1. Si scarica **solo** dalla fonte ufficiale (sito del progetto o release GitHub), si registra URL, data, dimensione e SHA-256 (`tools/inventory.ps1`) e, dove l'autore lo pubblica, si confronta con l'hash dichiarato (AutoHotkey lo pubblica nelle note di rilascio).
2. Si installa nella VM pulita, si prova, si annota versione mostrata nell'About.
3. Documentazione ufficiale delle API: SetWindowsHookEx (hook LL), SendInput (soggetta a UIPI: «Applications are permitted to inject input only into applications that are at an equal or lesser integrity level», e il fallimento per UIPI non è riportato dal valore di ritorno), Raw Input.
   Per le funzioni dei rivali si leggono il manuale ufficiale e, se aperto, il sorgente.
4. Issue e changelog: solo repository o pagine ufficiali del progetto.
