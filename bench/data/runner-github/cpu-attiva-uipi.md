# CPU attiva e finestre elevate: PR #41

Data: 2026-11-16. Sono misure del **sorgente**, non del pacchetto Windows v1.2.3.
Runner condivisi GitHub `windows-latest`, Windows Server 2025, Python 3.13,
skin Bambola, 96 DPI; prove attive/UIPI a 1920×1080. Soglie immutate.

## CPU: prima e seconda tornata, senza modifiche all'app

| Prova (% di un core) | Prima: [43939878453](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43939878453), `148bb38` | Seconda: [43941664289](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43941664289), `f146f7c` | Soglia / esito |
|---|---|---|---|
| Riposo, tre finestre da 20 s dopo 10 s | 1,48 · 0,78 · 1,56 | 2,11 · 2,73 · 2,50 | ≤2: passa la prima; **non passa la seconda** |
| Registrazione, tre finestre da 15 s | 4,17 · 4,06 · 4,27 | 9,06 · 7,71 · 7,40 | ≤5: passa la prima; **non passa la seconda** |
| Eventi registrati | 2237 · 2236 · 2235 | 2178 · 2185 · 2189 | Conteggio del carico, non fedeltà |
| Riproduzione della registrazione densa, tre finestre da 15 s | 10,73 · 12,19 · 13,02 | 14,37 · 14,58 · 14,37 | ≤5: **non passa entrambe** |
| Riproduzione riferimento rado, tre finestre da 15 s | non misurato | 3,12 · 3,33 · 3,02 | ≤5: **passa questa tornata** |

Fonte: JSON estratti dalle righe `RISULTATO` dei job `133554322492` e
`133560492891`, salvati nelle sottocartelle con l'ID del run. I record con
`window_s: 25` appartengono a **cProfile**: non usarli per il confronto CPU.
Ogni valore senza profiler è CPU totale del processo / tempo trascorso, media
sull'intera finestra, non mediana di campioni. Il generatore mouse (~125 Hz)
è un processo separato; la registrazione densa cambia leggermente tra le prove.
Il riferimento ha 29 eventi osservabili (13 down, 13 up, 3 wheel) in circa 16 s,
44 eventi nel formato MMR, inclusi i movimenti; viene ripetuto all'infinito.
Caricamento del riferimento riuscito in tutte le prove; nessun `error` o
`riferimento_errore`, riproduzione densa ancora attiva in tutte le finestre.
`active_view` è letto dopo lo stop finale: non descrive la vista durante la misura.

Entrambe le tornate eseguono lo stesso codice dell'app; cambia il banco
(riferimento aggiunto e ordine degli step). Non è un A/B di un'ottimizzazione.
Il runner condiviso e la durata breve limitano la ripetibilità. Non attribuiamo
con certezza la differenza al rumore né la dichiariamo una regressione dell'app:
il superamento delle soglie a riposo e in registrazione resta aperto.
La precedente ottimizzazione Bambola conserva l'A/B documentato, ma non
garantisce ≤2% su ogni runner. Nella seconda tornata: pixel identici **97/97**,
WM_PAINT **480 · 481 · 480** in 20 s. RAM attiva e CPU dell'exe non misurate.

## UIPI: controllo e blocco silenzioso confermati

Run [43941664269](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43941664269),
commit `f146f7cb6ca7b3945424927b68094bda1869fbf3`, job `133560492443`.
Orchestratore ad integrità alta, verificata con `whoami /groups`;
processo medio avviato con token ristretto a S-1-16-8192. Un'esecuzione per caso.
Contatore indipendente nella finestra elevata; attesi **13 down / 13 up / 3 wheel**.

| Caso | Arrivati down/up/wheel | Uscita | Stato e messaggio pannello |
|---|---|---|---|
| A, riferimento alto→alto | 13 / 13 / 3 | 0 | n.a. |
| B, riferimento medio→alto | 0 / 0 / 0 | 0 | n.a. |
| C, MMSS alto→alto | 13 / 13 / 3 | 0 | pronto; «Completati 1 giri.» |
| D, MMSS medio→alto | 0 / 0 / 0 | 0 | pronto; «Completati 1 giri.» |

In C e D: macro caricata, avvio rilevato, 44 eventi MMR, un giro dichiarato
completato. Il controllo C passa; D **non passa la corretta segnalazione**:
il programma dichiara il completamento senza input consegnato al bersaglio.
`checked_input` non solleva errori; il valore di ritorno di SendInput non è
registrato singolarmente. Non è una prova di elevazione UAC interattiva,
desktop sicuro, giochi o del pacchetto exe. Il workflow verde certifica
l'esecuzione del banco, **non** il rispetto delle soglie o l'assenza del difetto.
Dati: `43941664269/uipi.json`.

## Prossimi interventi e decisione sul timing

Avviso UIPI in PR separata: prima di creare il player, confrontare integrità
del processo e dei bersagli visibili della macro. Se un bersaglio è più alto,
fermare l'avvio con un messaggio che spiega come avviare Mouse Macro come
amministratore. Nessun controllo aggiunto al ciclo temporizzato. Il controllo
fotografa le finestre presenti prima della riproduzione, non quelle che la macro
potrebbe aprire in seguito.

CPU densa: `_wait_until` in `macro/engine.py` esegue spin quando restano fino
a 3 ms; è un candidato, non una causa isolata dal profiler. Proposta da
approvare da Luca: waitable timer Windows ad alta risoluzione e spin residuo
≤0,3 ms, con stop interrompibile. **Nessuna modifica al timing autorizzata in
questa fase.** Dopo un eventuale via: pacchetti prima/dopo, stesso banco,
posizione/intervalli/eventi persi non peggiorati e CPU ridotta; mediana attuale
4,80–4,91 ms contro 5 ms lascia solo 0,09–0,20 ms di margine. Il riferimento
ideale resta necessario per giudicare il p95 su runner condiviso.
