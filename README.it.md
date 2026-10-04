<p align="center"><a href="README.md">English</a> · <b>Italiano</b></p>

# Mouse Macro Stocazz Superpower

Registra movimenti, clic, trascinamenti e rotella; ripeti la sequenza da un pannello Windows compatto, sempre in primo piano.

**[Scarica v0.16.0 beta per Windows](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.16.0-beta)** · Progetto e design: **hcok**. Implementazione v0.16: **by codex**.

![Pannello Windows v0.16](docs/screenshots/v016-main.png)

## Avvio

1. Scarica `MouseMacroStocazzSuperpower-Windows-v0.16.0-beta-by-codex.zip` dalla release.
2. Estrai **tutta** la cartella ZIP.
3. Apri `Mouse Macro v0.16.0-beta-by-codex.exe`.

Windows x64 con .NET Framework 4; collaudato su Windows 11. Python è incluso: nessuna installazione di Python e nessun download al primo avvio. Il launcher non è firmato. La nuova interfaccia Windows è in italiano.

## Uso

1. Attiva Chrome o Firefox e sposta il pannello fuori dalla zona delle azioni.
2. Premi **F9**, esegui la sequenza su una scheda, premi di nuovo **F9**.
3. Imposta le ripetizioni e la velocità. Premi **F10** per riprodurre o fermare.
4. Per interrompere immediatamente usa **Ctrl+Alt+F11**.

**Scheda successiva** invia Ctrl+Tab fra i giri: le schede devono essere già aperte nella stessa finestra. Per un’altra finestra devi attivarla manualmente. Posizione del browser, zoom, risoluzione e scala dello schermo devono restare coerenti con la registrazione.

![Menu: salvataggio, caricamento, pagine lente e ripetizioni](docs/screenshots/v016-menu.png)

Nel menu trovi Salva/Carica, il preset di 20 ripetizioni, **Pagine lente** e la guida. Rapida 2× accelera i movimenti e conserva le pause lunghe; non dimezza necessariamente la durata totale. Pagine lente aggiunge pause più prudenti, senza rilevare automaticamente il caricamento del sito.

![Guida integrata](docs/screenshots/v016-help.png)

## Verifica e limiti

Il ZIP pubblicato ha superato **41 verifiche di accettazione**: Chrome e Firefox, 20 ripetizioni per velocità senza azioni perse sul bersaglio locale, cinque schede/due finestre, arresto e rilascio dei pulsanti, dialoghi nativi, scale 100% e 150%, avvio senza rete. Suite Windows: 102 test superati, 6 saltati.

Il programma invia input alle coordinate registrate: non conferma che un sito abbia accettato il clic e non riprova automaticamente. Non registra i tasti, non chiude schede e non offre ripetizione infinita nel nuovo pannello. Howrse reale, SentinelOne e Smart App Control non sono stati collaudati. Vedi il [rapporto completo](docs/ESITO-COLLAUDO-v0.16.md).

## Linux e sviluppo

Linux mantiene l’interfaccia Flet storica IT/EN; questa release aggiorna Windows. I pacchetti Linux sono nella [release v0.14 beta](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

- [Guida italiana](GUIDA-ITALIANA.md)
- [Build e collaudo v0.16](BUILD-v0.16-by-codex.md)
- [Tutte le release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases)
- [Licenza](LICENSE)
