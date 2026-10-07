# Convertitore welfare → voci paghe

**[Apri il convertitore online](https://lorejob.github.io/opsexc_jethr/)**

Il tool trasforma i report welfare di cinque provider, in formato Excel o CSV, in un file di voci paghe pronto per l'import nel gestionale.

## Come si usa

1. Seleziona il provider e inserisci il codice ditta e il periodo del cedolino.
2. Carica il file del provider e avvia la conversione.
3. Controlla il riepilogo e scarica il file `VOCI_<ditta>_<AAAAMM>.txt`.

## Come funziona

Per ogni movimento, il convertitore cerca il dipendente nell'anagrafica fornita e associa il trattamento welfare alla voce paghe corretta. Verifica la data e l'importo, poi somma i movimenti per dipendente e voce. Il TXT finale contiene un record per ogni coppia dipendente/voce.

Le righe non riconciliabili vengono escluse dal TXT e mostrate tra gli errori, scaricabili anche in CSV. Se le date del file non corrispondono al periodo selezionato, la conversione si interrompe con un messaggio esplicativo.

La versione online esegue la conversione nel browser: i file caricati non vengono inviati a un server.
