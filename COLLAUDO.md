# Verifica v0.14 beta — 30/09/2026

Problema: su Windows 11 con **Smart App Control attivo** la v0.13 si fermava subito con
`OSError: [WinError 4551] Un criterio di controllo dell'applicazione ha bloccato il file`.
Il registro *CodeIntegrity* mostrava il blocco di `flet.exe`, il client desktop di Flet
estratto in `%USERPROFILE%\.flet\client`, perché non è firmato.

Correzione: su Windows l'interfaccia viene mostrata in una finestra di Microsoft Edge in
modalità app (`app_launcher.py`), `flet.exe` non viene più incluso, Apri/Salva usano le
finestre native di Windows (`macro/win_dialogs.py`) e i font sono inclusi negli asset.

**72 test eseguiti su Windows, 66 superati e 6 saltati** (quelli specifici di Linux),
Python 3.13 e Flet 1.0.3. Collaudo dell'eseguibile compilato, su Windows 11 con Smart
App Control **in modalità applicazione** e con l'exe marcato come scaricato da Internet
(Zone.Identifier 3):

| Prova | Risultato |
| --- | --- |
| Avvio IT ed EN | Finestra dell'app aperta, nessun evento di blocco nel registro CodeIntegrity |
| `--self-test` IT ed EN | Tutti i controlli superati |
| Registrazione con F9 da tastiera | 20 eventi e 1 click registrati; F9 funziona anche con il focus altrove |
| Riproduzione con F10, N volte = 2 | Completata, "Riproduzione terminata" |
| Salva macro | Finestra nativa "Salva macro", file scritto e riletto (20 eventi) |
| Carica macro | Finestra nativa "Carica macro", macro caricata |
| Chiusura della finestra | Terminati sia il programma sia il processo di Edge |
| Aspetto | Font Outfit e cavallini 🐴 caricati dagli asset locali, senza rete |

Dopo il primo uso reale (1 click perso su 35, cioè 5 giri da 7 click, con schede aperte in
background) il click minimo di base è passato da 50 a **150 ms** e **Attesa pagina** è attiva di
base, nella schermata principale, con attesa massima di 10 s. L'attesa ora confronta solo i
24×24 pixel centrali del ritaglio (il pulsante), così foto e nome del cavallo attorno possono
cambiare da una scheda all'altra. I test automatici sono stati aggiornati di conseguenza.

**Limite scoperto:** le prime tre build della v0.14 sono partite con Smart App Control attivo,
ma le build successive, identiche salvo le modifiche sopra, sono state bloccate
("Un criterio di controllo dell'applicazione ha bloccato il file", eventi CodeIntegrity 3033,
3077 e 3118). Per un eseguibile non firmato Windows chiede un parere al cloud di Microsoft, e
il risultato cambia da una build all'altra. Senza firma digitale la compatibilità con Smart App
Control non è garantita.

**Versione portatile** (`build_portable.py`): Python ufficiale firmato, librerie di PyPI e
sorgenti `.py`, nessun eseguibile nuovo. Provata su questo PC con Smart App Control attivo,
nel caso reale: zip marcato come scaricato da Internet, estratto in Download con lo stesso
motore di Esplora file (tutti i 1.211 file marcati "da Internet"):

| Prova | Risultato |
| --- | --- |
| Doppio clic su `Mouse Macro Stocazz Superpower.exe` / `(English).exe` | Finestra IT ed EN aperte, nessun blocco nel registro CodeIntegrity |
| `--self-test` IT ed EN | Tutti i controlli superati |
| Carica macro (finestra nativa) | Macro caricata: 20 eventi, 1,29 s |
| Salva macro (finestra nativa) | File scritto, eventi identici all'originale |
| Registrazione con F9 da tastiera | 18 eventi, 1 click, 1,15 s |
| Riproduzione con F10, N volte = 2, Attesa pagina attiva | "Riproduzione terminata", nessuna fermata per pagina non pronta |
| Chiusura della finestra | Programma terminato |

