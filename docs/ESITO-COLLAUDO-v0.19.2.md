# Esito dei controlli v0.19.2-beta

La v0.19.2 parte dalla v0.19.0 (barra operativa, ripetizioni digitabili) e corregge alcuni difetti di robustezza. Il motore di riproduzione e i tempi non cambiano.

## Correzioni rispetto alla v0.19.0

- **Chiusura**: se il file delle impostazioni non era scrivibile, o il player impiegava troppo a fermarsi, la chiusura della finestra poteva lasciare attivi la riproduzione e i tasti globali. Ora finestra e tasti vengono sempre chiusi.
- **Posizione del pannello**: chiudendo durante registrazione o replay veniva persa la posizione del pannello completo. Ora viene salvata.
- **Registrazione**: se la finestra del pannello spariva mentre il mouse era in registrazione, l'hook poteva interrompersi con un'eccezione. Ora il gesto viene registrato normalmente.
- **File macro**: una macro con eventi incompleti o campi sconosciuti mostrava un errore tecnico di Python; ora il messaggio è leggibile e la macro caricata resta intatta.
- **Build**: la build non richiede più l'esatto Python 3.13.16 sull'interprete host (il runtime distribuito resta quello ufficiale 3.13.16, verificato); il nome di `SHA256SUMS` segue la versione; metadati del launcher e `version_info.txt` allineati; import inutilizzati rimossi.

## Verifiche eseguite su questo ZIP

- Suite automatica: **141 test, 135 superati, 6 saltati** (backend Linux), Python 3.13 su Windows 11. Incluse tre regressioni nuove (macro malformate, pannello distrutto durante la registrazione).
- `qa/check_package.py`: CRC validi, 105 hash del manifest, sorgenti e asset identici, file originali del runtime preservati; il runtime coincide con il pacchetto ufficiale scaricato da python.org.
- Avvio reale dell'exe estratto dallo ZIP: finestra «Pronto» in italiano, nessun file di errore creato.

## Non rieseguito su questo ZIP

Registrazione e replay con input fisico non sono stati ripetuti sulla v0.19.2. Le prove native della v0.19.0 (17 eventi registrati; 20 giri a 1× in 80,3 s e a 2× in 47,3 s con conteggi identici; F10 ed Emergenza durante una pressione, con rilascio del mouse) restano valide per il codice invariato, ma non certificano le correzioni sopra. Restano da provare: pulsante Stop durante la registrazione, DPI diversi dal 100%, avvio senza rete, regressioni con cambio scheda nel browser.

## Limiti

Coordinate assolute; nessuna conferma che un sito abbia accettato il click; nessun retry. Launcher non firmato; nessuna certificazione SentinelOne o Smart App Control; UAC/desktop sicuro e applicazioni con privilegi elevati non coperti.

SHA-256 del ZIP: indicato in `SHA256SUMS-v0.19.2.txt` allegato alla release.
