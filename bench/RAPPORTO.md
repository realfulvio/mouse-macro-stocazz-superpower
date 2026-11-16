# Mouse Macro Stocazz Superpower contro i rivali: analisi comparativa (Windows)

Data: 2026-11-16 · Versione in prova: Windows v1.2.3 · Perimetro: solo Windows (Linux escluso da Luca).

## 1. Cosa è stato fatto davvero (leggi prima questo)

**Costruito e verificato**: il banco di prova completo (logger di input esterno, macro di riferimento identica, orchestratore, misure di risorse/avvio, inventario con hash, ricerca VirusTotal, analisi con mediana/p95/varianza, soglie congelate, protocollo di usabilità con punteggio SUS). Gli script di analisi hanno 11 test automatici (dati sintetici) che passano.

**Non misurato**: nessuna misura su Windows. Il container non ha Windows, il PC di lavoro non è una VM pulita (la prova muoverebbe il mouse reale) e l'accesso SSH al mini PC con le VM è stato negato dalle regole di sicurezza della sessione, che non ho aggirato. Quindi **fedeltà in px/ms, CPU/RAM dei rivali, avvio, DPI misto, multi-monitor, finestre elevate, giochi, macro di ore, VirusTotal, SmartScreen e usabilità sono tutti "non misurato"** (`data/STATO-MISURE.md`). Il logger non è ancora mai girato su Windows: va collaudato nella prima sessione in VM.

Tutto il resto di questo documento è quindi: fatti letti su fonti primarie, fatti dal nostro codice, e **ipotesi marcate come tali** da confermare con il banco.

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
| 1 | **Costo a riposo dell'animazione Bambola**: 9,3 % di un core a pannello pronto, 13,2 % in Copertina, 6–7 % da Micro | misure del 1/11 in VM senza GPU (metodo diverso, non conforme); soglia preregistrata 2 % / 5 % | probabile NON PASSA; i rivali minimali sono nell'ordine di ~0 % (**da misurare**, non assunto) |
| 2 | **Peso e avvio**: ZIP ~12 MB (v1.1.1) contro AHK 3 MB e TinyTask di decine di KB (TinyTask 1.77: peso da confermare) | repo, release AHK | passa la soglia 25 MB, perde il confronto relativo; struttura (Python embedded), non è un obiettivo |
| 3 | **Antivirus/SmartScreen**: exe non firmato; issue #1 SentinelOne; Actiona dichiara la firma del codice | repo | da misurare (VirusTotal, SmartScreen) |
| 4 | **Finestre elevate**: SendInput è soggetta a UIPI e il codice segnala solo il rifiuto di `SendInput`; se il bersaglio è elevato l'iniezione può non arrivare senza messaggio chiaro | doc. Microsoft + `checked_input` in `windows_backend.py` | **ipotesi dal codice**: prova S5 |
| 5 | **Errore di posizione di 1 px**: l'iniezione usa coordinate assolute normalizzate `round(x·65535/(w−1))` con VIRTUALDESK; la conversione di Windows a pixel può non tornare esattamente sul pixel | `CheckedMouse._position_set` | **ipotesi dal codice**: prova S1–S4, logger esterno |
| 6 | **Portabilità tra configurazioni schermo**: una macro con geometria diversa viene rifiutata ("Schermo o monitor diversi") | `macro/runner.py` | è una scelta di sicurezza; i rivali probabilmente non la fanno (da verificare) |
| 7 | **DPI misto / multi-monitor**: la resa in pixel fisici è dichiarata (Per-Monitor-V2) ma mai misurata con logger esterno | codice | prova S2–S4 |
| 8 | Impostazioni non si riscala a caldo col DPI; pannello troppo alto a 1024×768 al 125 % | memoria di progetto | difetti noti |

## 6. Cosa fare e in che ordine (senza regressioni)

Ogni intervento passa dal banco **prima e dopo** con la stessa procedura; si pubblica solo se nessuna soglia peggiora rispetto alla versione precedente (regola di Luca).

1. **Collaudare il banco in VM e misurare la baseline 1.2.3 e TinyTask/AHK** (1 giornata). Senza numeri tutto il resto è ipotesi. Prima di tutto il logger.
2. **Gap 1, costo a riposo**: se la baseline lo conferma, ridurre il lavoro dell'animazione quando non serve (ritmo ridotto dopo N secondi senza interazione o con finestra non in primo piano), tenendo i 24 fps quando l'utente guarda. Confronto A/B con `measure_resources.ps1` e verifica visiva dei fotogrammi distinti, come già fatto per la 1.2.3.
3. **Gap 5 e 4 (precisione e UIPI)**: se la prova S1/S5 conferma, verifica a posteriori della posizione con `GetCursorPos` dopo l'iniezione e correzione a 1 px; avviso esplicito prima di riprodurre su un bersaglio elevato. Sono modifiche piccole e localizzate; devono passare i 163+ test e le prove S1–S5.
4. **Gap 3, firma e antivirus**: firma Authenticode del launcher (costo in soldi e tempo, non codice), segnalazione dei falsi positivi ai produttori; ripetere VirusTotal/SmartScreen a ogni release.
5. **Gap 7 e 8**: scala DPI a caldo per Impostazioni e altezza del pannello; poi prova su PC reale con 2 monitor a scale diverse.
6. Funzioni dei rivali non nostre (Jitbit compila in EXE, Actiona ha ricerca immagine e scripting): **non seguirle** finché il target resta "registratore semplice e sicuro"; valutare solo se il test di usabilità lo chiede.

## 7. Per rifare tutto

`bench/README.md` → `PROCEDURA.md`. Dati grezzi in `bench/data/`, sommari generati da `analyze.py`.
