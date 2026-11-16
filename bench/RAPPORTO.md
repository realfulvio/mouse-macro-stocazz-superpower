# Mouse Macro Stocazz Superpower contro i rivali: analisi comparativa (Windows)

Data: 2026-11-16 · Versione in prova: Windows v1.2.3 · Perimetro: solo Windows (Linux escluso da Luca).

## 1. Cosa è stato fatto davvero (leggi prima questo)

**Misurato** (2026-11-16, due esecuzioni complete dello stesso banco sui runner GitHub Actions `windows-latest`, vedi sezione 1b): fedeltà di posizione e di tempo con un logger di input esterno (30 ripetizioni, 870 punti di posizione e 840 intervalli per strumento ed esecuzione), CPU e memoria a riposo (60 s, 57 campioni), peso del pacchetto, e una **riga di riferimento "ideale"** (riproduzione SendInput con attese QPC) che dice quanto rumore mette l'ambiente da solo. Strumenti in prova: MMSS 1.2.3 e AutoHotkey 2.0.31; TinyTask 1.77 è stato scaricato dal sito ufficiale e avviato ma **non riproduce la macro in questo ambiente**, quindi la sua fedeltà è non misurata (sezione 1b).

**Costruito e verificato**: banco completo (logger, macro di riferimento identica, orchestratore CI, misure di risorse/avvio, inventario con hash, ricerca VirusTotal, analisi con mediana/p95/varianza, soglie congelate prima di misurare, protocollo di usabilità con SUS). 11 test automatici sull'analisi.

**Non misurato** (nessun numero stimato, elenco in `data/STATO-MISURE.md`): rivali Pulover, Jitbit, Mini Mouse Macro, OP Auto Clicker, Actiona (non girati), CPU in esecuzione, tempo di avvio (lo script non ha prodotto dati per MMSS: da correggere), DPI misto, multi-monitor, finestre elevate, giochi, macro di ore, VirusTotal (il container non raggiunge virustotal.com), SmartScreen, usabilità con persone, matrice funzioni in gran parte "non verificato".

## 1b. Risultati misurati e limiti dell'ambiente

Ambiente: runner GitHub condiviso, Windows Server 2025, CPU AMD EPYC (Family 25), 2 vCPU, sessione interattiva, schermo 1920×1080 a 96 DPI, **un solo monitor**. Non è una VM dedicata né hardware reale: il tempo non è in tempo reale e altri carichi condividono l'host. I numeri valgono per questo ambiente. Dati grezzi e sommari: `data/runner-github/<run>/<strumento>/`.

| | MMSS 1.2.3 (2 esecuzioni) | AutoHotkey 2.0.31 (2 esecuzioni) | Riferimento ideale (1) | TinyTask 1.77 |
|---|---|---|---|---|
| Errore di posizione (mediana / p95) | 0 / 0 px | 0 / 0 px | 0 / 0 px | non misurato |
| Eventi persi / extra su 870 | 0 / 0 | 0 / 0 | 0 / 0 | **870 persi: non riproduce** |
| Errore di intervallo, mediana | **4,80 e 4,91 ms** | 8,25 e 8,56 ms | 0,70 ms | non misurato |
| Errore di intervallo, p95 | 29,0 e 29,0 ms | 36,1 e 37,7 ms | 28,2 ms | non misurato |
| Deriva massima, p95 | 38,8 e 42,2 ms | 44,0 e 43,3 ms | 35,9 ms | non misurato |
| CPU a riposo (mediana, p95; % di un core) | **4,5 e 4,5 · 7,5 e 7,6** | 0 · 0 | n.a. | 0 · 0 |
| Memoria privata a riposo | 48,0 e 47,7 MB | 3,0 e 2,9 MB | n.a. | 4,6 MB |
| Peso scaricato | 19,05 MB (ZIP) | 3,16 MB (ZIP) | n.a. | 5,68 MB (exe) |

Lettura rispetto alle soglie congelate (`thresholds.json`, non modificate dopo le misure):

