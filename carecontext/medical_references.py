"""Opt-in, term-only lookups against NLM RxNorm and DailyMed metadata.

Never send raw clinical documents, symptoms, dates, questions or source snippets to
these APIs. Exact/normalized RxNorm matches are *candidates*, not authoritative
confirmation that the text was correctly transcribed.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import httpx

RXNORM_BASE = 'https://rxnav.nlm.nih.gov/REST'
DAILYMED_BASE = 'https://dailymed.nlm.nih.gov/dailymed/services/v2'
DRUG_TERM = re.compile(r'^[A-Za-z][A-Za-z /-]{2,58}$')

class ReferenceError(ValueError):
    pass


def clean_drug_term(term: str) -> str:
    normalized = ' '.join(term.strip().split())
    if not DRUG_TERM.fullmatch(normalized):
        raise ReferenceError('Only a medication name may be sent to reference APIs. Do not include document text or patient information.')
    return normalized


@dataclass(frozen=True)
class ReferenceConfig:
    online: bool = False
    timeout: float = 6


class MedicalReferences:
    def __init__(self, config: ReferenceConfig | None = None, transport=None):
        self.config = config or ReferenceConfig()
        self.transport = transport

    def lookup(self, raw_name: str) -> dict:
        term = clean_drug_term(raw_name)
        if not self.config.online:
            return {'term':term, 'status':'offline', 'rxnorm':None, 'dailymed':[],
                    'notice':'Live NLM lookups disabled. Enable explicitly for locally de-identified research.'}
        try:
            with httpx.Client(timeout=self.config.timeout, transport=self.transport, follow_redirects=False) as client:
                rx = self._get_json(client, RXNORM_BASE + '/rxcui.json', {'name':term,'search':'2'})
                labels = self._get_json(client, DAILYMED_BASE + '/spls.json',{'drug_name':term,'pagesize':5})
        except (httpx.HTTPError, ValueError) as exc:
            return {'term':term,'status':'unavailable', 'rxnorm':None,'dailymed':[],
                    'notice':'Upstream medical references unavailable or invalid. No medication identity was confirmed.'}
        group = rx.get('idGroup') if isinstance(rx.get('idGroup'),dict) else {}
        ids = group.get('rxnormId',[]) or []
        if isinstance(ids,str): ids=[ids]
        if not isinstance(ids,list): ids=[]
        ids = sorted(set(str(i) for i in ids if re.fullmatch(r'\d{1,12}',str(i))))
        resolution = 'one_candidate' if len(ids)==1 else 'ambiguous' if ids else 'not_found'
        meds = []
        label_data=labels.get('data',[])
        if not isinstance(label_data,list): label_data=[]
        for record in label_data[:5]:
            if not isinstance(record,dict): continue
            set_id = record.get('setid') or record.get('setId')
            if not isinstance(set_id,str) or not re.fullmatch(r'[a-fA-F0-9-]{30,40}',set_id): continue
            meds.append({'label_set_id':set_id,
                         'label_title':str(record.get('title') or '')[:140],
                         'published_date':str(record.get('published_date') or '')[:24],
                         'source_url':f'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}',
                         'source_type':'FDA structured product label metadata'})
        return {'term':term,'status':'candidate_lookup','rxnorm':{'status':resolution,'candidate_rxcuis':ids},
                'dailymed':meds,
                'notice':'NLM matches are reference candidates. They do not confirm the prescribed product, drug indication, safety, dosage or patient diagnosis.'}

    @staticmethod
    def _get_json(client, url, params):
        response=client.get(url,params=params,headers={'Accept':'application/json','User-Agent':'CareContext-open-source-research/0.4'})
        if response.status_code == 404:return {}
        response.raise_for_status()
        if len(response.content) > 256_000:
            raise ReferenceError('Unexpectedly large upstream response.')
        data = response.json()
        if not isinstance(data,dict): raise ReferenceError('Invalid NLM response.')
        return data
