const form = document.getElementById('conversion-form');
const provider = document.getElementById('provider');
const company = document.getElementById('company');
const companyHint = document.getElementById('company-hint');
const fileInput = document.getElementById('file');
const fileName = document.getElementById('file-name');
const fileHint = document.getElementById('file-hint');
const dropzone = document.getElementById('dropzone');
const convertButton = document.getElementById('convert-button');
let latestResult = null;
let browserWorker = null;

provider.addEventListener('change', () => {
  const selected = provider.selectedOptions[0];
  const extension = selected.dataset.extension;
  fileInput.accept = extension;
  company.placeholder = `Es. ${selected.dataset.company}`;
  companyHint.textContent = `Ditta del file di esempio: ${selected.dataset.company}`;
  fileHint.textContent = `${extension.toUpperCase()} · massimo 10 MB`;
  fileInput.value = '';
  fileName.textContent = 'Scegli un file o trascinalo qui';
});

fileInput.addEventListener('change', () => {
  fileName.textContent = fileInput.files[0]?.name || 'Scegli un file o trascinalo qui';
});

for (const eventName of ['dragenter', 'dragover']) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add('dragging');
  });
}
for (const eventName of ['dragleave', 'drop']) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove('dragging');
  });
}
dropzone.addEventListener('drop', (event) => {
  if (!event.dataTransfer.files.length) return;
  fileInput.files = event.dataTransfer.files;
  fileName.textContent = fileInput.files[0].name;
});

function showError(message) {
  document.getElementById('empty-result').classList.add('hidden');
  document.getElementById('conversion-result').classList.add('hidden');
  const errorBox = document.getElementById('error-result');
  errorBox.textContent = message;
  errorBox.classList.remove('hidden');
}

function csvCell(value) {
  return `"${String(value).replaceAll('"', '""')}"`;
}

function downloadBlob(content, filename, type) {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderRows(body, rows) {
  body.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement('tr');
    const number = document.createElement('td');
    number.textContent = row.row;
    const person = document.createElement('td');
    person.className = 'issue-person';
    const name = document.createElement('strong');
    name.textContent = row.person;
    const fiscalCode = document.createElement('small');
    fiscalCode.textContent = `CF: ${row.fiscal_code}`;
    person.append(name, fiscalCode);
    const detail = document.createElement('td');
    detail.textContent = row.detail;
    tr.append(number, person, detail);
    body.appendChild(tr);
  }
}

function showResult(result) {
  latestResult = result;
  document.getElementById('empty-result').classList.add('hidden');
  document.getElementById('error-result').classList.add('hidden');
  document.getElementById('conversion-result').classList.remove('hidden');
  document.getElementById('input-count').textContent = result.input_rows;
  document.getElementById('converted-count').textContent = result.converted_rows;
  document.getElementById('output-count').textContent = result.output_rows;
  document.getElementById('output-filename').textContent = result.filename;

  const banner = document.getElementById('status-banner');
  const hasIssues = result.issues.length > 0;
  const hasWarnings = result.warnings.length > 0;
  banner.className = `status-banner ${hasIssues ? 'partial' : hasWarnings ? 'attention' : 'complete'}`;
  if (hasIssues) {
    banner.textContent = `Conversione con errori: ${result.issues.length} ${result.issues.length === 1 ? 'riga esclusa' : 'righe escluse'}. Il TXT contiene solo i movimenti validi.${hasWarnings ? ` ${result.warnings.length} ${result.warnings.length === 1 ? 'avviso su una riga convertita' : 'avvisi su righe convertite'}.` : ''} Controlla le segnalazioni qui sotto.`;
  } else if (hasWarnings) {
    banner.textContent = `Conversione completata con ${result.warnings.length} ${result.warnings.length === 1 ? 'avviso' : 'avvisi'}. Il TXT include anche queste righe: controlla i dipendenti presenti in più aziende.`;
  } else {
    banner.textContent = 'Conversione completata: tutti i movimenti sono stati elaborati.';
  }

  const downloadButton = document.getElementById('download-button');
  downloadButton.disabled = result.output_rows === 0;
  downloadButton.textContent = result.output_rows ? 'Scarica ↓' : 'Nessuna riga';
  const issuesSection = document.getElementById('issues-section');
  issuesSection.classList.toggle('hidden', !hasIssues);
  document.getElementById('issues-count').textContent = hasIssues ? result.issues.length : '';
  renderRows(document.getElementById('issues-body'), result.issues);
  const warningsSection = document.getElementById('warnings-section');
  warningsSection.classList.toggle('hidden', !hasWarnings);
  document.getElementById('warnings-count').textContent = hasWarnings ? result.warnings.length : '';
  renderRows(document.getElementById('warnings-body'), result.warnings);
}

