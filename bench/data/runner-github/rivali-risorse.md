# Risorse dei rivali: protocollo e provenienza

Solo Windows, runner GitHub pulito per ciascun programma. **Fedeltà non
misurata**: nessun avvio della macro di riferimento per i cinque nuovi rivali.
Raccolta separata in `rivals.yml` finché l'affidabilità dei job non è verificata;
la matrice principale `bench.yml` resta MMSS/AHK/TinyTask/ideale.

| Rivale | Fonte ufficiale verificata il 2026-11-16 | Pacchetto / installazione |
|---|---|---|
| Pulover 5.4.1 | [sito](https://www.macrocreator.com/download/) → [release autore](https://github.com/Pulover/PuloversMacroCreator/releases/tag/v5.4.1) | ZIP portabile, eseguibile x64; hash registrato qui, non pubblicato dall'autore |
| Jitbit | [sito](https://www.jitbit.com/macro-recorder/) → `static.jitbit.com/mr/MacroRecorderSetup.exe` | Prova, installer Inno Setup rilevato nel pacchetto; hash registrato qui |
| Mini Mouse Macro | [progetto dell'autore turnssoft](https://sourceforge.net/projects/minimousemacro/files/) | MSI corrente; SHA-256 pubblicato nella [pagina download](https://sourceforge.net/projects/minimousemacro/files/MiniMouseMacro.Setup.msi/download), non il vecchio exe portabile |
| OP Auto Clicker | [sito](https://www.opautoclicker.com/downloads.html) → [progetto mousetool](https://sourceforge.net/projects/orphamielautoclicker/files/AutoClicker.exe/download) | EXE, SHA-256 pubblicato dalla pagina download SourceForge |
| Actiona 3.11.5 | [release autore](https://github.com/Jmgr/actiona/releases/tag/v3.11.5) | Installer Inno Setup rilevato nel pacchetto, digest SHA-256 GitHub |

Gli hash attesi sono nel registro `TOOLS` di `bench/ci/run_tool.py`; ogni
download viene verificato prima di eseguire il programma. URL effettivo, peso
in byte e hash calcolato finiscono in `inventario.json`; versione del binario,
titoli delle finestre e comando di installazione nei risultati. I file sono
archiviati come artifact `risorse-<strumento>` del run. Nessuna misura locale
sul notebook, server-di-prova o mini-PC.

Installazione silenziosa, solo sul runner:
- Inno Setup: `<setup.exe> /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /DIR=<destinazione> /LOG=<log>`.
- MSI: `msiexec.exe /i <pacchetto.msi> /qn /norestart INSTALLDIR=<destinazione> /L*v <log>`.
- ZIP/EXE portabili: estrazione/copia e avvio diretto.

Fonti parametri: [Inno Setup](https://jrsoftware.org/inno-setup/documentation/topic_setupcmdline.htm),
[Windows Installer](https://learn.microsoft.com/en-us/windows/win32/msi/standard-installer-command-line-options).
Il comando concreto e l'esito sono in `install.json`; un errore non diventa
una misura di zero CPU o zero memoria.

Avvio: 15 ripetizioni, prima finestra visibile e reattiva. Può essere un
dialogo iniziale/licenza: i titoli raccolti lo rendono verificabile. `cold=1`
significa soltanto primo avvio della serie, non cache disco garantita fredda.
Risorse: 10 s di assestamento, poi 60 s di campionamento del processo e figli.
CPU media pesata sul tempo di osservazione, % di un core; memoria massima
privata in MiB (lo script PowerShell usa 1MB binario), pacchetto in MB decimali.
Se il processo sparisce, la misura è rifiutata. Le soglie sono quelle congelate.

Esiti da compilare con dati CI; nessun valore prestazionale dedotto da dimensioni
pubblicizzate, requisiti di sistema o dichiarazioni dei siti.
