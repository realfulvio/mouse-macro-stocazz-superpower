# Procedura del banco di prova (Windows)

Chiunque abbia una macchina Hyper-V/VMware/VirtualBox può rifare tutto. Tempo stimato: ~1 giornata di lavoro per strumento
escluse le prove di lunga durata (4 h) e il test di usabilità.

## 0. Prerequisiti

- Host con Windows 11 e un hypervisor. VM: Windows 11 Pro 64 bit, 4 vCPU, 8 GB RAM, 1920×1080, **senza** altro software oltre a Python 3.13+ (solo per i nostri script).
- Una VM di base, aggiornata, con Python e questo repository in `C:\bench`. **Snapshot "base"**. Per ogni strumento: ripristina "base" → installa solo quello → snapshot "<strumento>-installato".
- Nessun antivirus di terze parti; Microsoft Defender attivo con aggiornamenti (annota versione delle definizioni, `Get-MpComputerStatus`).
- Il PC fisico non è una VM pulita: **non** eseguire qui le prove di input (muoverebbero il mouse dell'utente).

## 1. Download e inventario

1. Scarica dalle fonti ufficiali elencate in `RIVALI.md`; non da mirror o siti di download.
2. Per ogni file: `tools\inventory.ps1 -Path C:\bench\dl -Out data\inventario.csv` (peso, SHA-256, firma, versione, Mark-of-the-Web).
3. Confronta lo SHA-256 con quello pubblicato dall'autore dove esiste (AutoHotkey lo scrive nelle note di rilascio).
4. `set VT_API_KEY=…` poi `python tools\vt_lookup.py data\inventario.csv data\virustotal.csv` (solo ricerca per hash; 'sconosciuto' ≠ pulito).
5. **SmartScreen**: scarica il file con il browser della VM (così ottiene il Mark-of-the-Web), avvialo con doppio clic e annota: nessun avviso / "Windows ha protetto il PC" / blocco da Smart App Control, con screenshot. Una volta per file, su VM appena ripristinata.

## 2. Macro di riferimento

`python reference_macro.py --out macros` (già in repo: `macros/reference.*`). Stessa spec per tutti.
- Mouse Macro Stocazz Superpower: `macros\reference.mmr` (si carica dal pannello, o `windows_main.py --run macros\reference.mmr`).
- AutoHotkey: `macros\reference.ahk` (F8 avvia, F12 esce).
- Gli altri **registrano a mano** la macro con il metronomo: `python tools\record_helper.py --spec macros\reference.spec.json`. Una registrazione sola per strumento, salvata in `macros\<strumento>\`; le 30 ripetizioni sono 30 *riproduzioni* della stessa registrazione. L'errore del registratore fa parte del risultato.
- Le hotkey di ogni strumento sono in `tools\tools.json`; quelle con "VERIFICARE" vanno lette dalla guida dello strumento e annotate lì prima di misurare.

## 3. Fedeltà (errore in px e in ms)

Per ogni scenario (S1–S5) e ogni strumento:

```
python tools\run_trials.py --tool <chiave in tools.json> --scenario <s1..s5> --runs 30 --out data
python analyze.py --spec macros\reference.spec.json --runs "data\<tool>\<scenario>\run_*.csv" --json data\<tool>\<scenario>\sommario.json
```

| Scenario | Come si imposta | Cosa dimostra |
|---|---|---|
| s1_dpi100 | 1920×1080, scala 100 % | baseline |
| s2_dpi125 | stessa risoluzione, scala 125 %, **macro registrata a 100 %** | strumenti non DPI-aware sbagliano posizione |
| s3_dpi150 | idem 150 % | idem |
| s4_multimon | due monitor virtuali (driver di display virtuale o PC reale con 2 monitor), secondo a destra con scala diversa; la spec va rigenerata con `--width`/`--origin-x` sul monitor scelto, e una variante con monitor a sinistra (coordinate negative) | virtual desktop, origine negativa, DPI misto |
| s5_elevata | la finestra obiettivo `tools\target_window.py` avviata **come amministratore**; macro lanciata da processo non elevato, poi da elevato; logger elevato | UIPI: «Applications are permitted to inject input only into applications that are at an equal or lesser integrity level» (doc. SendInput). Conta gli eventi che arrivano alla finestra (`--out` della finestra) contro quelli attesi |

Il logger va avviato con lo stesso livello del bersaglio più alto (UIPI). Durante le ripetizioni non toccare la VM.
Verdetto automatico: `analyze.py` (soglie in `thresholds.json`). Esiti attesi ma **non assunti**: a scala ≠ 100 % uno strumento non DPI-aware può fallire; annotarlo come risultato.

## 4. Risorse e avvio

```
tools\measure_resources.ps1 -Name <processo> -Seconds 60  -Out data\<tool>\idle_01.csv      # a riposo (finestra aperta, nulla in corso) x 5 ripetizioni
tools\measure_resources.ps1 -Name <processo> -Seconds 20  -Out data\<tool>\run_01.csv       # mentre riproduce la macro di riferimento (avviata a mano a t=0) x 30
tools\measure_startup.ps1 -Exe <percorso> -ProcName <processo> -Runs 30 -Out data\<tool>\startup.csv
```
CPU è la percentuale di **un** core (delta tempo CPU / delta tempo reale, tutto l'albero dei processi); RAM = Private Bytes e Working Set.
Strumenti a script (AHK) → misura `AutoHotkey64`. Strumenti senza finestra (tray) → `ok=0` nella colonna di avvio: dichiaralo, non inventare un tempo.

### Profilo ETW opzionale (per capire il perché di un valore alto)
`wpr -start CPU -start Latency -filemode`, esegui il caso, `wpr -stop data\<tool>\caso.etl`, poi WPA → "CPU Usage (Sampled)" per processo.
Solo se un caso fallisce la soglia: serve a spiegarlo, non a misurarlo.

## 5. Lunga durata (≥ 4 h)

Macro in loop continuo (infinito dello strumento, o loop ≥ 1000). In parallelo:
```
python logger\inputlogger.py --out data\<tool>\endurance_logger.csv --no-moves --duration 14700
tools\measure_resources.ps1 -Name <processo> -Seconds 14400 -IntervalMs 60000 -Out data\<tool>\endurance_resources.csv
python analyze_endurance.py --logger data\<tool>\endurance_logger.csv --resources data\<tool>\endurance_resources.csv --cycle-s 17.3
```
Gli arresti anomali si contano a mano (Visualizza eventi → Applicazioni) e vanno aggiunti al verdetto.

## 6. Giochi (manuale)

Solo giochi **senza anti-cheat e senza account da proteggere** (es. un titolo offline). Registra e riproduci 3 clic e un trascinamento in gioco; esito per strumento: l'input arriva sì/no, a schermo intero e in finestra senza bordi. Documenta gioco, versione, API di input (Raw Input / DirectInput se nota dalla documentazione ufficiale del gioco).

## 7. Matrice delle funzioni

`matrice-funzioni.csv`: una riga per funzione, una colonna per strumento, valori **sì / no / parziale / non verificato**, con la versione provata. Ogni "sì" va provato a mano nella VM, non letto dal sito. Compilare in sessione, con data.

## 8. Usabilità

Protocollo in `USABILITA.md`.

## 9. Pubblicazione dei dati

Tutti i CSV grezzi in `bench/data/<strumento>/<scenario>/`, gli screenshot SmartScreen/AV in `bench/data/evidenze/`, i sommari JSON generati da `analyze.py`. Nessun dato personale dei partecipanti: solo codici P01, P02…
