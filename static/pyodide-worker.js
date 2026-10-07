import {loadPyodide} from 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs';

const siteRoot = new URL('../', self.location.href);
const assetVersion = new URL(self.location.href).searchParams.get('v');
let enginePromise;

async function initializeEngine() {
  self.postMessage({type: 'status', message: 'Caricamento motore…'});
  const pyodide = await loadPyodide();
  await pyodide.loadPackage('micropip');
  await pyodide.runPythonAsync(`
import micropip
await micropip.install(['openpyxl==3.1.5', 'xlrd==2.0.2'])
`);

  const paths = [
    ['converter.py', '/app/converter.py'],
    ['config/Lista_Dipendenti.csv', '/app/Kit Candidato/config/Lista_Dipendenti.csv'],
    ['config/Codici_Welfare_Voci_Payroll.csv', '/app/Kit Candidato/config/Codici_Welfare_Voci_Payroll.csv'],
  ];
  pyodide.FS.mkdirTree('/app/Kit Candidato/config');
  await Promise.all(paths.map(async ([url, path]) => {
    const assetUrl = new URL(url, siteRoot);
    if (assetVersion) assetUrl.searchParams.set('v', assetVersion);
    const response = await fetch(assetUrl);
    if (!response.ok) throw new Error(`Impossibile caricare ${url}.`);
    pyodide.FS.writeFile(path, new Uint8Array(await response.arrayBuffer()));
  }));
  pyodide.runPython("import sys; sys.path.insert(0, '/app'); import converter");
  return pyodide;
}

self.addEventListener('message', async (event) => {
  try {
    if (!enginePromise) enginePromise = initializeEngine();
    const pyodide = await enginePromise;
    self.postMessage({type: 'status', message: 'Conversione in corso…'});
    const {provider, company, period, filename, data} = event.data;
    pyodide.FS.writeFile('/app/upload', new Uint8Array(data));
    pyodide.globals.set('provider_arg', provider);
    pyodide.globals.set('company_arg', company);
    pyodide.globals.set('period_arg', period);
    pyodide.globals.set('filename_arg', filename);
    const result = JSON.parse(pyodide.runPython(`
import json
from pathlib import Path
from converter import ConversionError, convert

try:
    result = convert(provider_arg, company_arg, period_arg, filename_arg, Path('/app/upload').read_bytes())
    payload = {
        'filename': result.filename,
        'content': result.content,
        'input_rows': result.input_rows,
        'converted_rows': result.converted_rows,
        'output_rows': result.output_rows,
        'issues': [issue.as_dict() for issue in result.issues],
        'warnings': [warning.as_dict() for warning in result.warnings],
    }
except ConversionError as exc:
    payload = {'error': str(exc)}
json.dumps(payload)
`));
    if (result.error) self.postMessage({error: result.error});
    else self.postMessage({result});
  } catch (error) {
    enginePromise = null;
    self.postMessage({error: `Impossibile completare la conversione: ${error.message || error}`});
  }
});
