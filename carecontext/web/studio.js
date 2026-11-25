// CareContext v0.3: fictional-document studio. Data stays in this browser tab's JS memory.
// No localStorage, indexedDB, telemetry, or remote font/CDN requests.
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { session: '', docs: [], turns: [], role: 'patient', mode: 'local', modelReady: false, lastTrace: [], currentSource: null, busy: false };
const MAX_DOCS = 4;
const SAMPLE_TEXT = `FICTIONAL / EDUCATIONAL RECORD — NOT A REAL PATIENT
Patient: Maya Chen (invented name; no real patient information)

2026-08-04 — Primary care follow-up note
Allergy section: No allergies documented during intake. The record did not confirm a complete allergy history.
Reason for visit: Coordination of a fictional wound-care follow-up appointment. Transportation support was being explored.
Medications listed: The synthetic source mentions an over-the-counter moisturizer and a historical prescription, without doses or treatment guidance.

2026-08-12 — Telephone review, fictional care coordination
Updated allergy section: Patient reported a past rash after penicillin. Nurse recorded the report and requested confirmation by the treating clinician.
Follow-up appointment: A visit was tentatively planned for 2026-08-19, pending scheduling confirmation.
Documented gap: Allergy reconciliation remains pending. The record does not show confirmation of a diagnosis or treatment plan.

2026-08-14 — Synthetic laboratory excerpt
Hemoglobin: 12.7 g/dL (recorded value; no validated reference range included in this fictional file).
Creatinine: 0.9 mg/dL (recorded value; no interpretation or clinical conclusion provided).
Documentation note: Values are from an author-written fictional example. Laboratory reference ranges and clinical context are intentionally omitted.

2026-08-18 — Care coordination update
Transportation assistance confirmed by case coordinator for the planned appointment. The appointment itself is still marked unconfirmed in the fictional record. The timeline does not establish whether the appointment occurred.`;
const rolePrompts = {
  patient: ['What allergy information is documented?', 'What follow-up plan is recorded?', 'Which lab values appear?'],
  clinician: ['Which source entries document allergy changes?', 'What follow-up status is recorded?', 'What values are documented by date?'],
  researcher: ['Which passages document a change over time?', 'What provenance supports the allergy history?', 'Where is evidence incomplete?']
};
let toastTimer;