async function convertInBrowser(formData) {
  const file = formData.get('file');
  const data = await file.arrayBuffer();
  if (!browserWorker) {
    const workerUrl = new URL('static/pyodide-worker.js', document.baseURI);
    if (window.APP_VERSION) workerUrl.searchParams.set('v', window.APP_VERSION);
    browserWorker = new Worker(workerUrl, {type: 'module'});
  }
  return new Promise((resolve, reject) => {
    const worker = browserWorker;
    function cleanup() {
      worker.removeEventListener('message', onMessage);
      worker.removeEventListener('error', onError);
    }
    function onMessage(event) {
      if (event.data.type === 'status') {
        document.getElementById('button-label').textContent = event.data.message;
        return;
      }
      cleanup();
      if (event.data.error) reject(new Error(event.data.error));
      else resolve(event.data.result);
    }
    function onError() {
      cleanup();
      worker.terminate();
      browserWorker = null;
      reject(new Error('Impossibile avviare il motore nel browser. Verifica la connessione e riprova.'));
    }
    worker.addEventListener('message', onMessage);
    worker.addEventListener('error', onError);
    worker.postMessage({
      provider: formData.get('provider'),
      company: formData.get('company'),
      period: formData.get('period'),
      filename: file.name,
      data,
    }, [data]);
  });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  convertButton.disabled = true;
  document.getElementById('button-label').textContent = 'Conversione in corso…';
  try {
    let result;
    if (window.CONVERSION_MODE === 'browser') {
      result = await convertInBrowser(new FormData(form));
    } else {
      const response = await fetch('/api/convert', {method: 'POST', body: new FormData(form)});
      result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Conversione non riuscita.');
    }
    showResult(result);
  } catch (error) {
    latestResult = null;
    showError(error.message || 'Errore di connessione. Riprova.');
  } finally {
    convertButton.disabled = false;
    document.getElementById('button-label').textContent = 'Converti il file';
  }
});

document.getElementById('download-button').addEventListener('click', () => {
  if (latestResult?.output_rows) downloadBlob(latestResult.content, latestResult.filename, 'text/plain;charset=us-ascii');
});

function downloadReport(rows, prefix, detailHeader) {
  const report = [['Riga', 'Dipendente', 'Codice fiscale', detailHeader], ...rows.map(row => [row.row, row.person, row.fiscal_code, row.detail])];
  const content = '\uFEFF' + report.map(row => row.map(csvCell).join(';')).join('\r\n') + '\r\n';
  downloadBlob(content, latestResult.filename.replace('VOCI_', `${prefix}_`).replace('.txt', '.csv'), 'text/csv;charset=utf-8');
}

document.getElementById('issues-download').addEventListener('click', () => {
  if (latestResult?.issues.length) downloadReport(latestResult.issues, 'SCARTI', 'Problema');
});

document.getElementById('warnings-download').addEventListener('click', () => {
  if (latestResult?.warnings.length) downloadReport(latestResult.warnings, 'AVVISI', 'Segnalazione');
});
