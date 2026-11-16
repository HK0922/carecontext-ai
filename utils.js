export const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const formatDate = (value) => new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}).format(new Date(value.length===10 ? value+'T12:00:00Z' : value));
export function groupSources(sources) {
  const groups=new Map();
  for(const s of sources){if(!groups.has(s.document_id))groups.set(s.document_id,{...s,entries:[]});groups.get(s.document_id).entries.push(s);}
  return [...groups.values()].sort((a,b)=>b.date.localeCompare(a.date));
}
export function assertQuestion(value) {
  const q=value.trim();
  if(q.length<4)throw new Error('Enter a question with at least 4 characters.');
  if(q.length>600)throw new Error('Keep your question under 600 characters.');
  return q;
}
export const statusLabel = status => ({evidence_found:'Evidence found',insufficient_evidence:'Evidence gap',outside_scope:'Outside scope'}[status] || 'Review');