- **Posizione**: passa (0 px) per MMSS e AutoHotkey. L'ipotesi "errore di 1 px per la normalizzazione 65535/(w−1)" **non è confermata** a 1920×1080 e 96 DPI: 870 punti su 870 esatti. Resta aperta per altre scale DPI e altri monitor (non provati).
- **Intervallo, mediana ≤ 5 ms**: MMSS passa **di misura** (4,80 e 4,91 contro 5; il margine è 0,1–0,2 ms, quindi non è un passaggio solido: ogni nuova attesa o lavoro nel thread di riproduzione può farlo diventare un fallimento). AutoHotkey non passa (8,3–8,6 ms) con lo script generato dal banco (`reference.ahk`: la sua mediana dipende da come è scritto lo script, non è un limite assoluto del programma).
- **Intervallo, p95 ≤ 16 ms: non valutabile qui.** Anche il riferimento ideale fa 28,2 ms: il p95 è dominato dall'ambiente (il runner condiviso ritarda la consegna degli eventi al logger e/o la riproduzione). Il p95 di MMSS (29,0) è indistinguibile da quello ideale; non dimostra né esclude un problema. Serve hardware reale o una VM con core dedicati.
- **Deriva p95 ≤ 50 ms**: passa per tutti (38,8–44,0 ms), ma è anch'essa vicina al riferimento ideale (35,9).
- **CPU a riposo ≤ 2 % di un core: MMSS non passa** (mediana 4,5 %, p95 7,5 %, ripetuto in due esecuzioni; con 1024×768 la prima esecuzione aveva dato 6,0 % / 10,5 %). AutoHotkey 0 %, TinyTask 0 %. È coerente con le misure di sessioni precedenti (animazione Bambola) e **resta il difetto misurato più chiaro**.
- **Memoria ≤ 150 MB a riposo**: passa (48 MB), ma è 16 volte AutoHotkey.
- **Peso ≤ 25 MB**: passa (19,05 MB; 6 volte AutoHotkey, 3,4 volte TinyTask con editor).

