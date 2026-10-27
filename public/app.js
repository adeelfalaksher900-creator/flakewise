const $ = s => document.querySelector(s);
const byId = id => document.getElementById(id);
const MAX_FILE = 512 * 1024, MAX_TOTAL = 2 * 1024 * 1024, MAX_FILES = 12, REQUEST_TIMEOUT = 30000;
const COMMIT = /^[0-9a-f]{7,64}$/i;
const encoder = new TextEncoder();
let files = [], report = null, selectedId = null, isSample = false, busy = false, activeRequest = null, readToken = null;
const labels = { mixed: 'Inconsistent outcomes', failed: 'Failed only', passed: 'Passed only', skipped: 'Skipped', insufficient: 'Insufficient evidence' };
const element = (tag, content, className) => { const e = document.createElement(tag); if (content !== undefined) e.textContent = String(content); if (className) e.className = className; return e; };
const error = message => { byId('form-error').textContent = message; byId('form-error').hidden = !message; };
function clearResults() {
  report = null; selectedId = null;
  byId('results').hidden = true; byId('result-loading').hidden = true; byId('result-empty').hidden = false;
  byId('details').hidden = true; byId('copy-status').textContent = '';
}
function setBusy(value) {
  busy = value; byId('analyze').disabled = value; byId('file-input').disabled = value;
  byId('commit').disabled = value; byId('load-sample').disabled = value; byId('load-sample-empty').disabled = value;
  document.querySelectorAll('.remove, .commit-override input').forEach(control => { control.disabled = value; });
  byId('analyze').textContent = value ? 'Comparing reports…' : 'Compare reports →';
  byId('result-empty').hidden = value || Boolean(report); byId('results').hidden = value || !report; byId('result-loading').hidden = !value;
  byId('results-title').closest('section').setAttribute('aria-busy', String(value));
}
function drawFiles() {
  byId('run-count').textContent = `${files.length} / ${MAX_FILES}`;
  const list = byId('files'), overrides = byId('commit-overrides'); list.replaceChildren(); overrides.replaceChildren();
  for (const [index, file] of files.entries()) {
    const row = element('div', undefined, 'file-row');
    const name = element('span', file.name, 'file-name'); name.title = file.name;
    row.append(name, element('span', `${Math.ceil(file.size / 1024)} KB`, 'file-size'));
    const remove = element('button', '×', 'remove'); remove.type = 'button'; remove.disabled = busy; remove.setAttribute('aria-label', `Remove ${file.name}`);
    remove.addEventListener('click', () => { files.splice(index, 1); isSample = false; drawFiles(); clearResults(); error(''); });
    row.append(remove); list.append(row);
    const override = element('div', undefined, 'commit-override');
    const label = element('label', file.name); const id = `commit-${index}`; label.htmlFor = id; label.title = file.name;
    const input = element('input'); input.id = id; input.type = 'text'; input.value = file.commit || ''; input.placeholder = 'Use default'; input.autocomplete = 'off'; input.spellcheck = false; input.maxLength = 64; input.disabled = busy;
    input.setAttribute('aria-label', `Commit override for ${file.name}`); input.addEventListener('input', () => { file.commit = input.value; if (report) clearResults(); });
    override.append(label, input); overrides.append(override);
  }
}
async function addFiles(incoming) {
  error('');
  if (busy) return;
  if (readToken) return error('Please wait for the current files to finish loading.');
  const incomingFiles = Array.from(incoming);
  if (files.length + incomingFiles.length > MAX_FILES) return error('Choose no more than 12 reports.');
  if (incomingFiles.some(file => file.size > MAX_FILE)) return error('Each report must be 512 KB or smaller.');
  if (files.reduce((n, f) => n + f.size, 0) + incomingFiles.reduce((n, f) => n + f.size, 0) > MAX_TOTAL) return error('Combined reports must be 2 MB or smaller.');
  const names = new Set(files.map(f => f.name));
  for (const file of incomingFiles) {
    if (!file.name.toLowerCase().endsWith('.xml')) return error('Choose JUnit XML files ending in .xml.');
    if (names.has(file.name)) return error(`Report names must be unique: ${file.name}`);
    names.add(file.name);
  }
  const token = Symbol('file-read'); readToken = token;
  try {
    const additions = await Promise.all(incomingFiles.map(async file => ({name: file.name, size: file.size, xml: await file.text(), commit: ''})));
    if (readToken !== token) return;
    if (additions.some(file => encoder.encode(file.xml).length > MAX_FILE)) return error('Each report must be 512 KB or smaller when decoded as text.');
    files.push(...additions); isSample = false; drawFiles(); clearResults();
  } catch { if (readToken === token) error('We could not read those files. Please try again.'); }
  finally { if (readToken === token) readToken = null; }
}
function reset() {
  if (activeRequest) activeRequest.abort(); activeRequest = null; readToken = null;
  files = []; isSample = false; byId('file-input').value = ''; byId('commit').value = ''; byId('search').value = ''; byId('filter').value = 'all';
  error(''); clearResults(); setBusy(false); drawFiles();
}
async function loadSample() {
  if (busy) return;
  readToken = null; error('');
  const controller = new AbortController(); activeRequest = controller; setBusy(true);
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, REQUEST_TIMEOUT);
  try {
    const responses = await Promise.all(['/samples/pass.xml', '/samples/fail.xml'].map(url => fetch(url, {signal:controller.signal})));
    if (responses.some(response => !response.ok)) throw new Error('Samples are unavailable. Try again or upload your own reports.');
    const xml = await Promise.all(responses.map(response => response.text()));
    if (controller.signal.aborted && timedOut) throw new Error('Sample request timed out.');
    if (activeRequest !== controller || controller.signal.aborted) return;
    files = xml.map((value, index) => ({name: index ? 'sample-fail.xml' : 'sample-pass.xml', size: encoder.encode(value).length, xml: value, commit: ''}));
    byId('commit').value = 'abcdef1234567'; isSample = true; drawFiles(); clearResults();
    clearTimeout(timer);
    await analyze();
  } catch (e) {
    if (activeRequest === controller && (e.name !== 'AbortError' || timedOut))
      error(timedOut ? 'Loading samples took too long. Please try again.' : e.message || 'Samples are unavailable. Please try again.');
  } finally {
    clearTimeout(timer);
    if (activeRequest === controller) { activeRequest = null; setBusy(false); }
  }
}
async function analyze() {
  error('');
  if (readToken) { error('Please wait for the current files to finish loading.'); return; }
  if (!files.length) { setBusy(false); error('Add at least one JUnit report. Two or more runs are needed to observe changes.'); return; }
  const commit = byId('commit').value.trim();
  const runs = files.map(file => ({name:file.name,commit:(file.commit.trim() || commit).toLowerCase(),xml:file.xml}));
  if (runs.some(run => !COMMIT.test(run.commit))) { setBusy(false); error('Enter a 7–64 character hexadecimal commit for every report.'); byId('commit').focus(); return; }
  if (runs.reduce((n, r) => n + encoder.encode(r.xml).length, 0) > MAX_TOTAL) { setBusy(false); error('Combined reports must be 2 MB or smaller.'); return; }
  const controller = new AbortController(); activeRequest = controller; setBusy(true);
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, REQUEST_TIMEOUT);
  try {
    const response = await fetch('/api/analyze', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({runs}), signal:controller.signal});
    const body = await response.json().catch(() => ({}));
    if (controller.signal.aborted && timedOut) throw new Error('Analysis request timed out.');
    if (!response.ok) throw new Error(typeof body.error === 'string' ? body.error : 'Analysis failed. Please try again.');
    if (activeRequest !== controller || controller.signal.aborted) return;
    if (!Array.isArray(body.tests) || !Array.isArray(body.runs) || !body.summary || !Array.isArray(body.warnings)) throw new Error('The service returned an invalid report. Please try again.');
    report = body; selectedId = body.tests[0]?.id || null; byId('search').value = ''; byId('filter').value = 'all'; renderReport();
    if (isSample) byId('results-title').scrollIntoView({behavior:'smooth',block:'start'});
  } catch (e) {
    if (activeRequest === controller && (e.name !== 'AbortError' || timedOut)) { report = null; error(timedOut ? 'Analysis took too long. Please try again.' : e.message || 'Could not reach the analysis service. Please try again.'); }
  } finally { clearTimeout(timer); if (activeRequest === controller) { activeRequest = null; setBusy(false); } }
}
function pill(classification) { return element('span', labels[classification] || classification, `pill ${classification}`); }
function renderReport() {
  byId('sample-flag').hidden = !isSample;
  byId('result-title').textContent = report.summary.mixed ? `${report.summary.mixed} ${report.summary.mixed === 1 ? 'test has' : 'tests have'} inconsistent outcomes` : 'Comparison complete';
  byId('result-subtitle').textContent = `${report.summary.runs} reports · ${report.summary.tests} test / commit groups`;
  const summary = byId('summary'); summary.replaceChildren();
  for (const [count, label, type] of [[report.summary.runs,'Reports',''],[report.summary.tests,'Test groups',''],[report.summary.mixed,'Inconsistent','attention'],[report.summary.insufficient,'Need more runs','']]) {
    const item = element('div', undefined, `summary-item ${type}`); item.append(element('strong',count),element('span',label)); summary.append(item);
  }
  const warnings = byId('warnings'); warnings.replaceChildren();
  for (const warning of report.warnings) warnings.append(element('p',warning));
  renderList(); renderDetails();
}
function renderList() {
  if (!report) return;
  const q = byId('search').value.trim().toLowerCase(), filter = byId('filter').value;
  const matches = report.tests.filter(test => (filter === 'all' || filter === test.classification) && `${test.class_name} ${test.name} ${test.commit}`.toLowerCase().includes(q));
  const list = byId('test-list'); list.replaceChildren();
  byId('no-results').hidden = matches.length !== 0; list.hidden = matches.length === 0;
  for (const test of matches) {
    const row = element('button', undefined, 'test-row'); row.type='button'; row.setAttribute('aria-pressed',String(test.id===selectedId));
    const label = element('div', undefined, 'test-label'); label.append(element('strong',test.name),element('span',`${test.class_name || 'No class'} · ${test.commit.slice(0,12)}`));
    row.append(label,pill(test.classification));
    row.addEventListener('click',() => {selectedId=test.id;renderList();renderDetails();byId('details').scrollIntoView({behavior:'smooth',block:'nearest'});});
    list.append(row);
  }
}
function renderDetails() {
  const test = report?.tests.find(t=>t.id===selectedId); byId('details').hidden = !test; if (!test) return;
  byId('detail-title').textContent=test.name; byId('detail-meta').textContent=`${test.class_name || 'No class'} · ${test.commit}`;
  byId('detail-explanation').textContent = test.classification === 'mixed' ? 'This test both passed and failed in reports labeled with this commit. Different environments or data could explain the difference.' : `${labels[test.classification] || test.classification}: ${test.pass_count} passed, ${test.fail_count} failed, ${test.skip_count} skipped. More runs may change the picture.`;
  const root=byId('observations'); root.replaceChildren();
  for (const obs of test.observations) {
    const row=element('div',undefined,'observation'); row.append(element('strong',obs.run),pill(obs.status==='fail'?'failed':obs.status==='pass'?'passed':'skipped'));
    if (obs.message) row.append(element('pre',obs.message)); root.append(row);
  }
  byId('copy-status').textContent='';
}
function markdownText(value) { return String(value).replace(/[\\`*_\[\]<>]/g,'\\$&').replace(/[\r\n]+/g,' ').slice(0,600); }
function issueDraft(test) {
  return [`## Test outcome evidence`,``,`**Outcome:** ${markdownText(labels[test.classification] || test.classification)}`,`**Test:** ${markdownText(test.class_name || '(no class)')} / ${markdownText(test.name)}`,`**Commit (user supplied):** ${markdownText(test.commit)}`,`**Observed:** ${test.pass_count} passed, ${test.fail_count} failed, ${test.skip_count} skipped`,``,`### Runs`,...test.observations.map(o=>`- ${markdownText(o.run)}: ${o.status}${o.message ? ` — ${markdownText(o.message)}` : ''}`),``,`### Follow-up`,`- Compare test environment, configuration and data across runs.`,`- Re-run on the same commit; investigate the observed failure.`,``,`These results are observations, not proof of root cause.`].join('\n');
}
function download(name, content, type) {
  const blob = new Blob([content],{type}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download=name; document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000);
}
byId('file-input').addEventListener('change',async e=>{await addFiles(e.target.files);e.target.value='';});
const zone=byId('drop-zone');
for (const type of ['dragenter','dragover']) zone.addEventListener(type,e=>{e.preventDefault();zone.classList.add('dragover');});
for (const type of ['dragleave','drop']) zone.addEventListener(type,e=>{e.preventDefault();zone.classList.remove('dragover');});
zone.addEventListener('drop',e=>addFiles(e.dataTransfer.files));
byId('commit').addEventListener('input',()=>{if(report) clearResults();});
byId('analyze').addEventListener('click',()=>analyze());
byId('reset').addEventListener('click',()=>reset());
byId('load-sample').addEventListener('click',()=>loadSample()); byId('load-sample-empty').addEventListener('click',()=>loadSample());
byId('search').addEventListener('input',renderList); byId('filter').addEventListener('change',renderList);
byId('export-json').addEventListener('click',()=>{if(report)download('flakewise-evidence.json',JSON.stringify(report,null,2),'application/json');});
byId('copy-issue').addEventListener('click',async()=>{const test=report?.tests.find(t=>t.id===selectedId);if(!test)return;const draft=issueDraft(test);try{await navigator.clipboard.writeText(draft);byId('copy-status').textContent='Issue draft copied. Review it before sharing.';}catch{download('flakewise-issue.md',draft,'text/markdown');byId('copy-status').textContent='Clipboard unavailable. Downloaded the issue draft instead.';}});
