# Mouse Macro Stocazz Superpower contro i rivali: analisi comparativa (Windows)

Data: 2026-11-16 · Baseline comparativa: Windows v1.2.3; Windows v1.2.5 collaudata sullo ZIP finale · Perimetro: solo Windows (Linux escluso da Luca).

## 1. Cosa è stato fatto davvero (leggi prima questo)

**Misurato** (2026-11-16, due esecuzioni complete dello stesso banco sui runner GitHub Actions `windows-latest`, vedi sezione 1b): fedeltà di posizione e di tempo con un logger di input esterno (30 ripetizioni, 870 punti di posizione e 840 intervalli per strumento ed esecuzione), CPU e memoria a riposo (60 s, 57 campioni), peso del pacchetto, e una **riga di riferimento "ideale"** (riproduzione SendInput con attese QPC) che dice quanto rumore mette l'ambiente da solo. Strumenti in prova: MMSS 1.2.3 e AutoHotkey 2.0.31; TinyTask 1.77 è stato scaricato dal sito ufficiale e avviato ma **non riproduce la macro in questo ambiente**, quindi la sua fedeltà è non misurata (sezione 1b).

**Costruito e verificato**: banco completo (logger, macro di riferimento identica, orchestratore CI, misure di risorse/avvio, inventario con hash, ricerca VirusTotal, analisi con mediana/p95/varianza, soglie congelate prima di misurare, protocollo di usabilità con SUS). 13 test automatici sull'analisi.

**Non misurato** (nessun numero stimato, elenco in `data/STATO-MISURE.md`): fedeltà di Pulover, Jitbit, Mini Mouse Macro, OP Auto Clicker e Actiona; RAM attiva, DPI misto, multi-monitor, giochi, macro di ore, VirusTotal (nessuna chiave API disponibile in questa sessione), SmartScreen, usabilità con persone, matrice funzioni in gran parte "non verificato".

## 1b. Risultati misurati e limiti dell'ambiente

Ambiente: runner GitHub condiviso, Windows Server 2025, CPU AMD EPYC (Family 25; alcuni nuovi job usano Intel Family 6, come indicato negli inventari), 2 vCPU, sessione interattiva, schermo 1920×1080 a 96 DPI, **un solo monitor**. Non è una VM dedicata né hardware reale: il tempo non è in tempo reale e altri carichi condividono l'host. I numeri valgono per questo ambiente. Dati grezzi e sommari: `data/runner-github/<run>/<strumento>/`.

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

### CPU attiva, riposo ripetuto e UIPI (PR #41)

Misure dal **sorgente**, non dall'exe; dettagli, condizioni e JSON in
[`data/runner-github/cpu-attiva-uipi.md`](data/runner-github/cpu-attiva-uipi.md).
Run CPU `43941664289`, commit `f146f7c`, tre finestre da 15 s per carico:
registrazione **9,06 · 7,71 · 7,40%** (non passa ≤5), riproduzione densa
**14,37 · 14,58 · 14,37%** (non passa), riferimento rado
**3,12 · 3,33 · 3,02%** (passa). CPU media della finestra in % di un core.
La conferma finale prima del merge (`43942991759`) e la tornata con avviso (`43947162655`) sono conservate nei rapporti di dettaglio: persiste il costo sopra soglia della riproduzione densa e la variabilità a riposo/in registrazione.
La prima tornata (`43939878453`, stesso codice app) dava registrazione
4,17 · 4,06 · 4,27% e riproduzione densa 10,73 · 12,19 · 13,02%.
Il riposo ora dà **2,11 · 2,73 · 2,50%** (non passa ≤2), contro
1,48 · 0,78 · 1,56% della prima tornata. Non è un A/B di codice diverso:
variabilità del runner, ordine degli step e carico limitano il confronto.
Il miglioramento Bambola documentato non garantisce il rispetto della soglia
su tutti i runner. Pixel equivalenti 97/97; 480 · 481 · 480 WM_PAINT in 20 s.

