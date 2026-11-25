// CareContext Research Lab: de-identified local-only document extraction.
// No storage, analytics, remote fonts, or executable HTML injection.
const $ = (id) => document.getElementById(id);
const state = {session: null, config: null, file: null, analysis: null, source: null, busy:false, lastAnalyzedFile:null};
const SAMPLE = `RESEARCH EXAMPLE — FULLY SYNTHETIC; NO PATIENT DATA
Medication: Metformin 500 mg tablet - Take 1 tablet by mouth twice daily for 30 days.
Medication: Amoxicillin 250 mg capsule - Take 1 capsule by mouth three times daily for 7 days.
Symptoms: denies cough.
Glucose: 90 mg/dL
Indication: Educational example; not a diagnosis.
`;
const el = (tag, className, text) => { const n = document.createElement(tag); if(className)n.className=className; if(text !== undefined)n.textContent=String(text); return n; };
function notify(msg, good=false){const n=$('notice');n.textContent=msg;n.classList.toggle('good',good);}
function resetResults(){
  state.analysis=null; state.source=null; state.lastAnalyzedFile=null;
  $('results').hidden=true; $('results-empty').hidden=false; $('view-results').hidden=true;
  $('record-kind-note').hidden=true; $('record-kind-note').textContent='';
  $('source-text').textContent='Select an extracted field to view the exact cited text.';
  $('source-meta').textContent='PAGE — · OFFSETS — · NO CONFIDENCE CLAIM';
  $('selected-id').textContent='NO SOURCE SELECTED';
  $('reference-output').textContent='Select a medication and choose “Check NLM references.”';
  for(const id of ['document-meta','review-flags','meds','symptoms','labs','context'])$(id).replaceChildren();
  $('analyze-label').textContent='Extract fields';
}
function clear(){
  if(state.busy)return;
  resetResults();state.file=null;$('research-file').value='';
  $('file-name').textContent='No document selected.';$('privacy-attest').checked=false;
  notify('Research workspace cleared from this browser tab.',true);
}
function showResults(){
  const results=$('results'); if(results.hidden)return;
  results.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  $('results-heading').focus({preventScroll:true});
}
function selectSource(source){state.source=source;$('source-text').textContent=source.text;$('source-meta').textContent=`PAGE ${source.page} · CHARACTERS ${source.start}–${source.end} · OCR CONFIDENCE NOT AVAILABLE`;$('selected-id').textContent=source.source_id; document.getElementById('sources').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});}
function entityCard(primary,details,source,medicationName,extraSources=[]){
  const card=el('article','entity');card.append(el('strong','',primary));
  const kv=el('div','kv');for(const item of details){if(item)kv.append(el('span','',item));}card.append(kv);
  const btns=el('div','mini-buttons');
  const srcBtn=el('button','','Inspect exact source ↗');srcBtn.type='button';srcBtn.addEventListener('click',()=>selectSource(source));btns.append(srcBtn);
  for(const [caption,linkedSource] of extraSources){if(!linkedSource)continue;const btn=el('button','',caption);btn.type='button';btn.addEventListener('click',()=>selectSource(linkedSource));btns.append(btn);}
  if(medicationName){const reference=el('button','','Check NLM references ↗');reference.type='button';reference.addEventListener('click',()=>lookup(medicationName));btns.append(reference);}
  card.append(btns);return card;
}
const WARNING_LABELS={
  complex_or_weight_based_instruction_requires_review:'Nonstandard administration directions — manual review needed',
  frequency_missing:'Frequency not documented',
  dose_missing:'Administration dose not documented',
  administration_instructions_not_in_source:'Administration directions not present in this history',
  possible_combination_product_requires_review:'Additional ingredient may be present — inspect the full product description',
};
function medicationDetails(m){
  const details=[];
  const simulated=m.record_kind==='synthea_simulated_medication_history';
  if(m.ingredients?.length>1){
    for(const ingredient of m.ingredients) details.push(`${ingredient.name}: ${ingredient.strength.value} ${ingredient.strength.unit}`);
  }else if(m.strength){details.push(`Product ${m.strength.unit.includes('/')?'concentration':'strength'}: ${m.strength.value} ${m.strength.unit}`);}
  else{details.push('Product strength not identified');}
  if(m.package_volume)details.push(`Device volume: ${m.package_volume.value} ${m.package_volume.unit} (not an administered dose)`);
  if(m.product_form)details.push(`Dosage form: ${m.product_form}`);
  if(m.route)details.push(m.route_basis==='product_form'?`Form-associated route: ${m.route}`:`Route stated: ${m.route}`);
  if(m.dose)details.push(`Administration instruction: ${m.dose.raw}`);
  if(m.frequency)details.push(`Frequency stated: ${m.frequency}`);
  if(m.duration)details.push(`Duration stated: ${m.duration}`);
  if(simulated && !m.dose && !m.frequency)details.push('Administration directions not recorded in source');
  if(m.recorded_start)details.push(`Simulated record start: ${m.recorded_start.slice(0,10)}`);
  if(m.recorded_reason)details.push(`Reason in simulation: ${m.recorded_reason} (not independently verified)`);
  for(const code of m.warnings||[]){
    if(simulated && code==='administration_instructions_not_in_source')continue;
    const readable=WARNING_LABELS[code]||'Additional source review required';
    if(!details.includes(readable))details.push(readable);
  }
  return details;
}
function fill(list,items,make){const host=$(list);host.replaceChildren();if(!items.length){host.append(el('p','no-match','No confident field candidates identified. This is not proof that the document contains none.'));return;}for(const item of items){host.append(make(item));}}
function render(data){state.analysis=data;$('results-empty').hidden=true;$('results').hidden=false;const d=data.document;$('document-meta').textContent=`${d.name} · ${d.pages} page(s) · SHA-256 ${d.sha256.slice(0,15)}… · ${d.extraction} · ALL FIELDS REQUIRE REVIEW`;
  const simulated=d.kind==='synthea_simulated_medication_history';
  $('record-kind-note').hidden=!simulated;
  $('record-kind-note').textContent=simulated?'Synthea simulated medication history — not an original prescription. Product strength and dosage form do not establish the amount administered, the frequency, or the patient’s clinical diagnosis. Repeated entries are retained by recorded date.':'';
  $('review-flags').textContent=data.review_flags.length?data.review_flags.map(x=>x.note).join(' / '):'No unparsed lines flagged. Every extracted field still requires manual source review.';
  fill('meds',data.medications,m=>entityCard(m.raw_name,medicationDetails(m),m.source,m.raw_name,[
    ['Inspect recorded date ↗',m.recorded_start_source],
    ['Inspect simulated reason ↗',m.recorded_reason_source],
  ]));
  fill('symptoms',data.symptoms,s=>entityCard(s.raw_text,[s.negated?'NEGATED STATEMENT':'Documented statement',s.temporality],s.source));
  fill('labs',data.labs,l=>entityCard(l.name, [`${l.value} ${l.unit||'(unit not given)'}`,'Not clinically interpreted'],l.source));
  fill('context',data.explicit_context,c=>entityCard(c.text,['Explicitly written in source','Not independently diagnosed'],c.source));
  const all=[...data.medications,...data.symptoms,...data.labs,...data.explicit_context];if(all.length) selectSourceInPlace(all[0].source);
}
function selectSourceInPlace(source){state.source=source;$('source-text').textContent=source.text;$('source-meta').textContent=`PAGE ${source.page} · CHARACTERS ${source.start}–${source.end} · NO MEDICAL ACCURACY CLAIM`;$('selected-id').textContent=source.source_id;}
async function analyze(){
  if(state.busy)return;
  if(!state.config?.enabled){notify('Local research intake is disabled. See the startup instructions to opt in.');return;}
  if(!$('privacy-attest').checked){notify('Please verify that the document is authorized and de-identified.');return;}
  if(!state.file){notify('Choose a document or load the sample first.');return;}
  if(!state.session){notify('Missing local session. Refresh after starting FastAPI.');return;}
  // Clicking again after a completed analysis navigates to the existing results.
  // It does not repeatedly re-upload an unchanged document.
  if(state.analysis && state.lastAnalyzedFile===state.file){
    notify('Already analyzed this document. Showing your existing results.',true);showResults();return;
  }
  const selectedFile=state.file;
  state.busy=true;$('analyze').disabled=true;$('research-file').disabled=true;$('sample').disabled=true;
  notify('Extracting text and identifying source-grounded candidates…');
  try{
    const r=await fetch('/api/research/analyze?name='+encodeURIComponent(selectedFile.name),{
      method:'POST',headers:{'X-CareContext-Session':state.session,'X-CareContext-Data-Class':'deidentified',
      'X-CareContext-Data-Use':'authorized','Content-Type':'application/octet-stream'},body:selectedFile});
    const data=await r.json();if(!r.ok)throw Error(data.detail||'Research analysis failed.');
    render(data);state.lastAnalyzedFile=selectedFile;
    $('view-results').hidden=false;$('analyze-label').textContent='View results';
    const n=data.medications.length, flagged=data.review_flags.filter(f=>f.code==='unparsed_medication_line').length;
    const count=`${n} medication candidate${n===1?'':'s'}, ${data.symptoms.length} symptom statement${data.symptoms.length===1?'':'s'}, ${data.labs.length} lab value${data.labs.length===1?'s':''}`;
    const warning=flagged?` ${flagged} medication-like line(s) need manual review.`:'';
    notify(`Analysis complete: ${count}. ${n?'':'No medications were confidently extracted; this does not mean none are present.'}${warning} Opening results below.`,true);
    // The results panel falls below the upload card on small screens.
    // Without moving focus the user may think the file did not load.
    window.requestAnimationFrame(showResults);
  }catch(e){notify(e.message||'Analysis failed.');}
  finally{$('analyze').disabled=false;$('research-file').disabled=false;$('sample').disabled=false;state.busy=false;}
}
async function lookup(name){if(state.config?.reference_network_enabled && !window.confirm(`Send ONLY the selected term “${name}” to NLM? Confirm it is a medication name and contains no identifying patient details.`))return;const host=$('reference-output');host.replaceChildren(el('span','','Checking available reference metadata…'));if(!state.session){host.textContent='Local service unavailable.';return;}try{const res=await fetch('/api/research/lookup',{method:'POST',headers:{'X-CareContext-Session':state.session,'X-CareContext-Term-Only':'1','X-CareContext-Term-Verified':'1','Content-Type':'application/json'},body:JSON.stringify({medication_name:name})});const d=await res.json();if(!res.ok)throw Error(d.detail||'Reference lookup failed.');host.replaceChildren();host.append(el('strong','',d.term));host.append(el('p','',d.notice));if(d.rxnorm){host.append(el('p','',`RxNorm ${d.rxnorm.status}; candidate RxCUIs: ${d.rxnorm.candidate_rxcuis.join(', ')||'none'}`));}else{host.append(el('p','','Reference network currently offline.'));}if(d.dailymed?.length){const list=el('div');for(const row of d.dailymed){const link=el('a','',row.label_title||'DailyMed drug label');link.href=row.source_url;link.target='_blank';link.rel='noopener noreferrer';list.append(link);}host.append(list);}else if(d.status!=='offline'){host.append(el('p','','No DailyMed labels confirmed.'));}}catch(e){host.textContent=e.message||'Reference service unavailable.';}}
function save(){if(!state.analysis)return;const body=JSON.stringify({...state.analysis,export_warning:'The extracted data are unverified and may contain sensitive details; store securely. Do not commit to GitHub.'},null,2);const blob=new Blob([body],{type:'application/json'});const url=URL.createObjectURL(blob);const a=el('a');a.href=url;a.download='carecontext-research-review.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('JSON downloaded to your computer. Review before sharing.',true);}
async function init(){const responses=await Promise.allSettled([fetch('/api/research/config'),fetch('/api/config')]);try{if(responses.some(r=>r.status!=='fulfilled'||!r.value.ok))throw Error('local server offline');state.config=await responses[0].value.json();state.session=(await responses[1].value.json()).session;$('top-status').textContent=state.config.enabled?'LOCAL RESEARCH / ENABLED':'LOCAL RESEARCH / DISABLED';if(!state.config.enabled)notify('To enable: CARECONTEXT_RESEARCH_MODE=1 zsh RUN_ON_MAC.command');else notify('Local research mode ready. Only authorized de-identified documents.',true);}catch(e){$('top-status').textContent='LOCAL SERVER / OFFLINE';notify('Start the FastAPI application in VS Code.');}
 $('research-file').addEventListener('change',e=>{
   if(state.busy)return;
   resetResults();const f=e.target.files?.[0];state.file=f||null;
   $('file-name').textContent=f?`${f.name} (${Math.ceil(f.size/1024)} KB) · ready to extract`:'No document selected.';
   if(f)notify('Document selected. Click Extract fields to process it.');
 });
 $('sample').addEventListener('click',()=>{
   if(state.busy)return;
   resetResults();$('research-file').value='';
   state.file=new File([SAMPLE],'sample-research-prescription.txt',{type:'text/plain'});
   $('file-name').textContent='sample-research-prescription.txt · fully synthetic';
   $('privacy-attest').checked=true;notify('Synthetic example loaded; click Extract fields.',true);
 });
 $('analyze').addEventListener('click',analyze);
 $('view-results').addEventListener('click',showResults);
 $('export').addEventListener('click',save);$('clear').addEventListener('click',clear);
}
init();
