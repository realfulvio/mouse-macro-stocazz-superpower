# Protocollo prima delle misure: attese Windows

Baseline: ZIP pubblico Windows 1.2.5 SHA-256 `def843426d25dc0d12a5344c750a156e81f3b5567390df816337908c09174975`. Candidato: artifact del commit della PR, stessa versione per la prova, nessuna pubblicazione automatica. Soglie congelate invariate.

Modifica solo Windows: timer ad alta risoluzione di CPython (`time.sleep`, runtime distribuito 3.13), spin residuo massimo 0,3 ms anziché 2–3 ms. Scadenze, ordine, coordinate e protezioni temporali dei gesti invariati. Attesa lunga interrompibile con Event; sleep in tranche ≤10 ms per lo stop. Percorso Linux invariato.

1. Test contrattuali di scadenza/stop e suite esistente.
2. Stesso host, 30 coppie con ordine AB/BA alternato, 64 scadenze da 8 ms per lato. CPU del processo, ritardo per evento e 10 stop per replica. Misura senza backend, complementare al logger. Riportare mediana/p95/massimo, anticipo e singole repliche. Non considerare l’overhead di avvio del processo nella CPU. Differenze mediana/p95 oltre 0,1 ms costituiscono un segnale da diagnosticare, non da nascondere con ripetizioni selettive.
3. Stessa procedura di accettazione ZIP per baseline e candidato, 3 finestre CPU per carico, pixel, UIPI, exe/cmd/installazione e 30 ripetizioni con logger esterno; risorse e 15 avvii. Job su runner separati: dichiarare hardware e rumore. Nessuna soglia passa→non passa, zero eventi persi/extra, precisione delle coordinate preservata e CPU densa ridotta. P95 intervalli già non validabile su host condivisi: nessuna certificazione assoluta.
4. Salvare tutti i risultati, inclusi fallimenti. Nessun merge se emergono regressioni irrisolte. Nessuna modifica alle soglie o esclusione dei test.

Fonte del timer: https://docs.python.org/3.13/library/time.html#time.sleep (Windows: waitable timer da Python 3.11, timer ad alta risoluzione da Windows 8.1). La risoluzione del timer non garantisce la latenza dello scheduler; questa viene misurata.
