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

