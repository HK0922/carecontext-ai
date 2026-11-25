import {escapeHtml as esc,formatDate,groupSources,assertQuestion,statusLabel} from './utils.js';

const $=id=>document.getElementById(id);
const state={patients:[],patient:null,sources:[],answer:null,session:null,generation:0,queryController:null};
let toastTimer;
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,3800);}
function error(message){$('global-alert').textContent=message;$('global-alert').hidden=false;}
async function api(path,options={}){
  const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',...(state.session?{'X-CareContext-Session':state.session}:{}),...options.headers}});
  if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:`Request failed (${response.status}). Check the input and try again.`);}
  return response.json();
}
function view(name){document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!=='view-'+name);document.querySelectorAll('.nav-item').forEach(el=>{el.classList.toggle('active',el.dataset.view===name);el.setAttribute('aria-current',el.dataset.view===name?'page':'false');});}
document.querySelectorAll('[data-view]').forEach(el=>el.addEventListener('click',()=>view(el.dataset.view)));
document.querySelectorAll('[data-close]').forEach(el=>el.addEventListener('click',()=>$(el.dataset.close).close()));
function renderCases(){
  const search=$('case-search').value.toLowerCase();
  const cases=state.patients.filter(p=>(p.name+' '+p.label).toLowerCase().includes(search));
  $('case-list').innerHTML=cases.length?cases.map(p=>`<button class="case-button ${state.patient?.id===p.id?'active':''}" data-patient="${esc(p.id)}" aria-pressed="${state.patient?.id===p.id}"><span class="avatar ${esc(p.color)}">${esc(p.initials)}</span><span><strong>${esc(p.name)}</strong><small>${esc(p.label)}</small></span><span class="case-arrow" aria-hidden="true">›</span></button>`).join(''):'<p class="small muted">No matching cases.</p>';
}
$('case-search').addEventListener('input',renderCases);
$('case-list').addEventListener('click',e=>{const b=e.target.closest('[data-patient]');if(b)selectPatient(b.dataset.patient).catch(e=>error(e.message));});
async function selectPatient(id){
  const gen=++state.generation;
  state.queryController?.abort();
  state.patient=state.patients.find(p=>p.id===id);state.answer=null;state.sources=[];
  $('ask-button').disabled=true;$('answer-panel').setAttribute('aria-busy','false');
  $('review-panel').hidden=true;$('review-note').value='';$('review-status').textContent='';$('global-alert').hidden=true;
  $('question').value='';$('as-of').value='';$('include-reference').checked=false;
  $('answer-content').innerHTML='<div class="empty-state"><div class="empty-symbol">↗</div><h3>Every statement needs a source.</h3><p>Choose a suggested question or ask your own. Supporting passages will appear here with dated citations.</p></div>';
  renderCases();view('workspace');
  $('patient-name').textContent=state.patient.name;$('patient-description').textContent=`${state.patient.age} years · ${state.patient.label} · Synthetic case`;
  $('patient-avatar').textContent=state.patient.initials;$('patient-avatar').className='avatar large '+state.patient.color;
  $('patient-updated').textContent=formatDate(state.patient.updated);
  $('suggestions').innerHTML=state.patient.questions.map(q=>`<button class="suggestion" data-question="${esc(q)}">${esc(q)}</button>`).join('');
  $('timeline').innerHTML='<p class="small muted">Loading timeline…</p>';$('history').innerHTML='';
  const [patient,sources]=await Promise.all([api('/patients/'+id),api('/sources?patient_id='+id+'&include_reference=true')]);
  if(gen!==state.generation)return;
  state.patient=patient;state.sources=sources;
  $('patient-docs').textContent=String(patient.timeline.length).padStart(2,'0');
  $('timeline').innerHTML=patient.timeline.map(d=>`<div class="timeline-item"><time datetime="${esc(d.date)}">${formatDate(d.date)}</time><button class="text-button" data-document="${esc(d.id)}">${esc(d.title)} <span aria-hidden="true">↗</span></button><p>${esc(d.author.replace('Synthetic ',''))}</p></div>`).join('');
  $('ask-button').disabled=false;$('ask-button').innerHTML='Find evidence <span aria-hidden="true">↗</span>';
  await history(gen);
}
async function history(gen=state.generation){
  const items=await api('/history/'+state.patient.id);if(gen!==state.generation)return;
  $('history').innerHTML=items.length?items.slice(0,7).map(r=>`<button class="history-item" data-run="${esc(r.id)}">${esc(r.question)}<small>${esc(r.review?.decision==='reviewed'?'Reviewed':r.review?.decision==='needs_followup'?'Needs follow-up':statusLabel(r.status))} · ${formatDate(r.created_at)}</small></button>`).join(''):'<p class="small muted">No saved questions yet.</p>';
}
$('suggestions').addEventListener('click',e=>{const b=e.target.closest('[data-question]');if(b&&!$('ask-button').disabled){$('question').value=b.dataset.question;$('query-form').requestSubmit();}});
$('query-form').addEventListener('submit',async e=>{
  e.preventDefault();if(!state.patient||$('ask-button').disabled)return;
  const gen=state.generation;
  try{
    const question=assertQuestion($('question').value);$('global-alert').hidden=true;$('ask-button').disabled=true;
    $('answer-panel').setAttribute('aria-busy','true');$('review-panel').hidden=true;
    $('answer-content').innerHTML='<div class="loading"><span class="spinner"></span>Reading the selected sources…</div>';
    state.queryController=new AbortController();
    const answer=await api('/query',{method:'POST',signal:state.queryController.signal,body:JSON.stringify({patient_id:state.patient.id,question,mode:$('mode').value,include_reference:$('include-reference').checked,as_of:$('as-of').value||null})});
    if(gen!==state.generation)return;renderAnswer(answer);await history(gen);
  }catch(err){if(err.name==='AbortError')return;if(gen===state.generation){error(err.message);$('answer-content').innerHTML='<div class="empty-state"><h3>The request could not finish.</h3><p>Your sources are still available. Check the message above and retry.</p></div>';}}
  finally{if(gen===state.generation){$('ask-button').disabled=false;$('answer-panel').setAttribute('aria-busy','false');}}
});
function renderAnswer(answer){
  state.answer=answer;
  $('answer-content').innerHTML=`<div class="brief-meta"><span class="pill ${answer.status==='evidence_found'?'':'amber'}">${esc(statusLabel(answer.status))}</span><span class="small muted">${answer.evidence.length} excerpts · ${answer.mode==='local'?'Local retrieval':'Model selection'} · ${Math.round(answer.elapsed_ms)} ms</span></div><p class="brief-question">${esc(answer.question)}</p><p class="brief-summary">${esc(answer.summary)}</p>${answer.as_of?`<p class="small muted">Evidence cutoff: ${formatDate(answer.as_of)}</p>`:''}${answer.evidence.map(s=>`<article class="excerpt"><p>${esc(s.text)} <button class="citation" data-source="${esc(s.id)}" aria-label="View source ${s.citation}">${s.citation}</button></p><div class="excerpt-source"><button class="text-button" data-source="${esc(s.id)}">${esc(s.title)} ↗</button><span>· ${formatDate(s.date)}${s.kind==='reference'?' · Workflow reference':''}</span></div></article>`).join('')}${answer.warnings.map(w=>`<div class="warning-box"><h3>Differing entries: ${esc(w.field)}</h3><p>${esc(w.message)}</p><details><summary>Compare dated values</summary>${[w.latest,...w.previous].map(p=>`<p><button class="text-button" data-source="${esc(p.id)}">${formatDate(p.date)} ↗</button> · ${esc(p.text)}</p>`).join('')}</details></div>`).join('')}<div class="proof-footer"><span aria-hidden="true">◈</span>${answer.evidence.length?'All displayed excerpts match their source text.':'No unsupported answer was generated.'} Source matching does not verify clinical truth.</div>`;
  $('review-panel').hidden=false;$('review-note').value=answer.review?.note||'';
  $('review-status').textContent=answer.review?`Saved: ${answer.review.decision==='reviewed'?'reviewed':'needs follow-up'}.`:'Review notes remain separate from source evidence.';
}
$('history').addEventListener('click',async e=>{const b=e.target.closest('[data-run]');if(!b)return;const gen=state.generation;try{const r=await api('/runs/'+b.dataset.run);if(gen!==state.generation)return;renderAnswer(r);$('question').value=r.question;$('mode').value=r.mode;$('as-of').value=r.as_of||'';$('include-reference').checked=r.include_reference;}catch(err){error(err.message);}});
$('clear-history').addEventListener('click',async()=>{if(!state.patient||!confirm('Delete saved questions and review notes for this synthetic case? Source records will remain.'))return;const gen=state.generation;try{await api('/history/'+state.patient.id,{method:'DELETE'});if(gen!==state.generation)return;state.answer=null;$('review-panel').hidden=true;$('answer-content').innerHTML='<div class="empty-state"><h3>Review history cleared.</h3><p>Ask a new question to create an evidence brief.</p></div>';await history(gen);toast('Case review history deleted.');}catch(err){error(err.message);}});
async function saveReview(decision){if(!state.answer)return;const gen=state.generation;const runId=state.answer.id;const buttons=[$('save-review'),$('flag-review')];buttons.forEach(b=>b.disabled=true);try{const r=await api('/runs/'+runId+'/review',{method:'POST',body:JSON.stringify({decision,note:$('review-note').value})});if(gen!==state.generation||runId!==state.answer?.id)return;state.answer.review=r;$('review-status').textContent=`Saved: ${decision==='reviewed'?'reviewed':'needs follow-up'}.`;await history(gen);toast('Review saved locally.');}catch(err){error(err.message);}finally{buttons.forEach(b=>b.disabled=false);}}
$('save-review').addEventListener('click',()=>saveReview('reviewed'));$('flag-review').addEventListener('click',()=>saveReview('needs_followup'));
$('export-review').addEventListener('click',()=>{if(state.answer){const a=document.createElement('a');a.href='/api/runs/'+state.answer.id+'/export';a.download='carecontext-review.md';document.body.append(a);a.click();a.remove();}});
function openSources(sourceId=null,docId=null){
  const selected=state.sources.find(s=>s.id===sourceId);if(selected)docId=selected.document_id;
  const groups=groupSources(state.sources).filter(d=>!docId||d.document_id===docId);
  $('source-dialog-title').textContent=docId?groups[0]?.title||'Original record':'Sources for '+state.patient.name;
  $('source-detail').innerHTML='<p class="source-note">All records and reference documents are fictional. Workflow references are not medical guidelines.</p>'+groups.map(d=>`<article class="source-document"><h3>${esc(d.title)}</h3><p class="source-note">${formatDate(d.date)} · ${d.kind==='record'?'Synthetic patient record':'Fictional workflow reference'} · ${esc(d.document_id)}</p>${d.entries.map(p=>`<section class="source-passage ${p.id===sourceId?'selected':''}"><code>${esc(p.id)}</code><p>${esc(p.text)}</p></section>`).join('')}</article>`).join('');
  $('source-dialog').showModal();
}
$('browse-sources').addEventListener('click',()=>{if(state.sources.length)openSources();});
$('timeline').addEventListener('click',e=>{const b=e.target.closest('[data-document]');if(b)openSources(null,b.dataset.document);});
$('answer-content').addEventListener('click',e=>{const b=e.target.closest('[data-source]');if(b)openSources(b.dataset.source);});
$('open-verifier').addEventListener('click',()=>{if(!state.sources.length)return;$('verify-source').innerHTML=state.sources.map(s=>`<option value="${esc(s.id)}">${esc(s.id)} · ${esc(s.title)}</option>`).join('');$('verify-text').value=state.sources[0].text;$('verify-result').innerHTML='';$('verify-dialog').showModal();});
$('verify-source').addEventListener('change',()=>{$('verify-text').value=state.sources.find(s=>s.id===$('verify-source').value)?.text||'';$('verify-result').innerHTML='';});
$('verify-form').addEventListener('submit',async e=>{e.preventDefault();const button=e.submitter;button.disabled=true;try{const r=await api('/verify',{method:'POST',body:JSON.stringify({patient_id:state.patient.id,claims:[{source_id:$('verify-source').value,text:$('verify-text').value}]})});const result=r.results[0];$('verify-result').innerHTML=`<div class="alert ${result.verdict==='source_match'?'success':'error'}"><strong>${result.verdict==='source_match'?'Exact source match':'Requires review'}</strong><br>${esc(result.reason)}</div>`;}catch(err){$('verify-result').textContent=err.message;}finally{button.disabled=false;}});
$('run-evaluation').addEventListener('click',async()=>{const b=$('run-evaluation');b.disabled=true;$('eval-output').innerHTML='<p class="loading"><span class="spinner"></span>Running labeled cases…</p>';try{const r=await api('/evaluations',{method:'POST'});const s=r.summary;$('eval-output').innerHTML=`<div class="metric-grid"><div class="metric"><strong>${s.passed}/${s.total}</strong><span>Fixture checks passed</span></div><div class="metric"><strong>${Math.round(s.retrieval_recall_at_6*100)}%</strong><span>Expected-source recall @ 6</span></div><div class="metric"><strong>${s.cross_case_leaks}</strong><span>Cross-case passages returned</span></div></div><p class="small muted">${esc(r.limitations)} Evaluation mode: local. Corpus: ${esc(r.corpus_sha256.slice(0,12))}…</p><div class="table-wrap"><table><thead><tr><th>Case</th><th>Question / check</th><th>Outcome</th><th>Result</th></tr></thead><tbody>${r.results.map(t=>`<tr><td>${esc(t.category)}</td><td>${esc(t.question)}</td><td>${esc(t.actual_status)}</td><td><span class="pill ${t.passed?'':'amber'}">${t.passed?'PASS':'FAIL'}</span></td></tr>`).join('')}</tbody></table></div>`;}catch(err){$('eval-output').innerHTML=`<div class="alert error">${esc(err.message)}</div>`;}finally{b.disabled=false;}});
async function init(){try{const [config,patients]=await Promise.all([api('/config'),api('/patients')]);state.session=config.session;state.patients=patients;$('case-count').textContent=patients.length;$('connection').textContent='Local service connected';if(config.model_enabled){$('mode').options[1].disabled=false;$('mode').options[1].textContent='Model-assisted selection';}await selectPatient(patients[0].id);view('literature');}catch(err){error('Could not connect to CareContext. Start the local server and reload. '+err.message);$('connection').textContent='Service unavailable';}}
init();
