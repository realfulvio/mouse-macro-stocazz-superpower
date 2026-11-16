# Test di usabilità a tempo (persone che non conoscono il programma)

Obiettivo: misurare quanto ci vuole a una persona **nuova** per registrare e ripetere una macro semplice, con noi e con i rivali principali.

## Chi
- **≥ 5 persone per strumento** (meglio 8), che non hanno mai usato quello strumento. Persone diverse per strumento (between-subjects) oppure ordine bilanciato se le stesse persone provano due strumenti.
- Profilo: impiegati abituati al PC ma non tecnici (es. colleghi di altri uffici), non il CED. Annotare età, uso del PC, se hanno già usato macro (sì/no). Codici P01… senza nomi.

## Compito (identico per tutti)
Su una VM pulita con lo strumento già installato e la finestra del Blocco note aperta accanto:
1. Registra una macro che clicca tre punti indicati dal moderatore (tre caselle disegnate a schermo).
2. Riproducila **3 volte**.
3. Fermala a metà durante la seconda riproduzione.

Consegna: foglio con i tre passaggi, **nessuna spiegazione** sullo strumento. Il moderatore non aiuta; se la persona è bloccata da 3 minuti, segna "abbandono" e passa oltre.

## Cosa si registra
Per persona e strumento, in `data/usabilita.csv`:
`participant,tool,success,time_s,errors,sus1..sus10`
- `success` = 1 solo se i tre passaggi sono riusciti senza aiuto; `time_s` dal via al completamento (cronometro a mano o registrazione schermo);
- `errors` = clic/azioni sbagliate rilevanti (conta il moderatore con la registrazione schermo);
- SUS: 10 domande standard (1–5) subito dopo; **versione italiana validata** (non tradurre al volo).
- Note libere: dove si è bloccata, cosa ha cercato, parole usate.

## Soglie (fissate in `thresholds.json`)
Successo ≥ 80 %, tempo mediano dei riusciti ≤ 120 s, SUS mediano ≥ 68. Con meno di 5 persone: "INSUFFICIENTE".

## Analisi
`python usability_analyze.py data/usabilita.csv`. Con n piccolo si riportano i dati grezzi accanto ai sommari; nessun test statistico con n < 8.

## Consenso e privacy
Registrazione schermo solo con consenso scritto, nessun dato identificativo, cancellazione dopo l'analisi.
