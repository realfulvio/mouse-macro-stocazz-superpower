<p align="center"><a href="README.md">English</a> · <b>Italiano</b></p>

# Mouse Macro Stocazz Superpower

Registra movimenti, clic, trascinamenti e rotella; ripeti la sequenza da una finestra Windows compatta ed espandibile, sempre in primo piano. Outfit, cavallini e palette prugna, rosa, viola e giallo riprendono la direzione grafica approvata.

**[Scarica v0.17.0 beta per Windows](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.17.0-beta)** · Progetto e design: **hcok**.

![Pannello Windows v0.17](docs/screenshots/v017-compact-100.png)

## Avvio

1. Scarica `MouseMacroStocazzSuperpower-Windows-v0.17.0-beta.zip` dalla release.
2. Estrai **tutta** la cartella ZIP.
3. Apri `Mouse Macro v0.17.0-beta.exe`.

Windows x64 con .NET Framework 4; collaudato su Windows 11. Python è incluso: nessuna installazione di Python e nessun download al primo avvio. Il launcher non è firmato. L’interfaccia Windows è in italiano. I controlli e i contatori sono reali; gli screenshot mostrano l’applicazione, senza simulare la UI con il mockup.

## Uso

1. Attiva Chrome o Firefox e sposta il pannello fuori dalla zona delle azioni.
2. Premi **F9**, esegui la sequenza su una scheda, premi di nuovo **F9**.
3. Imposta le ripetizioni e la velocità. Premi **F10** per riprodurre o fermare.
4. Per interrompere immediatamente usa **Ctrl+Alt+F11**.

**Scheda successiva** invia Ctrl+Tab fra i giri: le schede devono essere già aperte nella stessa finestra. Per un’altra finestra devi attivarla manualmente. Posizione del browser, zoom, risoluzione e scala dello schermo devono restare coerenti con la registrazione.

![Applicazione reale: opzioni estese in Windows al 100%](docs/screenshots/v017-expanded-100.png)

Apri **Opzioni** per Salva/Carica, il preset di 20 ripetizioni, velocità e **Pagine lente**. Guida ed Emergenza restano nel footer. Senza macro valida, Riproduci e Salva sono disabilitati. Rapida 2× accelera i movimenti e conserva le pause lunghe; non dimezza necessariamente la durata totale. Pagine lente aggiunge pause più prudenti, senza rilevare automaticamente il caricamento del sito.

![Applicazione reale durante la registrazione](docs/screenshots/v017-recording-100.png)

## Verifica e limiti

Il nuovo ZIP ha superato **57 verifiche di accettazione** sul suo hash specifico: Chrome e Firefox, 20 ripetizioni per velocità senza azioni perse sul bersaglio locale, cinque schede/due finestre, arresto e rilascio dei pulsanti, dialoghi nativi, scale 100% e 150%, avvio senza rete. Suite Windows: 102 test superati, 6 saltati.

Il programma invia input alle coordinate registrate: non conferma che un sito abbia accettato il clic e non riprova automaticamente. Non registra i tasti, non chiude schede e non offre ripetizione infinita nel nuovo pannello. Howrse reale, SentinelOne e Smart App Control non sono stati collaudati. Vedi il [rapporto completo](docs/ESITO-COLLAUDO-v0.17.md).

## Linux e sviluppo

Linux mantiene l’interfaccia Flet storica IT/EN; questa release aggiorna Windows. I pacchetti Linux sono nella [release v0.14 beta](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

- [Guida italiana](GUIDA-ITALIANA.md)
- [Build e collaudo v0.17](BUILD-v0.17.md)
- [Tutte le release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases)
- [Implementazione della grafica approvata](docs/design/README.md)
- [Licenza](LICENSE)
