# Windows v0.17 — esito del collaudo

Collaudo del 4 ottobre 2026. Pacchetto: `MouseMacroStocazzSuperpower-Windows-v0.17.0-beta.zip`, **11.875.949 byte**.

SHA256: `3396ef92ff901a04bf281832a2e8f00a848b5c2778dda2c6a4a410a83b830477`.

**57 verifiche di accettazione superate** sullo stesso ZIP, aggregando le asserzioni riuscite delle run e contando una sola volta ogni combinazione verifica/velocità/DPI. Suite Windows: 108 test totali, **102 superati e 6 saltati** perché specifici di Linux. Controllo statico: CRC senza errori, 105 hash del manifest verificati, sorgenti e asset corrispondenti, launcher x64 GUI e byte originali del runtime Python preservati. I [risultati consultabili](qa/v017-results.json) contengono contatori, tempi e criterio di aggregazione.

Il ZIP è stato estratto e il suo EXE avviato in un desktop Windows 11 x64 interattivo, 1920×1200. Selenium ha preparato pagine locali e letto i contatori DOM; registrazione, riproduzione e comandi del pannello hanno usato input Windows reali. Il prodotto non include Selenium, Flet o un server web. Il pacchetto distribuito non è stato ricompilato dopo queste prove.

## Macro nei browser, scala 100%

| Browser | Normale, 20 giri | Rapida, 20 giri | Esito per velocità |
| --- | ---: | ---: | --- |
| Chrome 154.0.8037.98 | 100,94 s | 97,56 s | 20 A, 20 B, 20 doppi clic, 20 trascinamenti, 20 eventi rotella; zero persi |
| Firefox 157.0 | 102,74 s | 97,15 s | 20 A, 20 B, 20 doppi clic, 20 trascinamenti, 20 eventi rotella; zero persi |

Ogni prova ha verificato anche 40 eventi clic singoli appartenenti ai doppi clic e 20 coppie pressione/rilascio del trascinamento. Rapida 2× conserva le pause lunghe: non promette una durata totale dimezzata.

- Cinque schede distribuite fra due finestre: tre nella prima, due nella seconda. Un A/B per scheda, finestra secondaria intatta fino alla sua attivazione manuale, tutte le schede ancora aperte. Ctrl+Tab soltanto fra i giri.
- F9 da tastiera e Registra dal pannello; F10 e Riproduci dal pannello. Il pannello non sottrae il primo piano al browser con i normali clic.
- Salva/Carica con dialoghi nativi, eventi del pannello esclusi dalla macro; file non valido respinto conservando la macro precedente.
- F10 e Ferma interrompono una pausa di dieci secondi; l’emergenza interrompe un trascinamento tenendo premuto il mouse e lo rilascia. Latenze misurate nelle prove riuscite: **10,74–60,75 ms**. Chiusura durante pressione nativa: **59,73 ms**, mouse rilasciato e uscita 0.
- Perdita del primo piano e pannello sopra un bersaglio fermano la riproduzione. La prova del pannello sovrapposto ha inviato zero clic alla pagina.
- Pagina con ritardo simulato di 900 ms: il profilo standard perde intenzionalmente un’azione della sequenza molto ravvicinata; Pagine lente completa 20 coppie A/B senza perdite in entrambi i browser (53,53 s Chrome, 53,20 s Firefox). È una pausa fissa più prudente, non un rilevatore del caricamento.

## Interfaccia reale e DPI

Controlli veri, testo Outfit e SVG disegnati alla scala corrente, cavallini originali del handoff. Riproduci e Salva disabilitati senza una macro valida; contatori di eventi e durata aggiornati durante la registrazione; opzioni disabilitate durante le attività. Preset 20, Salva e Carica sono presenti nella sezione Opzioni.

Trascinamento dalla fascia superiore, espansione/riduzione conservando il preset, annullamento di Carica, Guida, navigazione Tab/Spazio con focus visibile, minimizzazione/ripristino e chiusura sono stati provati sullo ZIP. Per usare la tastiera sul pannello, attivarlo esplicitamente con Alt+Tab.

Alla scala Windows reale **150% (144 DPI)**, ciascun browser ha superato due giri per velocità con clic, doppi clic, trascinamenti e rotella, senza perdite, più il flusso cinque schede/due finestre e la protezione sul primo piano. Sono state esaminate le catture native al 100% e al 150%, nelle viste compatta ed estesa.

| Applicazione reale | Scala 100% | Scala 150% |
| --- | --- | --- |
| Compatta | [Schermata](screenshots/v017-compact-100.png) | [Schermata](screenshots/v017-compact-150.png) |
| Opzioni estese | [Schermata](screenshots/v017-expanded-100.png) | [Schermata](screenshots/v017-expanded-150.png) |
| Stati | [Registrazione](screenshots/v017-recording-100.png), [Riproduzione](screenshots/v017-playing-100.png), [Errore](screenshots/v017-error-100.png) | — |
| Guida nativa | [Schermata](screenshots/v017-guide-100.png) | — |

Queste immagini sono catture della finestra in Windows, ritagliate ai suoi bordi; non sono il mockup approvato.

## Avvio offline e build

Avvio riuscito in **1,15 s**, mentre la scheda virtuale era disconnessa; Windows riportava `Disconnected`. PATH senza Python, processo figlio nel `runtime/pythonw.exe` del pacchetto, uscita 0. Python era installato per il banco di prova: questo non è un collaudo di una macchina priva di qualunque installazione Python.

La [build Windows GitHub](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/37202617200) ha superato test, compilazione e controlli del manifest. Il suo artefatto resta un candidato distinto: la release allega il ZIP identificato dallo SHA256 sopra.

## Trasparenza delle run e limiti

Alcune run precedenti sono state interrotte. Sono stati corretti nel banco i percorsi relativi nei dialoghi e l’attesa del ripristino del bersaglio trascinabile. Interruzioni del desktop e un avvio ChromeDriver non riuscito hanno richiesto run successive; le verifiche riuscite sono riferite allo stesso ZIP e le protezioni dell’app sono rimaste attive. Un reset della connessione HTTP locale durante la chiusura del browser ha prodotto un messaggio del banco, senza invalidare le asserzioni riuscite al 150%. Log integrali e tentativi interrotti sono conservati come evidenze private; non vengono contati come run interamente riuscite.

L’app invia input alle coordinate registrate, senza confermare l’accettazione da parte di un sito e senza ritentare automaticamente. Richiede layout, zoom e DPI coerenti. Il pannello Windows è in italiano; non registra tasti, non chiude schede e non offre ripetizione infinita, casualità o confronto visuale automatico. Le registrazioni storiche senza metadati DPI restano limitate al 100%.

Nessun test su account Howrse reale e nessuna certificazione SentinelOne, Smart App Control o altre protezioni aziendali. Non collaudati ARM, elevazione/UAC, più monitor o DPI misti. Launcher non firmato. Linux conserva la UI storica.

Progetto e design: hcok.
