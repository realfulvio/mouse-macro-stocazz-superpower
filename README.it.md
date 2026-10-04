<p align="center"><a href="README.md">English</a> · <b>Italiano</b></p>

# Mouse Macro Stocazz Superpower

Registra movimenti, clic, trascinamenti e rotella; ripeti la sequenza da una finestra Windows compatta ed espandibile, sempre in primo piano. Outfit, cavallini e palette prugna, rosa, viola e giallo riprendono la direzione grafica approvata.

**[Scarica v0.18.1 beta per Windows](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.18.1-beta)** · Progetto e design: **hcok**.

**v0.18.1-beta** rimuove il blocco Chrome/Firefox: registra e riproduce anche fra programmi e desktop. Conserva le modifiche v0.18: disattiva il cambio scheda all’avvio e accelera anche le pause operative in Rapida 2×. Layout invariato rispetto alle schermate v0.17 qui sotto. [Modifiche, misure e stato del collaudo](docs/ESITO-COLLAUDO-v0.18.1.md) · [Build v0.18.1](BUILD-v0.18.1.md).

![Pannello Windows v0.17](docs/screenshots/v017-compact-100.png)

## Avvio

1. Scarica `MouseMacroStocazzSuperpower-Windows-v0.18.1-beta.zip` dalla release.
2. Estrai **tutta** la cartella ZIP.
3. Apri `Mouse Macro v0.18.1-beta.exe`.

Windows x64 con .NET Framework 4; collaudato su Windows 11. Python è incluso: nessuna installazione di Python e nessun download al primo avvio. Il launcher non è firmato. L’interfaccia Windows è in italiano. I controlli e i contatori sono reali; gli screenshot mostrano l’applicazione, senza simulare la UI con il mockup.

## Uso

1. Prepara le finestre da usare e sposta il pannello fuori dalla zona delle azioni.
2. Premi **F9**, esegui la sequenza del mouse, premi di nuovo **F9**.
3. Imposta le ripetizioni e la velocità. Premi **F10** per riprodurre o fermare.
4. Per interrompere immediatamente usa **Ctrl+Alt+F11**.

**Scheda successiva** parte disattivata; quando attivata invia Ctrl+Tab soltanto fra i giri, mai dopo l’ultimo: le schede devono essere già aperte nella stessa finestra. Il replay può cambiare finestre usando i click registrati. Mantieni posizione delle finestre, risoluzione e scala dello schermo coerenti con la registrazione.

![Applicazione reale: opzioni estese in Windows al 100%](docs/screenshots/v017-expanded-100.png)

Apri **Opzioni** per Salva/Carica, il preset di 20 ripetizioni, velocità e **Pagine lente**. Guida ed Emergenza restano nel footer. Senza macro valida, Riproduci e Salva sono disabilitati. Rapida 2× accelera movimenti e pause operative fino a 2 s; le attese oltre 2 s restano protette a 1×. Il minimo fra azioni passa da 650 a 325 ms; pressioni e doppi click restano protetti. La durata totale non viene necessariamente dimezzata. Pagine lente aggiunge pause più prudenti, senza rilevare automaticamente il caricamento del sito.

![Applicazione reale durante la registrazione](docs/screenshots/v017-recording-100.png)

## Verifica e limiti

Il ZIP v0.18.1 ha superato **18 verifiche interattive** su Windows 11 LTSC: registrazione e replay fra due finestre native e desktop, più 14 regressioni browser (click/doppio click, drag, wheel, 20 giri, cambio scheda OFF/ON, F10 ed emergenza). Zero click persi. La sequenza fra finestre scende da **6,841 s a 1× a 3,855 s a 2×**. Suite Windows: **112 superati, 6 saltati**; Linux: **67 superati, 51 saltati**. [Esito e limiti](docs/ESITO-COLLAUDO-v0.18.1.md).

Il programma invia input alle coordinate registrate: non conferma che un sito abbia accettato il clic e non riprova automaticamente. Non registra i tasti, non chiude schede e non offre ripetizione infinita nel nuovo pannello. Howrse reale, SentinelOne e Smart App Control non sono stati collaudati. Vedi il [rapporto completo](docs/ESITO-COLLAUDO-v0.18.1.md).

## Linux e sviluppo

Linux mantiene l’interfaccia Flet storica IT/EN; questa release aggiorna Windows. I pacchetti Linux sono nella [release v0.14 beta](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

- [Guida italiana](GUIDA-ITALIANA.md)
- [Build e collaudo v0.18](BUILD-v0.18.1.md)
- [Tutte le release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases)
- [Implementazione della grafica approvata](docs/design/README.md)
- [Licenza](LICENSE)