UIPI, run `43941664269`: attesi 13 down / 13 up / 3 wheel. Iniettore e MMSS
alto→alto consegnano **13/13/3**; medio→alto consegnano **0/0/0**, uscita 0.
MMSS termina entrambi i casi con stato **pronto** e «Completati 1 giri.».
Il controllo passa, la segnalazione del blocco **non passa**: difetto confermato.
Una prova per caso su token medio ristretto, non UAC interattivo o desktop sicuro.

Avvio MMSS v1.2.3, run `43927100173`: 15 avvii, 14 a caldo, mediana
**0,378 s**, p95 **0,402 s**, primo avvio **0,452 s**: passa ≤2/3 s.
Avvio di AutoHotkey/TinyTask non misurato; gli altri rivali sono descritti sotto. Il verde della CI indica che gli script sono
terminati, non che le soglie prestazionali o tutti i comportamenti siano passati.

### Correzione UIPI e risorse degli altri rivali

PR #41 unita dopo tutti i controlli verdi. Il controllo preflight della PR #44 impedisce ora l'avvio verso un bersaglio noto di integrità superiore, con avviso «Esegui come amministratore». Prova reale `43944349396`: C alto→alto 13/13/3 e un giro; D medio→alto 0/0/0, stato errore, zero giri, macro non partita. Il confronto dal sorgente `43944349328` usa 30 ripetizioni per lato: posizione 0 px e zero eventi persi/extra; mediana intervalli 4,3065→4,2390 ms; deriva p95 32,4054→31,9729 ms. Nessuna soglia passa→non passa; p95 intervalli sopra soglia in entrambi e non validabile su runner condivisi. [Dati, hash del codice temporizzato e limiti](data/runner-github/avviso-uipi.md).

Misurati peso, avvio e riposo di Pulover 5.4.1, Jitbit 5.9.0.0 in prova, OP Auto Clicker 4.1 , Actiona 3.11.5 e Mini Mouse Macro MSI (launcher 1.0.0.0). [Tabella e dati grezzi](data/runner-github/rivali-risorse.md). Nella tornata `43945606448` passano le soglie assolute di CPU, memoria e avvio; Actiona supera il peso massimo (75,835 MB contro 25). Actiona è misurato con il dialogo iniziale di aggiornamento aperto; Jitbit in una tornata precedente aveva un avvio scaduto. Mini Mouse Macro completa le quattro soglie nel run `43947060305`; versione e stato del processo figlio hanno i limiti dichiarati nel dettaglio. Hardware variabile fra job: nessuna classifica assoluta ricavata da questi tempi. **Fedeltà non misurata per tutti e cinque i nuovi rivali.**

### Collaudo del pacchetto Windows 1.2.5 contro 1.2.4

Run `43951916704`, build `43951421876`: stessa procedura su due runner, esatto ZIP da 19.053.039 byte, hash `def843426d25dc0d12a5344c750a156e81f3b5567390df816337908c09174975`. Nessuna soglia prima passata diventa fallita. Posizione 0 px, eventi persi/extra zero; mediana intervalli 4,2370→4,0180 ms; p95 28,6324→28,7958 ms non validabile qui. CPU media di tre finestre: idle 1,8467→1,9567%, registrazione 5,6600→4,9300%, densa 13,4367→13,1267% (ancora sopra soglia), rada 2,6733→2,8467%. Singole finestre e tornate precedenti superano le soglie idle/registrazione: non è un miglioramento stabile dimostrato.

Riposo 60 s: CPU media 1,5481→1,8094%, memoria privata massima 47,98→48,15 MiB. Avvio caldo mediana 0,277→0,361 s, p95 0,37445→0,37270 s, 15/15 avvii per lato. Exe, cmd, installazione per utente e pixel 97/97 passano. Il candidato avvisa e non parte verso il bersaglio elevato; controllo alto→alto 13/13/3. [Rapporto completo, limiti e dati](../docs/ESITO-COLLAUDO-v1.2.5.md). Le prove CPU usano runtime e file estratti dallo ZIP, la fedeltà il suo pythonw.exe: non sono più soltanto misure del checkout. Restano esclusi RAM attiva e prove hardware elencate sopra.

## 2. Rivali e perché