function el(tag, className = '', text) {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (text !== undefined) n.textContent = String(text);
  return n;
}
function status(message) {
  const t = $('#toast'); t.textContent = message; t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 4500);
}
function sourceCount() { return state.docs.reduce((sum, d) => sum + d.passages.length, 0); }
function refreshCounters() {
  $('#doc-count').textContent = String(state.docs.length).padStart(2, '0');
  $('#passage-count').textContent = String(sourceCount()).padStart(2, '0');
  $('#turn-count').textContent = String(state.turns.filter(t => t.role === 'user').length).padStart(2, '0');
}
function syntheticConfirmed() {
  if ($('#synthetic-ack').checked) return true;
  status('Confirm that your documents contain fictional test data before proceeding.');
  $('#synthetic-ack').focus();
  return false;
}
function renderDocuments() {
  const holder = $('#document-list'); holder.replaceChildren();
  if (!state.docs.length) { holder.append(el('div', 'empty-documents', 'No files in memory yet. Your sample will appear here.')); refreshCounters(); return; }
  for (const doc of state.docs) {
    const row = el('div', 'file-entry');
    row.append(el('span', 'file-icon', '▤'));
    const copy = el('div','file-desc');
    copy.append(el('strong','',doc.name));
    copy.append(el('small','',`${doc.passage_count} excerpts · ${doc.pages} pages · ${doc.extraction}`));
    const remove = el('button','', '×'); remove.type='button'; remove.title=`Remove ${doc.name}`; remove.setAttribute('aria-label',`Remove ${doc.name}`);
    remove.addEventListener('click', () => { state.docs = state.docs.filter(d => d.sha256 !== doc.sha256); state.turns=[]; state.lastTrace=[]; clearInspector(); renderDocuments(); renderChat(); refreshCounters(); status(`${doc.name} removed from this browser tab.`); });
    row.append(copy,remove); holder.append(row);
  }
  refreshCounters();
}
function roleChanged(role, announce = true) {
  if (!rolePrompts[role]) return;
  state.role = role;
  $$('input[name="role"]').forEach(input => { input.checked = input.value === role; input.closest('label').classList.toggle('selected', input.checked); });
  $('#mobile-role').value = role;
  $('#role-label').textContent = ({patient:'PATIENT',clinician:'CLINICIAN',researcher:'RESEARCHER'}[role]) + ' PERSPECTIVE';
  const list = $('#suggestion-list'); list.replaceChildren();
  for (const text of rolePrompts[role]) {
    const b = el('button','',`${text} ↗`); b.type='button'; b.addEventListener('click',()=>{ $('#question-input').value=text; $('#question-input').focus(); }); list.append(b);
  }
  if (announce) status(`Perspective changed to ${role}. This changes wording, not permissions or clinical validity.`);
}
function setMode(mode) {
  if (mode === 'model' && !state.modelReady) { status('Optional AI explanations require a server-side provider key. Using local evidence retrieval.'); return; }
  state.mode=mode;
  $$('.mode-choice').forEach(btn => { const active = btn.dataset.mode === mode; btn.classList.toggle('selected',active); btn.setAttribute('aria-pressed',String(active)); });
  $('#model-status').textContent = mode==='model' ? 'AI DRAFT / CITED' : 'LOCAL / NO MODEL';
}
async function parseOne(file) {
  if (!syntheticConfirmed()) return;
  if (state.docs.length>=MAX_DOCS) { status('This research preview allows four documents per session.'); return; }
  if (!file || file.size > 3*1024*1024) { status('Select a document smaller than 3 MB.'); return; }
  if (!/\.(pdf|docx|txt|md|png|jpe?g)$/i.test(file.name)) { status('Unsupported format. Use PDF, DOCX, TXT, MD, PNG or JPG.'); return; }
  if (!state.session) { status('Not connected to the local service.'); return; }
  state.busy=true; $('#load-sample').disabled=true;
  const drop = $('#dropzone'); drop.setAttribute('aria-busy','true');
  try {
    const res=await fetch('/api/studio/ingest?name='+encodeURIComponent(file.name),{method:'POST',headers:{'X-CareContext-Session':state.session,'Content-Type':'application/octet-stream'},body:file});
    const data=await res.json(); if (!res.ok) throw new Error(data.detail || 'Document extraction failed.');
    if (state.docs.some(d=>d.sha256===data.sha256)) throw new Error('This file is already loaded.');
    state.docs.push(data); state.turns=[]; state.lastTrace=[]; clearInspector(); renderDocuments(); renderChat();
    status(`Extracted ${data.passage_count} inspectable passages from ${data.name}.`);
  } catch(error) { status(error.message || 'Unable to process the document.'); }
  finally { state.busy=false; $('#load-sample').disabled=false; drop.setAttribute('aria-busy','false'); $('#upload-input').value=''; }
}
function removeAll() {
  state.docs=[]; state.turns=[]; state.lastTrace=[]; state.currentSource=null;
  $('#question-input').value=''; renderDocuments();renderChat();clearInspector();status('Fictional document text and conversation cleared from this tab.');
}
function citationsFor(turn) {
  const group=el('div','citation-buttons');
  turn.citations.forEach((cit,i)=>{
    const b=el('button','',`[${i+1}] ${cit.source_name} · p.${cit.page}`);
    b.type='button'; b.addEventListener('click',()=>{showSource(cit); document.getElementById('inspector').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});
    group.append(b);
  });return group;
}
function renderChat() {
  const host=$('#chat-log'); const welcome=$('.assistant-welcome'); host.replaceChildren();
  if (!state.turns.length) { if (welcome) host.append(welcome); else host.append(makeWelcome()); refreshCounters(); return; }
  for(const turn of state.turns){
    const wrapper=el('div','chat-turn '+turn.role); const isUser=turn.role==='user';
    wrapper.append(el('span','turn-label',isUser?'YOU / QUESTION':turn.mode==='model'?'CARECTXT / AI GENERATED DRAFT':'CARECTXT / EVIDENCE RETRIEVAL'));
    wrapper.append(el('div','turn-bubble',turn.text));
    if(!isUser){const meta=el('div','turn-meta');meta.append(el('span','status-label',turn.status.toUpperCase().replaceAll('_',' ')));meta.append(el('span','',turn.mode==='model'?'LLM / NOT CLINICALLY VALIDATED':'BM25 / NO GENERATION'));wrapper.append(meta);
      if(turn.citations?.length)wrapper.append(citationsFor(turn));
      if(turn.uncertainty)wrapper.append(el('p','uncertainty',turn.uncertainty));
    }
    host.append(wrapper);
  }
  host.scrollTop=host.scrollHeight; refreshCounters();
}
function makeWelcome(){const d=el('div','assistant-welcome');d.append(el('div','welcome-logo','C↗'),el('h4','','Start with a question. Finish with a source.'),el('p','','Load a fictional document to see exact, attributed excerpts.'));return d;}
function renderTrace(list) {
  const host=$('#trace-list');host.replaceChildren();
  if(!list.length){host.append(el('div','trace-empty','No retrieval matches for this question.'));return;}
  const all=state.docs.flatMap(d=>d.passages);
  for(const trace of list){const match=all.find(d=>d.source_id===trace.source_id);if(!match)continue;
    const row=el('div','trace-item');row.setAttribute('role','button');row.tabIndex=0;
    row.append(el('strong','',trace.source_id));
    const desc=el('div');desc.append(el('span','',`SCORE ${Number(trace.score).toFixed(3)}`));desc.append(el('small','',trace.matched_terms.join(', ')||'No terms'));row.append(desc);
    const activate=()=>showSource(match);row.addEventListener('click',activate);row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});host.append(row);
  }
}
function showSource(source){state.currentSource=source;$('#reader-id').textContent=source.source_id;const host=$('#source-display');host.replaceChildren();host.append(el('span','source-meta',`SOURCE ${source.source_id} · PAGE ${source.page}`),el('h3','source-name',source.source_name),el('div','quoted-source',source.text),el('div','source-footer','EXCERPT FROM USER-SUPPLIED FICTIONAL DOCUMENT · VERIFY AGAINST ORIGINAL FILE'));}
function clearInspector(){state.currentSource=null;$('#reader-id').textContent='NO SELECTION';$('#source-display').replaceChildren(el('div','source-empty','Select a source citation from the conversation to inspect its exact text.'));$('#trace-list').replaceChildren(el('div','trace-empty','Run a document question to see ranked evidence.'));}
async function submitQuestion(event){event.preventDefault();if(state.busy)return;
  if(!syntheticConfirmed())return;
  if(!state.docs.length){status('Load a fictional document first.');document.getElementById('documents').scrollIntoView();return;}
  const input=$('#question-input');const question=input.value.trim();if(question.length<3){status('Enter a question of at least three characters.');return;}
  if(!state.session){status('Connection unavailable.');return;}
  const previous=state.turns.slice(-6).map(t=>({role:t.role,text:t.text.slice(0,1000)}));
  state.busy=true;$('#send-button').disabled=true;input.value='';
  state.turns.push({role:'user',text:question});renderChat();
  try {
    const res=await fetch('/api/studio/answer',{method:'POST',headers:{'Content-Type':'application/json','X-CareContext-Session':state.session},body:JSON.stringify({question,role:state.role,mode:state.mode,synthetic_ack:true,snippets:state.docs.flatMap(d=>d.passages),history:previous})});
    const data=await res.json();if(!res.ok)throw new Error(data.detail||'Evidence service failed.');
    state.turns.push({role:'assistant',text:data.answer,mode:data.mode,status:data.status,uncertainty:data.uncertainty,citations:data.citations});
    state.lastTrace=data.retrieval;renderTrace(data.retrieval);if(data.citations.length)showSource(data.citations[0]);renderChat();
  } catch(error){state.turns.push({role:'assistant',text:'The evidence request could not complete. No conclusion was produced.',mode:'local',status:'error',uncertainty:error.message||'',citations:[]});renderChat();status(error.message||'Service error.');}
  finally{state.busy=false;$('#send-button').disabled=false;}
}
function exportSession(){const data={product:'CareContext Studio',version:'0.3',scope:'fictional test documents only',role:state.role,mode:state.mode,documents:state.docs.map(d=>({name:d.name,sha256:d.sha256,pages:d.pages,passages:d.passages})),turns:state.turns};
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=el('a');a.href=url;a.download='carecontext-v03-fictional-session.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),0);status('Fictional session exported locally.');}
async function start(){
  try {const [session,caps]=await Promise.all([fetch('/api/config'),fetch('/api/studio/config')]);if(!session.ok||!caps.ok)throw new Error('Service unavailable.');const conf=await session.json(), cap=await caps.json();state.session=conf.session;state.modelReady=cap.model_enabled;
    const model=$('.mode-choice[data-mode="model"]');model.disabled=!state.modelReady;model.querySelector('small').textContent=state.modelReady?'Server model available':'Requires server credentials';
    $('.online-indicator').lastChild.textContent=' LOCAL SERVICE';
  } catch(error){$('.online-indicator').lastChild.textContent=' SERVICE OFFLINE';status('Run the FastAPI service locally to process fictional documents.');}
  renderDocuments();roleChanged('patient', false);setMode('local');
  $$('input[name="role"]').forEach(node=>node.addEventListener('change',()=>roleChanged(node.value)));
  $('#mobile-role').addEventListener('change',e=>roleChanged(e.target.value));
  $$('.mode-choice').forEach(node=>node.addEventListener('click',()=>setMode(node.dataset.mode)));
  $('#load-sample').addEventListener('click',()=>{const file=new File([SAMPLE_TEXT],'fictional-care-note.txt',{type:'text/plain'});parseOne(file);});
  $('#upload-input').addEventListener('change',async e=>{for(const f of [...e.target.files].slice(0,MAX_DOCS)){await parseOne(f);}});
  const drop=$('#dropzone');['dragenter','dragover'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('dragover');}));
  ['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('dragover');}));
  drop.addEventListener('drop',async e=>{for(const f of [...(e.dataTransfer?.files||[])].slice(0,MAX_DOCS)){await parseOne(f);}});
  $('#question-form').addEventListener('submit',submitQuestion);
  $('#question-input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('#question-form').requestSubmit();}});
  $('#clear-session').addEventListener('click',removeAll);$('#export-session').addEventListener('click',exportSession);
  const navToggle=$('#nav-toggle');
  navToggle?.addEventListener('click',()=>{const open=navToggle.getAttribute('aria-expanded')!=='true';navToggle.setAttribute('aria-expanded',String(open));navToggle.setAttribute('aria-label',open?'Close navigation':'Open navigation');$('#primary-links').classList.toggle('is-open',open);});
  $$('.side-link').forEach(link=>link.addEventListener('click',()=>{$$('.side-link').forEach(x=>x.classList.remove('active'));link.classList.add('active');$('#primary-links').classList.remove('is-open');navToggle?.setAttribute('aria-expanded','false');navToggle?.setAttribute('aria-label','Open navigation');}));
  $$('.suggestion-list button').forEach(b=>b.addEventListener('click',()=>{$('#question-input').value=b.dataset.prompt;$('#question-input').focus();}));
}
start();