**TinyTask**: scaricato da `dl.tinytask.net/with-editor.exe` (5.678.424 byte, SHA-256 `4ef4cae2…bbb5` registrato qui perché l'autore non ne pubblica uno), avviato (2 processi, 4,6 MB, 0 % CPU a riposo). La registrazione con i tasti rapidi Ctrl+Maiusc+Alt+R (input iniettato con SendInput, come farebbe una persona) e la riproduzione con Ctrl+Maiusc+Alt+P non hanno prodotto nessun evento (870 persi su 870), e il rilevamento della finestra per il tempo di avvio è scaduto a 30 s in tutte le 15 prove. **Causa non accertata.** Ipotesi non verificata: la documentazione Microsoft dice che i ganci "journal" (WH_JOURNALRECORD/PLAYBACK) sono non supportati da Windows 11 in poi; se TinyTask li usa potrebbe non funzionare su Server 2025, ma non so se li usa. Per questo non scrivo che "TinyTask non funziona su Windows 11": va provato su un PC Windows 10/11 reale.

## 2. Rivali e perché

Famiglie coperte (dettaglio e fonti in `RIVALI.md`): registratore minimale (TinyTask, Mini Mouse Macro), scripting (AutoHotkey), registratore + generatore (Pulover), commerciale (Jitbit), auto-clicker (OP Auto Clicker), automazione visuale/JS (Actiona).
Fatti verificati oggi su fonti ufficiali: AutoHotkey 2.0.31 (2026-10-25, setup 2,9 MB, zip 3,01 MB); Pulover 5.4.1 **ferma al 2021-09-24**; Actiona 3.11.5 (2026-11-02, GPLv3, firma del codice a pagamento dichiarata); TinyTask 1.77 (2019); OP Auto Clicker gratuito/open source e **solo auto-click**, non registra; Jitbit registra mouse e tastiera, ha cicli, hotkey e compila in EXE (versione, prezzo e limiti di prova non dichiarati nel testo letto). Mini Mouse Macro: dominio ufficiale non raggiungibile dal container, nulla verificato.
Fatto API (documentazione Microsoft di SendInput): è soggetta a UIPI, si inietta solo verso processi con integrità uguale o inferiore, e il fallimento per UIPI non è distinguibile dagli altri.

## 3. Metodo e soglie

`PREREGISTRAZIONE.md` e `thresholds.json` (congelate il 2026-11-16 prima di misurare): posizione mediana ≤ 1 px, p95 ≤ 2 px; intervalli mediana ≤ 5 ms, p95 ≤ 16 ms; zero eventi persi o extra; CPU ≤ 2 % a riposo e ≤ 5 % in esecuzione (di un core); Private Bytes ≤ 150/200 MB; avvio ≤ 2 s; pacchetto ≤ 25 MB; 4 h senza crash e ≤ 1 MB/h di crescita; 0 rilevamenti AV e nessun blocco SmartScreen; usabilità ≥ 80 % successo, ≤ 120 s, SUS ≥ 68 con ≥ 5 persone. Procedura in `PROCEDURA.md`.

## 4. Dove vinciamo (dai fatti, non dalle misure)

| Area | Fatto | Fonte |
|---|---|---|
| Sicurezza di riproduzione | stop di emergenza globale Ctrl+Alt+F11, rilascio di tasti/pulsanti, controllo geometria schermo, snapshot dei pixel prima del clic | codice del repo |
| Aggiornamenti | pallino, SHA-256 verificato, installazione con un clic | repo |
| Formato | `.mmr` JSON leggibile e validato | repo |
| Rotella | registrata e riprodotta | repo |
| Manutenzione | release 1.2.3 del 2026-11-01; Pulover fermo al 2021, TinyTask al 2019 | repo, repo Pulover, tinytask.net |
| Lingua / licenza | italiano, open source | repo |
| Macro avviabile senza exe | `.cmd` + `.mmr`, niente exe compilato da far valutare all'antivirus | repo |

## 5. Dove perdiamo o rischiamo (da confermare col banco)

| # | Gap | Evidenza | Stato |
|---|---|---|---|
| 1 | **Costo a riposo dell'animazione Bambola**: mediana 4,5 % di un core (p95 7,5 %) misurata a riposo, due esecuzioni, contro soglia 2 %; AutoHotkey e TinyTask 0 %. Precedenti (VM senza GPU, metodo diverso): 9,3 % pannello, 13,2 % Copertina, 6–7 % Micro | **misurato**, `data/runner-github/` | **Corretto nel sorgente, da rilasciare**: dopo la modifica 1,48 · 1,48 · 1,33 % (prima 4,22–4,61 %), sotto la soglia 2 %, stessi 24 fotogrammi/s, pixel identici (`data/runner-github/ottimizzazione-cpu-bambola.md`). Non ancora misurato sul pacchetto exe né in esecuzione |
| 2 | **Peso, memoria e avvio**: ZIP v1.2.3 19,05 MB (non 12: quello era la v1.1.1) contro AHK 3,16 MB e TinyTask 5,68 MB; 48 MB di memoria contro 3 MB (AHK) e 4,6 MB (TinyTask). Avvio MMSS misurato: mediana 0,378 s, p95 0,402 s (15 avvii, 14 a caldo, runner condiviso), sotto la soglia di 2 s; per i rivali non misurato | **misurato** (peso, memoria) | passa le soglie assolute, perde il confronto relativo; deriva dalla struttura (Python embedded), non è un obiettivo |
| 3 | **Antivirus/SmartScreen**: exe non firmato; issue #1 SentinelOne; Actiona dichiara la firma del codice | repo | da misurare (VirusTotal, SmartScreen) |
| 4 | **Finestre elevate**: SendInput è soggetta a UIPI e il codice segnala solo il rifiuto di `SendInput`; se il bersaglio è elevato l'iniezione può non arrivare senza messaggio chiaro | doc. Microsoft + `checked_input` in `windows_backend.py` | **ipotesi dal codice**: prova S5 |
| 5 | **Errore di posizione di 1 px**: ipotesi dal codice (`round(x·65535/(w−1))` con VIRTUALDESK) | `CheckedMouse._position_set` | **non confermata** a 1920×1080, 96 DPI, un monitor: 0 px su 870 punti (anche per il riferimento ideale). Aperta per altre scale/monitor |
| 6 | **Portabilità tra configurazioni schermo**: una macro con geometria diversa viene rifiutata ("Schermo o monitor diversi") | `macro/runner.py` | è una scelta di sicurezza; i rivali probabilmente non la fanno (da verificare) |
| 7 | **DPI misto / multi-monitor**: la resa in pixel fisici è dichiarata (Per-Monitor-V2) ma mai misurata con logger esterno | codice | prova S2–S4 |
| 9 | **Margine sull'intervallo**: la mediana dell'errore di intervallo è 4,80–4,91 ms contro soglia 5 ms (riferimento ideale 0,70 ms): ~4 ms di attesa/dispatch in più per evento | **misurato**; passa di 0,1–0,2 ms | proteggere da regressioni; capire da dove vengono i ~4 ms |
| 8 | Impostazioni non si riscala a caldo col DPI; pannello troppo alto a 1024×768 al 125 % | memoria di progetto | difetti noti |

## 6. Cosa fare e in che ordine (senza regressioni)

Ogni intervento passa dal banco **prima e dopo** con la stessa procedura; si pubblica solo se nessuna soglia peggiora rispetto alla versione precedente (regola di Luca).

1. **Fatto in parte**: banco collaudato su runner Windows, baseline 1.2.3 e AHK misurate (sezione 1b). Mancano: avvio (script da correggere per MMSS), CPU in esecuzione, TinyTask su un Windows 10/11 reale, e il p95 degli intervalli su hardware dedicato (qui non valutabile).
2. **Gap 1, costo a riposo: fatto nel sorgente** (commit daf12ae e 2507bce): `render()` non riscrive testo e stato dei controlli se invariati (ogni riscrittura ridisegna il controllo owner-draw, 10 volte al secondo) e la mascotte si ridisegna per fotogramma con tre copie invece di ricostruire una tela GDI+ a 24 fps. CPU a riposo da 4,22–4,61 % a 1,33–1,48 % di un core, stessi 24 fotogrammi/s, pixel identici (97/97). Dati: `data/runner-github/ottimizzazione-cpu-bambola.md`. Da fare: misura sul pacchetto exe e in registrazione/riproduzione, poi rilascio quando lo decide il coordinatore.
3. **Gap 4 (UIPI) e prove di posizione su altre scale DPI/monitor**: la correzione a 1 px per il gap 5 **non è giustificata** dai dati (0 px di errore); non scriverla. Resta l'avviso esplicito prima di riprodurre su un bersaglio elevato (non provato) e la prova con DPI misto su hardware reale.
4. **Gap 3, firma e antivirus**: firma Authenticode del launcher (costo in soldi e tempo, non codice), segnalazione dei falsi positivi ai produttori; ripetere VirusTotal/SmartScreen a ogni release.
5. **Gap 7 e 8**: scala DPI a caldo per Impostazioni e altezza del pannello; poi prova su PC reale con 2 monitor a scale diverse.
6. Funzioni dei rivali non nostre (Jitbit compila in EXE, Actiona ha ricerca immagine e scripting): **non seguirle** finché il target resta "registratore semplice e sicuro"; valutare solo se il test di usabilità lo chiede.

## 7. Per rifare tutto

`bench/README.md` → `PROCEDURA.md`. Dati grezzi in `bench/data/runner-github/`, sommari generati da `analyze.py`. Il banco gira da solo su GitHub Actions (`.github/workflows/bench.yml`, a ogni push su `bench/**` o da avvio manuale); i dati grezzi finiscono anche nei rami `bench-data/<run>-<strumento>`.
