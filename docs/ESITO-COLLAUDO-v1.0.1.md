# Esito dei controlli v1.0.1

Release di compatibilità con **Smart App Control** (Controllo intelligente delle app di Windows 11). Il codice di registrazione, replay e interfaccia è **identico alla v1.0.0**: cambiano solo il numero di versione, le vie di avvio e la documentazione.

## Novità rispetto alla v1.0.0

- **`Mouse Macro v1.0.1 (senza exe).cmd`** nello ZIP: avvia direttamente `runtime\pythonw.exe` (firmato dalla Python Software Foundation) con `app\windows_main.py`, senza passare dal launcher `.exe` non firmato.
- **`install.ps1`**: `irm …/install.ps1 | iex` scarica la release da GitHub, verifica lo SHA-256 con `SHA256SUMS`, estrae in `%LOCALAPPDATA%\MouseMacroStocazzSuperpower\Portable` e avvia il programma. Usa solo cmdlet base.
- Documentazione (README IT/EN, Guida, BUILD) con la sezione «Windows blocca l'exe?».
- `qa/check_package.py` verifica anche che il `.cmd` nello ZIP coincida con `launcher.cmd`.

## Verifiche eseguite

Ambiente: Windows 11 Pro build 26300, **Smart App Control attivo** (`VerifiedAndReputablePolicyState = 1`), Python 3.13.

- **Suite automatica**: 141 test, 135 superati, 6 saltati (backend Linux).
- **Pacchetto**: build riproducibile con `build_native_windows.py`, `qa/check_package.py` superato (CRC validi, hash del manifest, sorgenti identici, file originali del runtime preservati, `.cmd` identico a `launcher.cmd`).
- **Avvio dell'exe con Smart App Control attivo**: **bloccato** da Windows («Un criterio di controllo dell'applicazione ha bloccato il file»). È il comportamento atteso per un exe non firmato e senza reputazione: l'exe resta non firmato.
- **Avvio del `.cmd` con Smart App Control attivo**: il programma parte, finestra «Mouse Macro 1.0.1 · hcok · pronto», processo `pythonw.exe` del runtime incluso.
- **Avvio da PowerShell** (`install.ps1`) con Smart App Control attivo: vedi sezione sotto.

## Non verificato

- La prova fisica di registrazione/replay non è stata ripetuta: vale il [rapporto v1.0.0](ESITO-COLLAUDO-v1.0.0.md) per il codice invariato.
- Smart App Control è stato provato su **un solo PC**; la valutazione cloud di reputazione può dare esiti diversi su altre macchine.
- SentinelOne e policy aziendali (AppLocker/WDAC) non sono certificati. Windows 10 e Windows 11 senza Smart App Control non sono stati riprovati.

## Limiti

Coordinate assolute; nessuna conferma che un sito abbia accettato il click; nessun retry. Launcher `.exe` non firmato; UAC/desktop sicuro e applicazioni con privilegi elevati non coperti. Nessuna protezione di Windows è stata modificata o disattivata per ottenere questi risultati.

SHA-256 del ZIP: nel file `SHA256SUMS-v1.0.1.txt` allegato alla release.
