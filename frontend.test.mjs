import test from 'node:test';
import assert from 'node:assert/strict';
import {escapeHtml,formatDate,groupSources,assertQuestion,statusLabel} from '../carecontext/web/utils.js';
test('untrusted source content and quote-bearing attributes are escaped',()=>{
 assert.equal(escapeHtml('<img src=x onerror="alert(1)">'),'&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
 assert.equal(escapeHtml("' &"),'&#39; &amp;');
});
test('dates do not shift into the previous day in western time zones',()=>assert.equal(formatDate('2026-05-14'),'May 14, 2026'));
test('source library preserves passage order and groups distinct documents newest first',()=>{
 const data=[{id:'A:1',document_id:'A',date:'2026-01-01'},{id:'B:1',document_id:'B',date:'2026-02-01'},{id:'A:2',document_id:'A',date:'2026-01-01'}];
 const groups=groupSources(data);assert.deepEqual(groups.map(g=>g.document_id),['B','A']);assert.deepEqual(groups[1].entries.map(x=>x.id),['A:1','A:2']);assert.equal(data.length,3);
});
test('questions are trimmed and bounded before submission',()=>{assert.equal(assertQuestion('  What allergy?  '),'What allergy?');assert.throws(()=>assertQuestion('  '));assert.throws(()=>assertQuestion('x'.repeat(601)));});
test('abstentions are labeled as evidence gaps rather than clinical negatives',()=>assert.equal(statusLabel('insufficient_evidence'),'Evidence gap'));
