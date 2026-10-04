# Candidato v0.18.0-beta — modifiche e verifiche

Data: 4 ottobre 2026. Base esatta: `main` **ceee60d2399cd06af00fd029a042dde58b9b32e0**. Il tag v0.17.0-beta è `6d8c6464908d9b3ae722cce9f367634b775b6579`; i successivi cambiamenti su main erano documentali. Non sono state incorporate le vecchie directory di lavoro delle iterazioni precedenti.

**Stato: codice, build candidato e collaudo interattivo Windows completati. Release Windows v0.18.0-beta.**

## Causa e modifica

Il pannello v0.17 impostava `max_pause_speedup=1`, soglia delle pause lunghe 350 ms e pausa minima fra azioni 650 ms, a entrambe le velocità. Il motore protegge anche le attese tra azioni intercalate da movimenti, la durata minima della pressione e l'ultima azione del giro. Su una sequenza di click con pause ordinarie, impostare `speed=2` lasciava pertanto quasi tutte le attese a 1×.

Sono cambiati solo i parametri del pannello:

| Opzione | Normale | Rapida 2× | Pagine lente, entrambe le velocità |
|---|---:|---:|---:|
| Soglia pausa lunga | 2 s | 2 s | 350 ms, invariata |
| Accelerazione massima oltre soglia | 1× | 1× | 1×, invariata |
| Minimo dopo rilascio/azione wheel | 650 ms | 325 ms | 1.200 ms, invariato |
| Pressione minima | 120 ms | 120 ms | 120 ms, invariata |
| Minimo tra click di un doppio click | 80 ms | 80 ms | 80 ms, invariato |

Il limite del doppio click continua a provenire da `GetDoubleClickTime()` di Windows. `protect_wheel_actions=True` resta attivo. Motore, backend, stop, layout, posizione dei controlli, preset e logica delle ripetizioni non sono stati riscritti. `Panel.next_tab` parte **False**, resta attivabile dalle opzioni. Il default della API `Session.toggle_play` resta compatibile; il pannello passa sempre esplicitamente il proprio toggle.

## Confronto deterministico prima/dopo

Tempi end-to-end del motore con backend senza latenza, incluso il guard finale di `play()`. Clock virtuale; non sono misure di input su un browser reale. I test controllano anche il piano di `_compute_scaled_times()`, tutti gli eventi emessi e il completamento del giro.

| Macro | Prima 1× | Prima 2× | Dopo 1× | Dopo 2× |
|---|---:|---:|---:|---:|
| Movimenti ogni 100 ms, durata 1 s | 1,000 s | 0,500 s | 1,000 s | 0,500 s |
| Sei click, pause 0,4 / 0,7 / 1 / 1,5 / 0,6 s | 5,870 s | 5,870 s | 5,870 s | **3,295 s** |
| Doppio click seguito da click ravvicinato | 1,800 s | 1,740 s | 1,800 s | **1,090 s** |
| Quattro click, pause 0,7 / 6 / 0,7 s | 8,530 s | 8,530 s | 8,530 s | **7,505 s** |

La macro realistica migliora del **43,9% rispetto a Normale**. La pausa di 6 s resta interamente protetta, anche se contiene movimenti ogni 100 ms. Normale e Pagine lente mantengono le durate precedenti nei casi verificati. Il banco è ripetibile con `python qa/playback_timing.py`.

## Test eseguiti

- CachyOS `dev`, mirati: **59 test, OK, 18 skip Windows**.
- CachyOS `dev`, suite completa una volta: **116 test, OK, 50 skip Windows**.
- Windows `win-test`, mirati: **59 test, OK, nessuno skip**.
- Windows `win-test`, suite completa una volta: **116 test, OK, 6 skip Linux**.
- Nuovi test: default OFF, durate prima/dopo, `duration_fast < duration_normal`, miglioramento sostanziale sui click realistici, pressioni/doppi click, wheel e relativi margini, pausa lunga con movimenti, stop con rilascio del mouse, ripetizioni fino a 20. Test Session: OFF non chiama `next_tab`; ON effettua due cambi per tre giri, mai dopo l'ultimo.
- I test nativi preesistenti verificano anche registrazione delle hotkey, invio delle combinazioni, cleanup, pulsanti e wheel. Questi sono test automatici con backend controllati, non prove di hotkey su desktop reale.
- `git diff --check`: OK. Nessuna modifica a `macro/engine.py`, `macro/windows_backend.py` o `windows_visual.py`.

## Build e verifica su win-test

Build **nativa Windows** con Python 3.13.16, dipendenze fissate e `csc.exe` .NET Framework, stessa procedura di v0.17.

`MouseMacroStocazzSuperpower-Windows-v0.18.0-beta.zip`, **11.876.167 byte**.

SHA256: `e7d8781ae91bd3e720803779d6fbda6a5de12049b5b0a9253446c940a0eb3a38`.

`qa/check_package.py`: CRC ZIP corretto, **105 hash** verificati, sorgenti e asset corrispondenti, runtime originale preservato, launcher x64 GUI. Hash ricontrollato dopo il trasferimento a `dev`.

Avvio dei sorgenti e dello ZIP estratto nella sessione SSH non interattiva: entrambi creano il pannello v0.18. Il testo del toggle è inizialmente **disattivato**; il callback Win32 lo attiva; Preset 20 imposta **20**. Il pacchetto parte con Python installato escluso dal PATH.

