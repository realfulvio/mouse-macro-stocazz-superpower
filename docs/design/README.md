# Direzione grafica approvata — Windows v0.17

Progetto e design: hcok. La UI Windows è costruita con controlli Win32 reali e disegno GDI+ alla scala DPI corrente, con Outfit, palette prugna/rosa/viola/giallo e i quattro cavallini del handoff approvato. Nessuna immagine del mockup viene usata come interfaccia.

I PNG originali sono conservati senza modifiche in `assets/horses`. In fase di rendering viene selezionata soltanto la regione illustrata: i file forniti contengono margini trasparenti e scritte di catalogo. Le icone SVG sono disegnate come vettori. Outfit Regular/Bold sono istanze statiche del font variabile originale, con la stessa licenza OFL.

La finestra compatta misura 340×600 pixel logici; quella estesa 640×608. Le opzioni si dispongono su tre colonne. La riga aggiunta con Salva/Carica e il preset 20 completa le funzioni richieste. Riduci a icona, espandi/riduci, chiudi e trascina dalla fascia superiore sono comandi reali.

Registra/Riproduci diventano Ferma durante le rispettive attività. I contatori mostrano eventi e durata reali; durante la registrazione si aggiornano ogni 100 ms. Senza macro valida, Riproduci e Salva sono disabilitati. Durante un’attività, i controlli delle opzioni sono disabilitati. Ctrl+Alt+F11 resta disponibile anche con un dialogo aperto.

Per la sicurezza il pannello non prende il focus del browser al clic. Per navigarlo da tastiera attivarlo esplicitamente (Alt+Tab), quindi usare Tab/Shift+Tab e Spazio. I dialoghi file sono nativi Windows. La modalità rapida e il profilo Pagine lente conservano il comportamento del motore v0.16.

Gli screenshot della release sono catture dell’applicazione reale in Windows; non sono mockup né una certificazione di servizi o protezioni esterne.
