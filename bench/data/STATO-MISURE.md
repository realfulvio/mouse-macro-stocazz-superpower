# Stato delle misure (aggiornato 2026-11-16, sera)

Regola: una cella vuota o "non misurato" significa che **non** è stata fatta la misura. Nessun numero stimato.
Ambiente delle misure: runner GitHub Actions `windows-latest` (Windows Server 2025, AMD EPYC o Intel secondo inventario, 2 vCPU condivisi, 1920×1080 a 96 DPI, un monitor). Non è una VM dedicata: vedi i limiti in `RAPPORTO.md` §1b.

| Prova | Stato | Dove / perché |
|---|---|---|
| Fedeltà px/ms, 30 rip., MMSS 1.2.3 e AutoHotkey 2.0.31 | **misurato** (2 esecuzioni) | `runner-github/43912272395/`, `runner-github/43918554473/` |
| Riferimento ideale (SendInput + QPC) | **misurato** (1 esecuzione) | `runner-github/43918554473/ideal/` |
| Fedeltà TinyTask 1.77 | **non misurato**: non riproduce la macro in questo ambiente, causa non accertata | `runner-github/43912272395/tinytask/` (870 eventi persi su 870) |
| Fedeltà Pulover, Jitbit, Mini Mouse Macro, OP Auto Clicker, Actiona | **non misurato** | misurare risorse/avvio non equivale a riprodurre la macro di riferimento |
| p95 dell'errore di intervallo (soglia 16 ms) | **non valutabile** qui: il riferimento ideale fa 28,2 ms | serve hardware reale o VM con core dedicati |
| CPU/RAM a riposo (60 s) | **misurato** per MMSS, AutoHotkey, TinyTask e cinque nuovi rivali | `risorse_riposo.csv`, `runner-github/rivali-risorse.md` |
| CPU a riposo MMSS dopo l'ottimizzazione Bambola | **misurato dal sorgente**: 1,48 · 1,48 · 1,33 % (prima 4,22–4,61 %), pixel identici 97/97, 24 fps invariati. Nuova tornata a codice app invariato: **2,11 · 2,73 · 2,50%, non passa ≤2**; soglia non stabilmente rispettata. ZIP 1.2.5 ora misurato: media 3×20 s 1,9567%, riposo 60 s 1,8094%; singole finestre sopra soglia | `runner-github/ottimizzazione-cpu-bambola.md` |
| CPU in registrazione/riproduzione | **misurato dal sorgente**: seconda tornata registrazione 9,06 · 7,71 · 7,40% (non passa ≤5); riproduzione densa 14,37 · 14,58 · 14,37% (non passa), rada 3,12 · 3,33 · 3,02% (passa). Prima tornata registrazione sotto soglia: risultato non stabile | `runner-github/cpu-attiva-uipi.md` |
| CPU attiva del pacchetto | **misurato** usando runtime e file estratti dallo ZIP: medie 1.2.5 registrazione 4,93%, densa 13,1267% (non passa), rada 2,8467% | `runner-github/43951916704/`, stesso protocollo sulla v1.2.4; nessuna soglia passa→non passa |
| RAM attiva | **non misurato** | il profilo attivo misura CPU |
| Tempo di avvio | **misurato per MMSS** (run 43927100173, ramo `bench-data/43927100173-mmss`): 15 avvii, 14 a caldo: mediana 0,378 s, p95 0,402 s, primo avvio a freddo 0,452 s (soglia 2 s / 3 s). Dal CreateProcess alla finestra visibile e reattiva, su runner condiviso. **Non misurato** per AutoHotkey e TinyTask (finestra non rilevata) | `avvio.csv` |
| Peso | **misurato** (MMSS 19.049.731 byte; AHK 3.160.453; TinyTask 5.678.424) | `inventario.json` |
| Finestre elevate (UIPI) | **misurato prima/dopo dal sorgente**: prima falso successo medio→alto; dopo avviso, zero giri e macro non partita. Controllo alto→alto 13/13/3 | `runner-github/avviso-uipi.md`, run `43944349396` |
| DPI misto, multi-monitor, giochi | **non misurato** | servono hardware reale, più monitor, un gioco |
| Macro di più ore | **non misurato** | il job CI ha un limite di 45 minuti |
| VirusTotal / SmartScreen | **non misurato** | nessuna `VT_API_KEY` disponibile nella sessione corrente; nessun esito VirusTotal acquisito. SmartScreen richiede un Windows con reputazione/Mark-of-the-Web reale |
| Test di usabilità | **non eseguito** | servono persone; protocollo pronto in `USABILITA.md` |
| Matrice funzioni | **parziale** | colonne dei rivali: solo fatti letti su fonti ufficiali, il resto "non verificato" |
| Test degli script di analisi | **eseguiti** (13 test, dati sintetici) | verificano statistiche e verdetti |
| Logger esterno su Windows | **collaudato** (0 px di errore sul riferimento ideale) | job `smoke` e riga `ideal` |

Nuove prove:

- ZIP 1.2.5 contro 1.2.4: `runner-github/43951916704/`, rapporto `../../docs/ESITO-COLLAUDO-v1.2.5.md`. 30 ripetizioni per lato, posizione 0 px, zero eventi persi/extra; mediana intervalli 4,2370→4,0180 ms. Installer, exe/cmd, pixel 97/97 e UIPI verificati. Avvio caldo candidato 0,361/0,37270 s (mediana/p95); 48,15 MiB privati a riposo; ZIP 19.053.039 byte. Nessuna soglia passa→non passa, CPU densa ancora sopra soglia e p95 intervalli non validabile.

- Fedeltà prima/dopo il preflight dal sorgente: 30 ripetizioni per lato, zero eventi persi/extra e posizione 0 px. Mediana intervalli 4,3065→4,2390 ms; nessuna soglia passa→non passa. P95 non validabile sul runner condiviso. `runner-github/43944349328/`.
- Risorse e avvio di Pulover, Jitbit, OP Auto Clicker, Actiona e Mini Mouse Macro: `runner-github/rivali-risorse.md`; Actiona non passa peso, Jitbit ha un avvio scaduto in una tornata precedente. Condizioni e dati grezzi separati dalla fedeltà.

## Misure di altre sessioni (metodo diverso, **non conformi a questa procedura**)

Da `project-state` (1/11/2026, VM VM-TEST senza GPU, % di un core pronto, versione 1.2.3): pannello pronto 9,3 · Copertina 13,2 · Micro in registrazione 7,1 · Micro in riproduzione 6,0. Peso ZIP v1.1.1: 12.114.231 byte (`docs/ESITO-COLLAUDO-v1.1.1.md`). Riferimento di partenza, non verdetto.

## Ottimizzazione delle attese Windows

PR #48: confronto degli esatti ZIP e 30 ripetizioni per lato nel run 43960726750; precisione di posizione 0 px, eventi persi/extra zero, mediana intervalli 4,3175→0,6935 ms. P95 28,7270→26,9566 ms ancora non validabile. Sullo stesso host (43965391957), CPU densa 11,7367→5,1733%, rada 2,57→1,8767%. Finestre brevi di registrazione sopra soglia nel candidato; conservate. Diagnosi isolata 3×60 s per lato (43967066526): registrazione 4,47→4,4933%, tutte le finestre sotto il 5%. [Report e dati](runner-github/ottimizzazione-attese-risultati.md). Nessuna dichiarazione di stabilità universale o di tutte le soglie passate; release pubblica invariata.
