# Stato delle misure (2026-11-16)

Regola: una cella vuota o "non misurato" significa che **non** è stata fatta la misura. Nessun numero stimato.

| Prova | Stato | Perché |
|---|---|---|
| Fedeltà px/ms (30 rip. per strumento e scenario) | **non misurato** | serve una VM Windows con sessione grafica. Il container di analisi non ha Windows; il PC di lavoro non è una VM pulita e la prova muove il mouse reale dell'utente; l'accesso SSH al PC di collaudo con le VM è stato negato dalle regole di sicurezza della sessione |
| CPU/RAM a riposo e in esecuzione dei rivali | **non misurato** | idem |
| Tempo di avvio | **non misurato** | idem |
| DPI misto, multi-monitor, finestre elevate, giochi | **non misurato** | idem (più hardware/monitor reali) |
| Macro di più ore | **non misurato** | idem |
| VirusTotal / SmartScreen | **non misurato** | il container non raggiunge virustotal.com (proxy) e SmartScreen richiede Windows |
| Test di usabilità | **non eseguito** | servono persone; protocollo pronto |
| Matrice funzioni | **parziale** | colonne dei rivali: solo fatti letti su fonti ufficiali, il resto "non verificato" |
| Test degli script di analisi | **eseguiti** (11 test, dati sintetici su Linux) | verificano le statistiche e i verdetti, non il logger |
| Sintassi del logger e degli script PowerShell/Python | Python compilato; **logger non ancora eseguito su Windows** | |

## Numeri che esistono già (misure di altre sessioni, metodo diverso, **non conformi a questa procedura**)

Da `project-state` (1/11/2026, VM VM-TEST senza GPU, % di un core pronto, versione 1.2.3): pannello pronto 9,3 · Copertina 13,2 · Micro in registrazione 7,1 · Micro in riproduzione 6,0.
Peso ZIP v1.1.1: 12.114.231 byte (`docs/ESITO-COLLAUDO-v1.1.1.md`). Servono come riferimento di partenza, non come verdetto.
