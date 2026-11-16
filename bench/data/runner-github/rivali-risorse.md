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
| OP Auto Clicker | [sito](https://www.opautoclicker.com/downloads.html) → [progetto mousetool](https://sourceforge.net/projects/orphamielautoclicker/files/4.1/AutoClicker.exe/download) | EXE, SHA-256 pubblicato dalla pagina download SourceForge |
| Actiona 3.11.5 | [release autore](https://github.com/Jmgr/actiona/releases/tag/v3.11.5) | Installer Inno Setup rilevato nel pacchetto, digest SHA-256 GitHub |

Gli hash attesi sono nel registro `TOOLS` di `bench/ci/run_tool.py`; ogni
download viene verificato prima di eseguire il programma. URL effettivo, peso
in byte e hash calcolato finiscono in `inventario.json`; versione del binario,
titoli delle finestre e comando di installazione nei risultati. I file sono
archiviati come artifact `risorse-<strumento>` del run. Nessuna misura locale
sul notebook, SRV-AI o mini-PC.

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

## Esiti acquisiti

Run [43945606448](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43945606448), head `825340b`, checkout di merge `53e3b1d`. Dati grezzi CSV/JSON e log installazione nella cartella omonima. Valori arrotondati soltanto nella tabella.

| Programma | Pacchetto MB | CPU media, % core | Privata max MiB | Avvio caldo mediana / p95, s | Avvii riusciti | Soglie |
|---|---:|---:|---:|---:|---:|---|
| Pulover 5.4.1 | 10,981 | 0,502 | 40,68 | 0,911 / 0,932 | 15/15 | passa peso, CPU, memoria, avvio |
| Jitbit 5.9.0.0, prova | 2,725 | 0,026 | 15,39 | 0,279 / 0,292 | 15/15 | passa le quattro soglie in questa tornata |
| OP Auto Clicker 4.1 | 1,187 | 0,106 | 19,52 | 0,163 / 0,179 | 15/15 | passa le quattro soglie |
| Actiona 3.11.5 | 75,835 | 0,000 | 24,61 | 1,091 / 1,188 | 15/15 | peso non passa ≤25 MB; altre tre passano |
| Mini Mouse Macro MSI | 10,540 | non misurato | non misurato | non misurato | non misurato | peso passa; installazione riuscita, selezione exe fallita |

Ogni misura a riposo comprende 57 intervalli validi, circa 59 s osservati. Jitbit ha ricevuto un runner Intel Family 6 Model 207; gli altri AMD Family 25. Non sono confronti sullo stesso hardware. Gli 0,000% di Actiona sono il risultato della risoluzione del campionamento, non un consumo fisico nullo. Era aperta la finestra iniziale **Automatic updates** insieme a `untitled.ascr`: la misura vale per questo stato. Jitbit mostrava **evaluation**.

Nel run precedente `43944793133`, Jitbit aveva 14/15 avvii riusciti (primo scaduto), mediana a caldo 0,2115 s e p95 1,37445 s: soglia avvio non passata per l'avvio mancante. Il nuovo 15/15 non cancella questa variabilità. Pulover e Actiona hanno completato anche le tornate precedenti.

Mini Mouse Macro: download e hash ufficiale corretti, MSI uscita 0; il pacchetto ignora `INSTALLDIR` e installa sia `MiniMouseMacro.exe` sia `app/9.0.0/MiniMouseMacro.exe` sotto Program Files (x86). Il banco ha rifiutato l'ambiguità. La selezione ora usa il launcher principale, coerente con la directory dei collegamenti nel log MSI; serve la nuova esecuzione per misurare avvio e risorse. Nessun fallimento è stato trasformato in uno zero.

I primi tentativi SourceForge ricevevano HTML invece del binario: sono stati rifiutati. Il downloader segue ora il meta-refresh HTTPS soltanto verso mirror SourceForge e verifica ancora l'hash prima dell'esecuzione. I quattro binari misurati e l'MSI hanno inventario e provenienza separati; la fedeltà dei cinque rivali resta **non misurata**.