Famiglie coperte (dettaglio e fonti in `RIVALI.md`): registratore minimale (TinyTask, Mini Mouse Macro), scripting (AutoHotkey), registratore + generatore (Pulover), commerciale (Jitbit), auto-clicker (OP Auto Clicker), automazione visuale/JS (Actiona).
Fatti verificati oggi su fonti ufficiali: AutoHotkey 2.0.31 (2026-10-25, setup 2,9 MB, zip 3,01 MB); Pulover 5.4.1 **ferma al 2021-09-24**; Actiona 3.11.5 (2026-11-02, GPLv3, firma del codice a pagamento dichiarata); TinyTask 1.77 (2019); OP Auto Clicker gratuito/open source e **solo auto-click**, non registra; Jitbit registra mouse e tastiera, ha cicli, hotkey e compila in EXE (versione, prezzo e limiti di prova non dichiarati nel testo letto). Mini Mouse Macro: verificati download, hash pubblicato e installazione MSI dal progetto SourceForge turnssoft; esiti di avvio/risorse nel rapporto collegato.
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
| Manutenzione | baseline MMSS 1.2.3; aggiornamento 1.2.5 collaudato il 2026-11-16; Pulover 5.4.1 del 2021, TinyTask 1.77 del 2019 | repo, repo Pulover, tinytask.net |
| Lingua / licenza | italiano, open source | repo |
| Macro avviabile senza exe | `.cmd` + `.mmr`, niente exe compilato da far valutare all'antivirus | repo |

## 5. Dove perdiamo o rischiamo: stato delle verifiche

| # | Gap | Evidenza | Stato |
|---|---|---|---|
| 1 | **Costo a riposo dell'animazione Bambola**: mediana 4,5 % di un core (p95 7,5 %) misurata a riposo, due esecuzioni, contro soglia 2 %; AutoHotkey e TinyTask 0 %. Precedenti (VM senza GPU, metodo diverso): 9,3 % pannello, 13,2 % Copertina, 6–7 % Micro | **misurato**, `data/runner-github/` | **Misurato, soglia non stabilmente rispettata**: A/B Bambola migliorato (1,33–1,48%); nuova tornata riposo 2,11–2,73% e registrazione 7,40–9,06% non passano. Riproduzione densa 14,37–14,58% non passa; rada 3,02–3,33% passa. Sorgente e ZIP finale misurati: CPU media 1.2.5 idle 1,9567%, registrazione 4,93%, densa 13,1267%, rada 2,8467%; soglie non stabili tra finestre/runner |
| 2 | **Peso, memoria e avvio**: ZIP v1.2.3 19,05 MB (non 12: quello era la v1.1.1) contro AHK 3,16 MB e TinyTask 5,68 MB; 48 MB di memoria contro 3 MB (AHK) e 4,6 MB (TinyTask). Avvio MMSS misurato: mediana 0,378 s, p95 0,402 s (15 avvii, 14 a caldo, runner condiviso), sotto la soglia di 2 s; altri rivali misurati nel rapporto risorse | **misurato** (peso, memoria, avvio) | passa le soglie assolute, perde il confronto relativo; deriva dalla struttura (Python embedded), non è un obiettivo |
| 3 | **Antivirus/SmartScreen**: exe non firmato; issue #1 SentinelOne; Actiona dichiara la firma del codice | repo | **non misurato** (VirusTotal, SmartScreen) |
| 4 | **Finestre elevate**: SendInput è soggetta a UIPI e il codice segnala solo il rifiuto di `SendInput`; se il bersaglio è elevato l'iniezione può non arrivare senza messaggio chiaro | doc. Microsoft + `checked_input` in `windows_backend.py` | **Misurato, correzione verificata**: prima D dichiarava un giro pur consegnando zero eventi; dopo si ferma prima di partire con avviso amministratore. C resta 13/13/3. Limiti del controllo descritti nel rapporto UIPI |
| 5 | **Errore di posizione di 1 px**: ipotesi dal codice (`round(x·65535/(w−1))` con VIRTUALDESK) | `CheckedMouse._position_set` | **non confermata** a 1920×1080, 96 DPI, un monitor: 0 px su 870 punti (anche per il riferimento ideale). Aperta per altre scale/monitor |
| 6 | **Portabilità tra configurazioni schermo**: una macro con geometria diversa viene rifiutata ("Schermo o monitor diversi") | `macro/runner.py` | **verificato nel codice**, scelta di sicurezza; confronto con i rivali **non misurato** |
| 7 | **DPI misto / multi-monitor**: la resa in pixel fisici è dichiarata (Per-Monitor-V2) ma mai misurata con logger esterno | codice | **non misurato**: prova S2–S4 |
| 9 | **Margine sull'intervallo**: la mediana dell'errore di intervallo è 4,80–4,91 ms contro soglia 5 ms (riferimento ideale 0,70 ms): ~4 ms di attesa/dispatch in più per evento | **misurato**; passa di 0,1–0,2 ms | proteggere da regressioni; capire da dove vengono i ~4 ms |
| 8 | Impostazioni non si riscala a caldo col DPI; pannello troppo alto a 1024×768 al 125 % | memoria di progetto | **non misurato in questo banco**; precedente segnalazione da riverificare |