**Questo avvio non è un'accettazione riuscita sul desktop:** entrambi i pannelli riportano `ERRORE`, messaggio «Tasti occupati: F9, F10, Ctrl+Alt+F11. Chiudi l’altra app.». La stessa prova con `windows_main.py` e `macro/session.py` esatti del tag v0.17 produce lo stesso errore. Windows non ha una sessione utente aperta (`quser`: nessun utente); non è stato effettuato alcun provisioning o reset della VM.

## Collaudo interattivo completato sul PC locale

Dopo il primo tentativo via SSH, l'utente ha autorizzato esplicitamente una VM Windows temporanea sul notebook e il completamento dei test lì. È stata creata **mouse-v018-test-local**, QEMU/KVM in sessione utente: 4 vCPU, 6 GiB RAM, Windows 11 Enterprise LTSC Evaluation 2024 dalla ISO ufficiale Microsoft, Python 3.13.16 e Chrome. Desktop **1280×800, 96 DPI**, account di test nuovo. Nessun segreto del minipc è stato copiato. Autostart della VM disabilitato; collegamenti di controllo solo su loopback. La VM è stata spenta al termine; file e definizione restano per eventuali verifiche.

Il controllo automatico ha rifiutato il trasferimento dell'ISO esistente dal minipc: è stata usata invece la ISO pubblica di valutazione Microsoft. Il tentativo del fixture di impostare 1920×1200 non è riuscito con l'adattatore video di base: il banco ha lavorato alla risoluzione disponibile, con tutti i bersagli fuori dal pannello. Questo errore di preparazione è conservato separatamente.

**Pacchetto testato: lo ZIP nativo Windows sopra indicato, SHA256 identico.** Avvio con Python installato escluso dal PATH; nessun errore di hotkey sul desktop interattivo. `qa/rapid_windows.py`: **14 controlli passati, exit code 0**, registrazione e input tramite API native, lettura dei contatori DOM tramite Selenium.

| Macro sul browser reale | Normale 1× | Rapida 2× | Contatori |
|---|---:|---:|---|
| Registrata: click A/B, doppio click, drag, wheel | 5,232 s | **2,914 s** | A=1, B=1, doppio=1 (2 singoli), drag=1, wheel=1; zero persi |
| Caricata: sei click, pause 0,4–1,5 s | 5,986 s | **3,409 s** | A=3, B=3, ricevuti=6; zero persi |
| Caricata: quattro click, pausa lunga 6 s | 8,562 s | **7,597 s** | A=2, B=2, ricevuti=4; zero persi |

Tempi effettivi del motore letti dalle trace, inclusa la protezione finale. Tempi esterni conservati anch'essi. Miglioramento effettivo della macro realistica: **43,0%**. Tutte le trace dei replay completati mantengono pressioni effettive di almeno **120 ms**.

Ulteriori controlli nativi:

- **Default OFF**, toggle ON manuale e **Preset 20** verificati sul pannello reale.
- **20 giri**: 20 click ricevuti, zero persi, completamento regolare (9,125 s).
- **Due giri OFF**: zero input Tab, 12 click sulla prima scheda, zero sulla seconda.
- **Due giri ON**: un solo input Tab tra i giri, 6 click per scheda; prima finestra sul titolo della seconda scheda al termine, nessun cambio dopo l'ultimo.
- **F10 durante pausa lunga**: arresto in **10,652 ms**, nessun secondo click e mouse rilasciato.
- **Ctrl+Alt+F11 durante drag premuto**: arresto in **11,029 ms**, rilascio di sicurezza osservato nella pagina.
- Prova aggiuntiva **Pagine lente**, sito con ritardo di 900 ms: due giri a 1× e due a 2×, quattro click ricevuti in ciascun replay, zero persi. Conservata la politica prudente precedente.

Il banco principale ha registrato in stderr una chiusura/reset della connessione HTTP del fixture al termine del browser; esito complessivo e tutti gli assert sono passati. Lo stderr originale è conservato, insieme ai contatori, alle trace e alle schermate. Non è stato ripetuto il collaudo grafico completo di v0.17.

## Limiti rimasti

Le attese sono temporali: non confermano che una pagina sia pronta. Per pagine che richiedono margini maggiori usare Pagine lente e registrare attese sufficienti. La modifica non garantisce durata/2 quando prevalgono pressioni minime o caricamenti lunghi. Il collaudo interattivo aggiunto è su Chrome nella VM locale; su `win-test` sono passate le suite automatiche, mentre il suo desktop resta senza sessione aperta. Il nuovo collaudo non estende le precedenti dichiarazioni su Howrse, Firefox, DPI, SentinelOne o SAC.

Evidenze locali (ignorate da Git): `evidence/v018/` per Linux e confronto numerico, `evidence/windows/` per test/build/pacchetto e tentativo SSH; **`evidence/local-windows/`** per il collaudo interattivo completo, trace, schermate e prova Pagine lente. Copia delle evidenze conservata anche nel repository su `dev`.

## File modificati

- Comportamento: `windows_main.py`; `macro/session.py` cambia soltanto la versione.
- Test e misura: `test_windows_timing.py`, `test_session.py`, `qa/playback_timing.py`, `qa/rapid_windows.py`.
- Build/versione: `build_native_windows.py`, `launcher.cs`, `qa/check_package.py`, `.github/workflows/release.yml`.
- Documentazione: `GUIDA-ITALIANA.md`, `README.md`, `README.it.md`, `BUILD-v0.18.md`, questo rapporto.
