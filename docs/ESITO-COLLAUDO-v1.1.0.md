# Esito dei controlli v1.1.0

Aggiunge skin, pallino aggiornamenti e modalità «movimento umano». Il motore di registrazione e il replay predefinito sono **invariati**: con «movimento umano» spento il replay è identico alla v1.0.x (verificato da un test che confronta gli eventi riprodotti con la registrazione).

## Novità rispetto alla v1.0.1

- **Skin** *Unicorno* e *Palio*: palette e mascotte (quattro espressioni: pronto, registrazione, riproduzione, errore) per skin; pulsante di scelta in alto, scelta salvata nelle impostazioni. Aggiungere una skin richiede solo quattro PNG e una palette.
- **Aggiornamenti** (`macro/updater.py`): lettura anonima dell'ultima release GitHub all'avvio (disattivabile), pallino verde/giallo/grigio, installazione solo su richiesta con verifica SHA-256 contro `SHA256SUMS`, rifiuto di ZIP con percorsi non sicuri o incompleti, riavvio automatico.
- **Movimento umano** (Opzioni, spento di default): ogni giro varia curva e velocità dei soli movimenti liberi del cursore e le pause; pressioni, rilasci, rotella e trascinamenti restano identici.
- `install.ps1` avvia la versione più recente già installata invece di reinstallare quella fissata.
- La casella numerica delle ripetizioni usa i colori della skin (prima usava quelli di sistema).

## Verifiche eseguite

Ambiente: Windows 11 Pro build 26300, **Smart App Control attivo** (`VerifiedAndReputablePolicyState = 1`), Python 3.13.

- **Suite automatica**: 162 test, 156 superati, 6 saltati (backend Linux). Nuovi: 11 sul modulo di aggiornamento (rete simulata: confronto versioni, errori offline, hash errato, path traversal, pacchetto incompleto, pulizia delle versioni vecchie) e 10 su «movimento umano» (clic invariati, estremi dei tragitti esatti, scostamento limitato, tempi monotoni, trascinamenti intatti, spento di default).
- **Pacchetto**: `qa/check_package.py` superato (112 hash del manifest, sorgenti identici, runtime originale preservato, `.cmd` identico a `launcher.cmd`).
- **Interfaccia reale**, avviata dai sorgenti con una cartella impostazioni isolata e catturata finestra per finestra (`PrintWindow`): vista compatta, vista con le Opzioni e barra di registrazione, in **entrambe le skin**; interruttore «Movimento umano» acceso con il messaggio di conferma.
- **Controllo aggiornamenti contro GitHub** (rete reale): con la 1.1.0 non ancora pubblicata, pallino verde (aggiornato rispetto alla 1.0.1).
- **Avvio del `.cmd` del pacchetto 1.1.0** con Smart App Control attivo: il programma parte («Mouse Macro 1.1.0 · pronto»).
- **Avvio dell'exe con Smart App Control attivo**: l'esito **non è deterministico**. Nel collaudo della v1.0.1 Windows lo ha bloccato («Un criterio di controllo dell'applicazione ha bloccato il file»); in una prova successiva, sullo stesso PC, sia l'exe 1.0.1 sia l'exe 1.1.0 sono partiti. L'exe resta non firmato e dipende dalla reputazione che Microsoft gli assegna.

## Non verificato

- «Movimento umano» è coperto da test del motore, ma **non è stato provato con un replay fisico su desktop o su un sito reale**. Non garantisce di non essere rilevato come automazione.
- La prova fisica di registrazione/replay resta quella del [rapporto v1.0.0](ESITO-COLLAUDO-v1.0.0.md).
- Menu delle skin e menu del pallino: il codice è provato solo fino alla creazione della finestra e al disegno; la scelta da menu con il mouse non è stata automatizzata.
- Smart App Control provato su **un solo PC**. SentinelOne, AppLocker/WDAC, Windows 10 e altre scale DPI non sono stati riprovati.
- Le skin *Mezzanotte* e *Scacchi* mostrate nei bozzetti non sono incluse: mancano le immagini.
- La verifica SHA-256 dell'aggiornamento protegge da download corrotti, ma `SHA256SUMS` arriva dalla stessa release: non sostituisce una firma digitale dell'editore.

## Limiti

Coordinate assolute; nessuna conferma che un sito abbia accettato il click; nessun retry. Launcher `.exe` non firmato; UAC/desktop sicuro e applicazioni con privilegi elevati non coperti. Nessuna protezione di Windows è stata modificata o disattivata.

SHA-256 del ZIP: nel file `SHA256SUMS-v1.1.0.txt` allegato alla release.