## 6. Cosa fare e in che ordine (senza regressioni)

Ogni intervento passa dal banco **prima e dopo** con la stessa procedura; si pubblica solo se nessuna soglia peggiora rispetto alla versione precedente (regola di Luca).

1. **Fatto in parte**: banco collaudato su runner Windows, baseline 1.2.3 e AHK misurate (sezione 1b). Avvio MMSS, CPU attiva dal sorgente e UIPI ora misurati (§1b). CPU del pacchetto ora misurata nel confronto 1.2.4→1.2.5. Mancano RAM attiva, fedeltà dei cinque nuovi rivali, TinyTask su Windows 10/11 reale e p95 su hardware dedicato.
2. **Gap 1, costo a riposo: fatto nel sorgente** (commit daf12ae e 2507bce): `render()` non riscrive testo e stato dei controlli se invariati (ogni riscrittura ridisegna il controllo owner-draw, 10 volte al secondo) e la mascotte si ridisegna per fotogramma con tre copie invece di ricostruire una tela GDI+ a 24 fps. CPU a riposo da 4,22–4,61 % a 1,33–1,48 % di un core, stessi 24 fotogrammi/s, pixel identici (97/97). Dati: `data/runner-github/ottimizzazione-cpu-bambola.md`. Nuove misure CPU: soglia non stabilmente rispettata a riposo/in registrazione; riproduzione densa sopra soglia, rada sotto. Prima di cambiare `_wait_until`, Luca deve approvare proposta e A/B descritti in `data/runner-github/cpu-attiva-uipi.md`. Timing invariato. La successiva richiesta di Luca autorizza la release Windows 1.2.5 dopo il collaudo dell’esatto ZIP; l’ottimizzazione delle attese resta una proposta da approvare separatamente.
3. **Gap 4 (UIPI) e prove di posizione su altre scale DPI/monitor**: la correzione a 1 px per il gap 5 **non è giustificata** dai dati (0 px di errore); non scriverla. Blocco silenzioso UIPI confermato e avviso implementato in PR #44, con test mock e prova C/D prima/dopo; tempi invariati. DPI misto resta da provare su hardware reale.
4. **Gap 3, firma e antivirus**: firma Authenticode del launcher (costo in soldi e tempo, non codice), segnalazione dei falsi positivi ai produttori; ripetere VirusTotal/SmartScreen a ogni release.
5. **Gap 7 e 8**: scala DPI a caldo per Impostazioni e altezza del pannello; poi prova su PC reale con 2 monitor a scale diverse.
6. Funzioni dei rivali non nostre (Jitbit compila in EXE, Actiona ha ricerca immagine e scripting): **non seguirle** finché il target resta "registratore semplice e sicuro"; valutare solo se il test di usabilità lo chiede.

## 7. Per rifare tutto

`bench/README.md` → `PROCEDURA.md`. Dati grezzi in `bench/data/runner-github/`, sommari generati da `analyze.py`. Il banco gira da solo su GitHub Actions (`.github/workflows/bench.yml`, a ogni push su `bench/**` o da avvio manuale); i dati grezzi finiscono anche nei rami `bench-data/<run>-<strumento>`.
