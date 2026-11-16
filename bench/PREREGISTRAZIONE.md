# Preregistrazione: soglie passa / non passa

**Congelata il 2026-11-16, prima di qualsiasi misura.** I valori numerici sono in `thresholds.json` (letto da `analyze.py`).
Se una soglia va cambiata dopo aver visto i dati, si crea un nuovo file con data e motivo e si riportano **entrambi** i verdetti.

## Come sono state scelte (senza guardare i nostri risultati)

Le soglie vengono dall'uso, non dalle prestazioni del nostro programma:

- **Posizione**: un bersaglio cliccabile piccolo (casella, checkbox) misura 12–16 px; un errore sistematico oltre 2 px al 95° percentile
  fa mancare i controlli piccoli. Mediana ≤ 1 px, p95 ≤ 2 px.
- **Tempo**: un fotogramma a 60 Hz dura 16,7 ms; sotto quella soglia l'effetto non si vede su pagina o applicazione.
  Errore di intervallo (valore assoluto, solo intervalli ≥ 100 ms): mediana ≤ 5 ms, p95 ≤ 16 ms. Deriva massima dall'inizio di una macro da 16 s: p95 ≤ 50 ms.
- **Eventi**: zero mancanti e zero extra in ogni ripetizione (una macro che perde un clic è sbagliata, non "meno precisa").
- **Risorse**: uno strumento che resta aperto tutto il giorno deve costare poco. A riposo ≤ 2 % di un core, in esecuzione ≤ 5 %;
  Private Bytes ≤ 150 MB a riposo e ≤ 200 MB in esecuzione. (TinyTask e AHK sono nell'ordine dei pochi MB: la soglia è larga apposta.)
- **Avvio**: finestra visibile e reattiva ≤ 2 s (mediana, avvii caldi), p95 ≤ 3 s. L'avvio freddo si riporta a parte, senza soglia.
- **Peso del pacchetto**: ≤ 25 MB (il download che un utente accetta senza pensarci).
- **Lunga durata**: ≥ 4 h di loop continuo senza arresti anomali; crescita di Private Bytes ≤ 1 MB/h (regressione lineare sui campioni a 1 minuto).
- **Sicurezza**: 0 rilevamenti su VirusTotal e nessun blocco SmartScreen al primo avvio di un file con Mark-of-the-Web. File mai visti da VirusTotal = "sconosciuto", non "pulito".
- **Usabilità**: ≥ 5 persone che non conoscono il programma, compito completato da ≥ 80 %, tempo mediano ≤ 120 s, SUS mediano ≥ 68 (media di settore).
  Con n così piccolo i risultati sono **indicativi**, non statistici: si riportano i dati grezzi.

## Regole di misura

1. VM Windows 11 pulita da snapshot, ripristinato **prima di ogni strumento**; un solo strumento installato per volta.
2. Stessa macro di riferimento (`macros/reference.spec.json`: 12 clic su griglia, 1 trascinamento da 1 s, 3 scatti di rotella; 16,3 s; pause ≥ 0,9 s e pressioni da 0,15 s, quindi sopra i minimi di protezione del nostro motore: i suoi limiti di sicurezza non alterano la prova).
3. **30 ripetizioni** per strumento e scenario (minimo; sotto 30 il verdetto è "NON PASSA" per costruzione). Si riportano n, mediana, p95, varianza e deviazione standard, minimo e massimo; nessuna ripetizione si scarta, salvo errore del banco annotato a mano.
4. Il logger è un processo separato (`logger/inputlogger.py`, WH_MOUSE_LL) con timestamp QPC; non usa codice dei progetti in prova.
5. Gli strumenti che non registrano (OP Auto Clicker, script AHK scritto a mano) si valutano solo sul sottoinsieme applicabile; "non applicabile" non è "passa".
6. Esito di una funzione verificata a mano: **sì / no / parziale**, con data, versione provata e come l'hai provata. Niente giudizi presi da recensioni.
7. Un valore non misurato resta vuoto. Nei rapporti compare come "non misurato", mai come stima.

## Limiti dichiarati in anticipo

- Una VM non ha GPU reale né monitor reali: DPI misto e multi-monitor si simulano (`PROCEDURA.md`) e si ripetono su hardware reale prima di dire "passa".
- Giochi: l'input iniettato con SendInput è scartato da molti giochi con anti-cheat o che leggono Raw Input/DirectInput; la prova con un gioco vero è manuale e va fatta solo su titoli senza anti-cheat e senza account da proteggere.
- Il confronto è su Windows. Linux è fuori perimetro per richiesta di realhcok (2026-11-16).