Prima prova con avvio tramite file `.cmd`: bloccato da Smart App Control ("estensione di file
pericolosa dal web"), per questo i file da cliccare sono copie rinominate di `pythonw.exe`.

Le schermate in `docs/screenshots` mostrano la versione finale (150 ms, Attesa pagina nella
schermata principale), avviata dai sorgenti con lo stesso avvio in finestra Edge, perché su
questo PC la build finale viene bloccata da Smart App Control. La build Linux della v0.14 viene compilata e testata da GitHub Actions su
Ubuntu 22.04, ma in questa sessione non è stata provata su un desktop Linux reale.

# Verifica v0.13 beta — 30/09/2026

**58 test superati su Windows e 32 su Linux**, Python 3.14.7 e Flet 1.0.3. Su 62 test raccolti, Windows salta i 4 specifici Linux; Linux salta i 30 specifici Windows.
Comando: `python -m unittest discover -v`.

| Funzione | Verifica effettuata |
| --- | --- |
| Carica e Salva | Clic sui callback effettivi dei pulsanti, coroutine attese e chiamate al trasporto FilePicker reale; trasporto nativo simulato |
| File | Scrittura e rilettura di file reali, nomi con spazi/accenti, coordinate, tempi, riferimenti visivi e geometria dello schermo conservati |
| Annullamento/errori | Annullamento innocuo, errori di scelta file e scrittura visibili, macro precedente conservata se il caricamento fallisce |
| Integrità | Scrittura temporanea e sostituzione finale; simulati disco pieno e sostituzione negata senza alterare il file precedente |
| Registrazione | Avvio/stop dai pulsanti e dalle scorciatoie, eliminazione del click sul pulsante di stop, mantenimento dell'ultimo click con F9 |
| Riproduzione | N volte, Infinito e Durata, numero di giri obbligatorio, velocità e impostazioni effettivamente ricevute dal motore |
| Stop | Pulsante, F10 e scorciatoia di emergenza, rilascio dei tasti premuti e recupero dei controlli |
| Timing | Minimo di 30/50 ms a tutte le velocità dello slider; tempi reali a 0,1x, 1x, 2x, 3x e limite interno 20x |
| Pagina/schede | Confronto e timeout, tolleranza, ripresa quando il punto coincide, Ctrl+W soltanto tra giri |
| Backend Windows | Movimenti, tre pulsanti, rotella, snapshot, chiamate ai controller e hotkey con dispositivi/API simulati |
| Interfaccia | Impostazioni conservate, aiuto e dialoghi, azioni fuori dall'area scorrevole, icona di stop corretta |
| Sessione | Richiesta di stop e rilascio delle hotkey alla disconnessione/chiusura della sessione |

## Limiti ancora aperti

Il controllo della GUI Windows non è disponibile nella sessione di verifica:
il collegamento al helper nativo fallisce anche dopo i tentativi di recupero.
Non sono quindi stati verificati il clic fisico nella finestra, la comparsa
visiva delle finestre file, l'iniezione reale degli input o il risultato su un sito.
Il backend Linux è stato verificato su CachyOS x86_64: eventi evdev, tre pulsanti, rotella, errori di accesso e rilascio uinput. Tutti e quattro i binari IT/EN hanno superato la diagnostica integrata. Su Linux è stato creato e chiuso un dispositivo uinput reale senza emettere eventi. La GUI Flet è stata controllata nel browser a 560×720: questo non equivale al collaudo delle finestre native.

I test non garantiscono che ogni pagina riceva ogni click: deve essere pronta e
la finestra di destinazione deve mantenere posizione, dimensioni e zoom.

## Correzioni

- FilePicker aggiornato alle chiamate asincrone di Flet 1.x e uso dei risultati diretti.
- Salva viene abilitato anche dopo Carica; annullamento/errori gestiti.
- Avvio della riproduzione bloccato durante la registrazione.
- Icona di stop aggiornata attraverso la proprietà corrente `icon`.
- Numeri non finiti nei campi gestiti attraverso il fallback già previsto.
- File macro malformati respinti prima di sostituire la macro aperta.
- Scrittura della macro senza troncare il file precedente prima del completamento.
- Firma di progetto e metadati dell'eseguibile: **hcok**.

- Traduzione inglese della presentazione con valori e formato macro conservati.
- Impostazioni sempre accessibili fuori dall'area scorrevole.
- Su Linux gli errori di apertura del mouse raggiungono la GUI prima della registrazione.
- Una lista mouse vuota azzera anche la selezione precedente.

