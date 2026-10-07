# Convertitore welfare → voci paghe

**[Apri il convertitore online](https://lorejob.github.io/opsexc_jethr/)**

Soluzione locale al case study Ops Excellence in `description.md`. Legge gli export dei cinque provider del kit, riconcilia dipendenti e trattamenti con i CSV forniti e genera `VOCI_<ditta>_<AAAAMM>.txt`.

## Avvio locale

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Apri `http://127.0.0.1:8000` (oppure imposta la variabile `PORT` per usare un'altra porta). Per eseguire i controlli:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## GitHub Pages

La versione pubblicabile usa la stessa interfaccia e lo stesso `converter.py`. Il motore Python viene eseguito in un Web Worker del browser con Pyodide; i file caricati restano nel browser. Al primo utilizzo serve una connessione per scaricare Pyodide e le librerie Excel. Per rigenerare i file statici in `docs/`:

```bash
.venv/bin/python scripts/build_pages.py
```

GitHub Pages pubblica direttamente la cartella `docs/` del branch `main`. Dopo una modifica alla UI o al convertitore, rigenera `docs/` con il comando sopra e includi i file generati nel commit. GitHub Pages serve file statici e non esegue il server Flask.

## File di esempio

| Provider | Ditta dell'esempio | Formato | Trattamento specifico |
| --- | ---: | --- | --- |
| A | 4012 | XLSX | Intestazione alla riga 4 |
| B | 4027 | CSV | Senza intestazione, `;`, codifica Windows-1252 |
| C | 4041 | XLS | Articolo e riferimento fiscale in colonne separate |
| D | 4093 | CSV | Il codice fiscale presente è del fruitore, non sempre del dipendente |
| E | 4131 | XLSX | `Totale` è l'importo del movimento, anche se quantità > 1 |

La UI accetta provider, codice ditta, periodo e file. Mostra quanti movimenti sono stati letti, convertiti e aggregati, con l'elenco degli scarti scaricabile in CSV. Se ci sono scarti, il TXT è esplicitamente indicato come **parziale** e contiene solo i movimenti validi. I movimenti dei dipendenti presenti in più ditte sono scartati e segnalati come errori.

## Regole di conversione

1. Ogni parser restituisce movimento, identità del dipendente, trattamento, sottocategoria, importo e numero di riga.
2. Il dipendente viene cercato **solo nella ditta indicata**. Si usa il codice fiscale del dipendente quando disponibile; per B e D si confrontano esattamente nome e cognome in entrambi gli ordini. Duplicati identici nell'anagrafica non creano ambiguità. Se il codice fiscale risulta associato a più ditte, il movimento viene escluso anche quando la ditta selezionata ha un solo codice gestionale.
3. La voce viene cercata per trattamento e sottocategoria, poi per trattamento senza sottocategoria. Il confronto ignora maiuscole/minuscole e spazi superflui; se non trova una corrispondenza esatta, normalizza abbreviazioni e punteggiatura (`let`/`lett`, `f-bis`/`f-b`/`f.b`). Se la normalizzazione produce più codici diversi, la riga viene segnalata come ambigua. Per alcune etichette assenti nel mapping si usa il trattamento fiscale generico riconoscibile dall'etichetta: `Art 100 [Iva 22%]` → 370 e `Art. 51 c.2 lett. f-bis` / `Asilo nido` → 373. I codici opachi senza mapping, come `X71133`, diventano scarti.
4. Le date dei movimenti vengono lette e confrontate con il periodo `AAAAMM` inserito dall'utente. Se una data è mancante, non valida o appartiene a un altro mese, la conversione si blocca con un messaggio che indica le righe interessate; non viene generato un TXT parziale per un periodo errato. Gli importi sono convertiti in centesimi con `Decimal` e sommati per `(dipendente, voce)`.
5. I record sono ordinati per codice dipendente numerico e poi per voce. Ogni riga contiene esattamente 38 caratteri ASCII e termina con CRLF, come il file di esempio.

### Dipendenti assenti o presenti in più ditte

Il file `Lista_Dipendenti.csv` del kit non contiene **Alessia Fumagalli**, presente invece nel report A. L'output di esempio le assegna il codice gestionale **25**, ma il convertitore usa esclusivamente l'anagrafica fornita: la riga 8 di Alessia viene esclusa e segnalata come errore.

Il codice fiscale di **Noemi La Rocca** compare sia nella ditta 4012 (codice dipendente 10) sia nella 4175 (codice 900). I suoi quattro movimenti nel report A vengono esclusi con l'errore `Dipendente duplicato in due aziende (4012,4175)`. Il TXT della ditta 4012 contiene quindi 14 record; sono esclusi anche il movimento di Alessia e i quattro di Noemi. Se si seleziona la ditta 4175, nessun movimento del report A viene convertito.

I report B, D ed E contengono altri dipendenti assenti dall'anagrafica e B contiene `X71133`, non presente nel mapping delle voci. Questi casi vengono segnalati come scarti: non si attribuiscono codici per ipotesi.

## Struttura

- `converter.py`: parser, riconciliazione, aggregazione, tracciato.
- `app.py`: interfaccia Flask e API di conversione.
- `templates/` e `static/`: UI custom senza framework frontend.
- `tests/`: confronto con l'output atteso e controlli sui cinque formati.

L'app Flask non conserva i file caricati sul server. Per un'eventuale pubblicazione come servizio WSGI, il comando di avvio è `gunicorn app:app`. Il video richiesto dalla consegna va preparato separatamente.
