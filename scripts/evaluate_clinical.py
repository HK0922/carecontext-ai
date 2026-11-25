"""Fieldwise evaluation with exact-match scoring, Wilson CI, and no clinical claims.

The included fixture is authored by this project. An external dataset with
independently adjudicated annotations must be substituted for clinical claims.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from carecontext.clinical_extract import analyze_document,VERSION
FIELDS=('raw_name','strength_value','unit','route','frequency','duration')


def ci_wilson(success,total):
    if total==0:return None
    z=1.95996398454; p=success/total; z2=z*z
    center=(p+z2/(2*total))/(1+z2/total)
    half=z*math.sqrt(p*(1-p)/total+z2/(4*total*total))/(1+z2/total)
    return [round(max(0,center-half),4),round(min(1,center+half),4)]


def analyze_fixture(path):
    fixture=json.loads(Path(path).read_text())
    scores=defaultdict(lambda:{'correct':0,'total':0})
    docs=[]
    for e in fixture['examples']:
        result=analyze_document(e['id']+'.txt',e['text'].encode())
        actual=result['medications']
        expected=e['expected']
        names=sorted(m['raw_name'].lower() for m in actual)
        gold_names=sorted(m['raw_name'].lower() for m in expected)
        matched=names==gold_names
        scores['document_medication_list_exact']['total']+=1
        scores['document_medication_list_exact']['correct']+=int(matched)
        if matched:
            left={m['raw_name'].lower():m for m in actual}
            for exp in expected:
                observed=left[exp['raw_name'].lower()]
                for key in FIELDS:
                    if key=='raw_name':continue
                    val=observed.get('strength',{}).get('value') if key=='strength_value' else observed.get('strength',{}).get('unit') if key=='unit' else observed.get(key)
                    scores[key]['total']+=1
                    scores[key]['correct']+=int(val==exp[key])
        docs.append({'id':e['id'],'expected_medication_names':gold_names,'actual_medication_names':names,'names_exact_match':matched})
    stats={key:{'correct':value['correct'],'total':value['total'],'accuracy':round(value['correct']/value['total'],4) if value['total'] else None,
                'wilson_95_ci':ci_wilson(value['correct'],value['total'])} for key,value in scores.items()}
    return {'evaluation_type':'synthetic_author_written_regression_not_clinical_validation','extractor_version':VERSION,
            'data_source':str(Path(path).name),'sample_size':len(docs),'scores':stats,'examples':docs,
            'limitations':['No independent clinician annotations','No handwritten-OCR benchmark','No external documents','No dosage safety validation','No diagnosis inference']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--gold',default=str(ROOT/'tests/fixtures/medication_gold.json'));p.add_argument('--output',default=str(ROOT/'evaluations/clinical/author_written_results.json'));a=p.parse_args()
    result=analyze_fixture(a.gold)
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sample_size':result['sample_size'],'scores':result['scores']},indent=2))

if __name__=='__main__':main()
