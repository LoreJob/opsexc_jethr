# Case Study Ops Excellence – Convertitore welfare universale

## **Scenario**

Jet HR elabora i cedolini per centinaia di aziende clienti, molte delle quali offrono ai dipendenti un **piano welfare** gestito da un provider esterno.

Ogni mese il provider manda un report con quello che ogni dipendente ha speso: buoni acquisto, rimborsi di spese scolastiche, versamenti alla previdenza complementare, servizi ricreativi. Ogni movimento ha un trattamento fiscale diverso (art. 51 c.3 fringe benefit, art. 51 c.2 lett. f, f-bis, h, ecc.) e deve finire in busta paga sulla **voce payroll** corretta.

Il problema: **ogni provider usa un report diverso**. Il file è sempre un Excel o un CSV, ma cambiano tutto il resto: colonne, intestazioni, righe di titolo, separatori, formato degli importi, chiave del dipendente e soprattutto il modo di indicare il trattamento fiscale.

## **Obiettivo del progetto**

Realizzare un **convertitore welfare universale**: un motore unico che, configurato una volta per ogni provider, trasforma il report del provider nel tracciato di import delle voci retributive del gestionale paghe.

Il convertitore riceve in input:

1. **Provider** (es. Provider A, Provider B, Provider C)
2. **Codice ditta** (il numero della ditta nel gestionale)
3. **Periodo del cedolino** (AAAAMM)
4. **File del provider** (xlsx, xls o csv)

E restituisce:

1. **File voci** nel tracciato di destinazione

## **Materiale fornito**

In fondo alla pagina trovi il kit (`kit_candidato.zip`). Al suo interno trovi diversi esempi di export dei provider con dati anonimizzati/inventati.

I file aggiuntivi sono file che riconciliano i dipendenti e le voci welfare al loro codice nel gestionale. 

Gli importi si sommano per dipendente e voce: **un record per coppia dipendente/voce**.

## **Tracciato di destinazione**

L'output è sempre lo stesso, qualunque sia il provider: il file `VOCI_<ditta>_<AAAAMM>.txt`, a **record a lunghezza fissa** di 38 caratteri, un record per riga, solo caratteri ASCII, nessuna intestazione.

- **N (numerico)**: allineato a destra, riempito con zeri; con decimali il valore è moltiplicato per 100 senza separatore (25,73 → `000002573`).
- **A (alfanumerico)**: allineato a sinistra, riempito con spazi.

| **Campo** | **Posizione** | **Lunghezza** | **Tipo** | **Regola** |
| --- | --- | --- | --- | --- |
| Codice ditta | 1 | 6 | N | Codice inserito in input |
| Codice dipendente | 7 | 6 | A | Codice gestionale del dipendente |
| Codice voce | 13 | 4 | A | Codice gestionale della voce welfare |
| Quantità | 17 | 7 | N, 2 decimali | Sempre zeri |
| Importo | 24 | 9 | N, 2 decimali | Somma degli importi del dipendente per quella voce |
| Periodo | 33 | 6 | AAAAMM | Periodo del cedolino inserito in input |

Ordinamento: codice dipendente crescente (numerico), poi codice voce.

Esempio: `0040124     371 0000000000002244202609` = ditta 4012, dipendente 4, voce 371, importo 22,44, cedolino di settembre 2026.

## **Requisiti tecnici e interfaccia**

Puoi usare lo strumento che preferisci: codice, strumenti no-code, fogli di calcolo. Deve però:

- funzionare ed essere **accessibile online** da chiunque abbia il link;
- prendere un file in input (pulsante di selezione) e restituire i file di output (download o link);
- deve essere facile da utilizzare e l’utente deve essere guidato dall’input fino allo scaricamento finale del file.

Non usare strumenti di *vibe coding* come Lovable, Bolt.new, Base44, Replit Agent, Firebase Studio. Questi non ci permettono di verificare se sei tu a guidare l’AI o viceversa. Gli assistenti AI possono essere utilizzati come strumenti di supporto.

Interfaccia minima:

```
+------------------------------------------+
| Provider:        [ Provider A    ▼ ]     |
| Codice ditta:    [___________]           |
| Periodo:         [ 202609 ]              |
| File input:      [ Scegli file ]         |
|                                          |
|            [   Converti   ]              |
|                                          |
| Esito: ...    |
| [ Scarica VOCI ]       |
+------------------------------------------+
```

Tutto quello che aggiungi è a tua discrezione.

## **Come lo testeremo**

Confronteremo i tuoi output con quelli attesi per gli export di esempio (o alcuni di questi se non riesci a gestirli tutti).

## **Consegna**

- Il **link** al convertitore, funzionante e accessibile.
- Un **video di massimo 5 minuti** in cui spieghi la soluzione, come l'hai strutturata e le scelte che hai fatto.

Se trovi un caso non coperto da quanto condiviso nella consegna, applica un’interpretazione logica a tua discrezione.

## **Kit**

Kit Candidato.zip

Buon lavoro! 💪🏻