# Stato delle misure (aggiornato 2026-11-16, sera)

Regola: una cella vuota o "non misurato" significa che **non** è stata fatta la misura. Nessun numero stimato.
Ambiente delle misure: runner GitHub Actions `windows-latest` (Windows Server 2025, AMD EPYC, 2 vCPU condivisi, 1920×1080 a 96 DPI, un monitor). Non è una VM dedicata: vedi i limiti in `RAPPORTO.md` §1b.

| Prova | Stato | Dove / perché |
|---|---|---|
| Fedeltà px/ms, 30 rip., MMSS 1.2.3 e AutoHotkey 2.0.31 | **misurato** (2 esecuzioni) | `runner-github/43912272395/`, `runner-github/43918554473/` |
| Riferimento ideale (SendInput + QPC) | **misurato** (1 esecuzione) | `runner-github/43918554473/ideal/` |
| Fedeltà TinyTask 1.77 | **non misurato**: non riproduce la macro in questo ambiente, causa non accertata | `runner-github/43912272395/tinytask/` (870 eventi persi su 870) |
| Fedeltà Pulover, Jitbit, Mini Mouse Macro, OP Auto Clicker, Actiona | **non misurato** | non girati |
| p95 dell'errore di intervallo (soglia 16 ms) | **non valutabile** qui: il riferimento ideale fa 28,2 ms | serve hardware reale o VM con core dedicati |
| CPU/RAM a riposo (60 s) | **misurato** per MMSS, AutoHotkey, TinyTask | `risorse_riposo.csv` |
| CPU a riposo MMSS dopo l'ottimizzazione Bambola | **misurato dal sorgente**: 1,48 · 1,48 · 1,33 % (prima 4,22–4,61 %), pixel identici 97/97, 24 fps invariati. **Non** misurato sull'exe impacchettato | `runner-github/ottimizzazione-cpu-bambola.md` |
| CPU/RAM in esecuzione | **non misurato** | non ancora nel banco |
| Tempo di avvio | **misurato per MMSS** (run 43927100173, ramo `bench-data/43927100173-mmss`): 15 avvii, 14 a caldo: mediana 0,378 s, p95 0,402 s, primo avvio a freddo 0,452 s (soglia 2 s / 3 s). Dal CreateProcess alla finestra visibile e reattiva, su runner condiviso. **Non misurato** per AutoHotkey e TinyTask (finestra non rilevata) | `avvio.csv` |
| Peso | **misurato** (MMSS 19.049.731 byte; AHK 3.160.453; TinyTask 5.678.424) | `inventario.json` |
| DPI misto, multi-monitor, finestre elevate, giochi | **non misurato** | servono hardware reale, più monitor, un gioco |
| Macro di più ore | **non misurato** | il job CI ha un limite di 45 minuti |
| VirusTotal / SmartScreen | **non misurato** | il container non raggiunge virustotal.com (proxy); SmartScreen richiede un Windows con reputazione/Mark-of-the-Web reale |
| Test di usabilità | **non eseguito** | servono persone; protocollo pronto in `USABILITA.md` |
| Matrice funzioni | **parziale** | colonne dei rivali: solo fatti letti su fonti ufficiali, il resto "non verificato" |
| Test degli script di analisi | **eseguiti** (11 test, dati sintetici) | verificano statistiche e verdetti |
| Logger esterno su Windows | **collaudato** (0 px di errore sul riferimento ideale) | job `smoke` e riga `ideal` |

## Misure di altre sessioni (metodo diverso, **non conformi a questa procedura**)

Da `project-state` (1/11/2026, VM vm-windows-test senza GPU, % di un core pronto, versione 1.2.3): pannello pronto 9,3 · Copertina 13,2 · Micro in registrazione 7,1 · Micro in riproduzione 6,0. Peso ZIP v1.1.1: 12.114.231 byte (`docs/ESITO-COLLAUDO-v1.1.1.md`). Riferimento di partenza, non verdetto.
