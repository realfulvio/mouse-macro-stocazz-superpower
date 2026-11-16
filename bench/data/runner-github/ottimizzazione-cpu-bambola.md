# Costo a riposo del pannello (skin Bambola): prima e dopo

Ambiente: runner GitHub `windows-latest` (Server 2025, 2 vCPU condivisi, 1920x1080, 96 DPI). Pannello avviato **dal sorgente** (`bench/ci/profile_idle.py`), non dall'exe impacchettato. CPU = tempo di processo del processo Python / finestra, in % di un core, senza profiler. Finestra 20 s dopo 10 s di riscaldamento, tre ripetizioni.

| | Prima (run 43923753698, commit c0f1505) | Dopo (run 43925782393, commit 2507bce) |
|---|---|---|
| CPU a riposo, 3 ripetizioni | 4,22 · 4,61 · 4,61 % | 1,48 · 1,48 · 1,33 % |
| Soglia (`thresholds.json`) | 2 % | 2 % |
| Messaggi WM_PAINT in 20 s | 480 (24/s) | 480 (24/s) |
| Tele GDI+ per la mascotte | 480 da 505 ms | 0 (percorso rapido a 3 copie) |
| draw_control | 366 chiamate da 231 ms | non compare piu' tra le voci misurate |
| render() | 183 da 300 ms | 182 da ~9-10 ms |
| WM_PAINT totale | n.d. | 480 da ~192-197 ms |

Verifica di equivalenza (`--mode verify`): 97 fotogrammi, 97 confrontati, 0 differenze, 97 passati dal percorso rapido; i pixel del fotogramma rapido sono identici a quelli del disegno completo.

Limiti: misura dal sorgente su runner condiviso (non dall'exe del pacchetto, non su PC reale, non in registrazione/riproduzione). La fluidita' e' dedotta dal numero di WM_PAINT (480 in 20 s = 24/s, identico a prima) e dalla verifica pixel per pixel, non da una cattura video. Il numero assoluto dipende dal runner; il confronto prima/dopo usa lo stesso ambiente e lo stesso metodo.
