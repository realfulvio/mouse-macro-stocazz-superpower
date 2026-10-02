# Collaudo locale v0.15 beta — esito aggiornato

**20 prove native superate, 0 fallite dopo il ricontrollo.**
In aggiunta: 85 test automatici superati, 6 esclusi perche specifici di Linux. Howrse non e stato aperto o usato.

## Come sono state eseguite le prove

Il Python 3.13.15, le dipendenze e i moduli engine/WindowsPlayer/WindowsRecorder/GDI sono quelli della portable consegnata, senza mock. Un launcher firmato Python Software Foundation ha eseguito il banco di prova sul desktop interattivo. La finestra destinataria appartiene al banco di prova: conta messaggi mouse e tastiera realmente ricevuti, scarta azioni durante un intervallo occupato e mantiene identici i pixel del bersaglio.

La prima esecuzione dall ambiente dei comandi non poteva ottenere il primo piano e non ha inviato input. La prima prova sul desktop ha avuto due anomalie del banco (ridisegno iniziale e misurazione nella dispatch Python); queste sono state corrette nel banco, usando timestamp Windows, e ricontrollate. Sono conservati anche i risultati iniziali. Nessuna modifica al motore e stata necessaria in questo collaudo.

## Risultati fisici principali

| Prova | Ricevuti | Accettati | Tempo reale |
|---|---:|---:|---:|
| 150 ms pressione / 150 ms pausa | 10 pressioni + 10 rilasci | 5 | 3.37 s |
| 150 ms pressione / 300 ms pausa | 10 pressioni + 10 rilasci | 10 | 4.86 s |
| 150 ms pressione / 450 ms pausa | 10 pressioni + 10 rilasci | 10 | 6.39 s |
| 450 ms pressione / 450 ms pausa | 10 pressioni + 10 rilasci | 10 | 9.38 s |
| 100 click a 20x, 150/450 ms | 100 pressioni + 100 rilasci | 100 | 63.86 s |

A parita di 10 azioni accettate e pausa di 450 ms, tenere la pressione a 150 ms ha ridotto il tempo di circa 32% rispetto a una pressione di 450 ms.

Il caso 150/150 invia tutti gli input ma la destinazione occupata accetta solo meta delle azioni. Il confronto visivo corrisponde durante tutta la prova: conferma il limite di usare soltanto i pixel per dedurre che una pagina sia pronta. I 300 ms sono sufficienti in questo scenario controllato (pressione + pausa + costi di invio), non una raccomandazione universale per un sito reale.

## Copertura

- 10 click a 1x, 3x, 10x e 20x, senza pressioni o rilasci persi.
- Registrazione tramite hook Windows di 5 click fisici, con snapshot GDI; salvataggio e ricaricamento MMR identici; riproduzione fisica dei 5 click registrati.
- Pixel diversi: attesa fino al ripristino; timeout senza inviare click; stop che interrompe l attesa.
- Stop durante la pressione: rilascio fisico di sicurezza, pulsante non bloccato; stop nella pausa finale: nessuna azione extra e nessuna chiusura.
- Cambio della finestra in primo piano e sovrapposizione: fermata prima del secondo click.
- Quattro cicli: tre Ctrl+W realmente ricevuti dalla finestra locale, dopo la pausa finale; nessuna chiusura dopo l ultimo ciclo. La finestra simula le schede: questa prova non certifica un browser reale.
- Click destro, centrale e rotella realmente ricevuti.
- F9, F10 e Ctrl+Alt+F11 realmente registrati e ricevuti con il focus sulla finestra locale; rilevato anche il conflitto con l istanza di collaudo precedente, poi chiusa.
- Registro JSON per ogni riproduzione: input inviati, tempi, esito e conteggi. Non inventa conferme del sito.

## Limite del collaudo dell interfaccia

Avvio, versione, backend Windows, impostazioni e apertura dell interfaccia in Chrome sono stati verificati. Per questa ispezione un adattatore esterno ha sostituito solo l apertura della finestra con l esposizione dell URL locale; il codice main della portable e rimasto invariato. La finestra Edge della portable era stata avviata nella prova precedente.

Il controllo fisico della finestra browser e stato fermato dallo strumento perche non poteva stabilire l URL con sufficiente certezza. Di conseguenza, dialoghi Apri/Salva dall interfaccia, registrazione comandata dall interfaccia e passaggio fra schede browser reali non sono dichiarati completati. Il salvataggio/caricamento del formato, il registratore nativo e il comando Ctrl+W sono invece verificati dalle prove native sopra.

## Ripetere il banco locale

Estrarre la portable, chiudere le altre istanze e avviare il suo eseguibile passando native_acceptance.py come unico argomento. Il banco mostra una finestra propria; non aprire altri programmi durante la prova e attendere la sua chiusura. La cartella outputs accanto alla cartella del file riceve native-acceptance.json, native-traces e native-recorded.mmr. Se lo script e gia nella cartella outputs, i risultati vengono scritti nella stessa cartella.

I file native-first-run.json e native-acceptance-recheck.json documentano i tentativi; native-acceptance-final.json contiene l esito consolidato e tutti i dettagli. Prima della pubblicazione è stato aggiornato soltanto LEGGIMI - README.txt per conservare le note di compatibilità aggiunte a monte. Tutti gli altri file della portable, inclusi applicazione e runtime, sono byte-identici al pacchetto collaudato. Gli hash distribuiti sono in SHA256SUMS.txt.
