"""Conservative, inspectable research baselines for clinical document fields.

No diagnosis or drug indication is inferred. A matched field is a *candidate* that
requires source inspection. Character offsets always refer to extracted page text.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import re

from .studio_ingest import extract_pages

VERSION = 'clinical-extract-0.2'

# The small baseline deliberately prefers an abstention to a speculative extraction.
# This is NOT a model for handwritten prescriptions, medication reconciliation,
# prescription validation, drug safety checking or clinical decision support.
MEDICATION_RE = re.compile(
    r"(?i)^(?:\s*(?P<label>medication|med|rx|prescription|drug)\s*:\s*)?"
    r"(?P<name>[A-Z][a-zA-Z\-]{2,}(?:\s+[a-zA-Z][a-zA-Z\-]{2,}){0,2})"
    r"\s+(?P<strength>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>mcg|µg|μg|mg|g|mL|ml)\b(?P<tail>.*)$"
)
DOSE_RE = re.compile(r'(?i)\b(?:take|apply|inhale|inject|instill|use)\s+(\d+(?:\.\d+)?)\s+(tablet|tablets|capsule|capsules|mL|ml|puff|puffs|drop|drops)\b')
FREQ_RE = re.compile(r'(?i)\b(once\s+daily|twice\s+daily|three\s+times\s+daily|four\s+times\s+daily|every\s+\d+\s+hours|daily|weekly|at\s+bedtime|as\s+needed|bid|tid|qid|qhs|prn)\b')
DURATION_RE = re.compile(r'(?i)\bfor\s+\d+\s+(?:days?|weeks?|months?)\b')
ROUTES = [(re.compile(r'(?i)\b(?:by\s+mouth|orally|oral|po)\b'), 'oral'),
          (re.compile(r'(?i)\b(?:topically|topical)\b'), 'topical'),
          (re.compile(r'(?i)\b(?:intravenously|intravenous|iv)\b'), 'intravenous'),
          (re.compile(r'(?i)\b(?:intramuscularly|intramuscular|im)\b'), 'intramuscular'),
          (re.compile(r'(?i)\b(?:subcutaneously|subcutaneous)\b'), 'subcutaneous'),
          (re.compile(r'(?i)\b(?:inhaled|inhalation)\b'), 'inhaled')]
LABEL_RE = re.compile(r'(?i)^\s*(?:indication|reason\s+for\s+(?:prescription|medication)|diagnosis)\s*:\s*(.{3,180})$')
SYMPTOM_RE = re.compile(r'(?i)^\s*(?:symptoms?|reported\s+symptoms?|denies)\s*:\s*(.{2,200})$')
LAB_RE = re.compile(r'(?i)^\s*(?P<name>hemoglobin|creatinine|glucose|hba1c|a1c|sodium|potassium|platelets|wbc|tsh)\s*:\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>%|mg/dL|mmol/L|g/dL|mEq/L|K/uL|µIU/mL)?\s*(?:\(.*\))?$', re.I)

HIGH_RISK_COMPLEX = re.compile(r'(?i)(?:\b(?:taper|sliding\s+scale|according\s+to\s+schedule|weight[- ]based)\b|\b(?:mg|mcg|units?)\s*/\s*kg\b)')

@dataclass(frozen=True)
class Span:
    document_sha256: str
    page: int
    start: int
    end: int
    text: str
    source_id: str
    bbox: None = None  # pypdf/DOCX text baseline does not have spatial coordinates
    ocr_confidence: None = None  # never manufacture OCR confidence


def make_span(digest: str, page: int, text: str, start: int, end: int) -> dict:
    match = text[start:end]
    identifier = hashlib.sha256(f'{digest}:{page}:{start}:{end}:{match}'.encode()).hexdigest()[:16]
    return asdict(Span(digest, page, start, end, match, f'P{page}-{identifier}'))


def _decimal_value(s: str) -> str:
    try:
        return format(Decimal(s).normalize(), 'f')
    except InvalidOperation:
        return s


# A Synthea CSV conversion is a simulated medication HISTORY, not a prescription.
# Product strength, concentration and route implied by a dosage form are not
# patient-specific dose, administration frequency, or verified clinical history.
_SYNTHEA_MED = re.compile(r'(?i)^Medication:\s*(.+)$')
_SYNTHEA_CODE_VOLUME = re.compile(
    r'(?i)^(?P<code>NDA[0-9]{4,12})\s+(?P<volume>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>mL)\s+(?P<remainder>.+)$'
)
_SYNTHEA_FIRST_INGREDIENT = re.compile(
    r'(?i)^(?P<name>[A-Za-z][A-Za-z -]*?)\s+(?P<value>[0-9]+(?:\.[0-9]+)?)\s*'
    r'(?P<unit>mcg|mg|g|mL)(?:\s*/\s*(?P<denom>mL))?\b(?P<rest>.*)$'
)
_SYNTHEA_SECOND_INGREDIENT = re.compile(
    r'(?i)^\s*/\s*(?P<name>[A-Za-z][A-Za-z -]*?)\s+(?P<value>[0-9]+(?:\.[0-9]+)?)\s*'
    r'(?P<unit>mcg|mg|g)\b(?P<rest>.*)$'
)
_SYNTHEA_START = re.compile(r'^Recorded start:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)$')
_SYNTHEA_REASON = re.compile(r'^Reason recorded in Synthea simulation:\s*(.{2,180})$')


def _synthea_medication(description: str, span: dict) -> dict | None:
    """Parse a known simulated product-description format without inventing a sig."""
    product = description.strip()
    code = None
    package_volume = None
    packaging = _SYNTHEA_CODE_VOLUME.match(product)
    if packaging:
        code = packaging['code']
        package_volume = {'value': _decimal_value(packaging['volume']), 'unit': 'mL'}
        product = packaging['remainder']
    first = _SYNTHEA_FIRST_INGREDIENT.match(product)
    if not first:
        return None
    ingredient_name = first['name'].strip()
    unit = first['unit'].lower()
    unit = 'mL' if unit == 'ml' else unit
    if first['denom']:
        unit += '/mL'
    first_strength = {'value': _decimal_value(first['value']), 'unit': unit}
    ingredients = [{'name': ingredient_name, 'strength': first_strength}]
    rest = first['rest']
    second = _SYNTHEA_SECOND_INGREDIENT.match(rest)
    if second:
        second_unit = second['unit'].lower()
        ingredients.append({'name': second['name'].strip(), 'strength': {
            'value': _decimal_value(second['value']), 'unit': second_unit}})
        rest = second['rest']
    form = rest.strip(' .;-')
    if not form:
        return None  # don't guess where the label's product identity ends
    route = 'oral' if re.search(r'(?i)\boral\b', form) else (
        'topical' if re.search(r'(?i)\btopical\b', form) else None)
    return {
        'raw_name': ' / '.join(item['name'] for item in ingredients),
        'normalized_name': None, 'rxcui': None,
        'strength': first_strength if len(ingredients) == 1 else None,
        'ingredients': ingredients,
        'package_volume': package_volume, 'product_code': code,
        'product_form': form,
        'dose': None, 'route': route, 'route_basis': 'product_form' if route else None,
        'frequency': None, 'duration': None, 'explicit_indication': None,
        'recorded_start': None, 'recorded_reason': None,
        'recorded_start_source': None, 'recorded_reason_source': None,
        'source': span, 'extraction_method': 'synthea_product_description',
        'record_kind': 'synthea_simulated_medication_history',
        'status': 'manual_review_required',
        'warnings': ['administration_instructions_not_in_source'],
    }


def analyze_pages(name: str, digest: str, pages: list[tuple[int, str]], extraction: str = 'native_text') -> dict:
    medications, symptoms, labs, explicit_context, flags = [], [], [], [], []
    # Require both conversion markers; do not apply Synthea-specific rules to
    # unrelated clinical documents simply because their filename says Synthea.
    header = '\n'.join(text[:700] for _, text in pages[:2]).lower()
    is_synthea = ('converted simulated medication history' in header
                  and 'synthea sample csv medication records' in header)
    most_recent_synthea_med = None
    for page, text in pages:
        offset = 0
        for raw_line in text.splitlines(keepends=True):
            line = raw_line.rstrip('\r\n')
            stripped = line.strip()
            start = offset + len(line) - len(line.lstrip())
            offset += len(raw_line)
            if not stripped:
                continue
            span = make_span(digest, page, text, start, start + len(stripped))
            if is_synthea:
                synthetic_line = _SYNTHEA_MED.match(stripped)
                if synthetic_line:
                    med = _synthea_medication(synthetic_line.group(1), span)
                    if med is not None:
                        medications.append(med)
                        most_recent_synthea_med = med
                    else:
                        most_recent_synthea_med = None
                        flags.append({'code': 'unparsed_medication_line', 'page': page,
                                      'source_id': span['source_id'],
                                      'note': 'Product description could not be parsed; review the source.'})
                    continue
                recorded_start = _SYNTHEA_START.match(stripped)
                if recorded_start and most_recent_synthea_med is not None:
                    most_recent_synthea_med['recorded_start'] = recorded_start.group(1)
                    most_recent_synthea_med['recorded_start_source'] = span
                    continue
                recorded_reason = _SYNTHEA_REASON.match(stripped)
                if recorded_reason and most_recent_synthea_med is not None:
                    most_recent_synthea_med['recorded_reason'] = recorded_reason.group(1).strip()
                    most_recent_synthea_med['recorded_reason_source'] = span
                    continue
            context = LABEL_RE.match(stripped)
            if context:
                explicit_context.append({'text':context.group(1).strip(), 'source':span, 'type':'explicit_document_context',
                                         'warning':'Documented text only; it is not an independently confirmed diagnosis.'})
                continue
            symptom = SYMPTOM_RE.match(stripped)
            if symptom:
                symptoms.append({'raw_text':symptom.group(1).strip(), 'source':span,
                                 'negated': stripped.lower().startswith('denies') or bool(re.match(r'(?i)\s*(?:no|none|denies)\b',symptom.group(1))),
                                 'temporality': 'historical' if re.search(r'(?i)\b(?:history\s+of|previously|in\s+the\s+past)\b',stripped) else 'unspecified',
                                 'kind':'documented_symptom_statement'})
                continue
            lab = LAB_RE.match(stripped)
            if lab:
                labs.append({'name':lab.group('name').lower(), 'value':_decimal_value(lab.group('value')),
                             'unit':lab.group('unit'), 'source':span, 'loinc':None, 'status':'unverified_extraction'})
                continue
            candidate = MEDICATION_RE.match(stripped)
            if not candidate:
                if re.match(r'(?i)^\s*(?:rx|medication|prescription|med)\s*:',stripped):
                    flags.append({'code':'unparsed_medication_line','page':page,'source_id':span['source_id'],
                                  'note':'Medication-like line not extracted; manual review required.'})
                continue
            # Require an explicit Rx label or recognizable dosing context to avoid
            # misclassifying arbitrary name-number combinations as prescriptions.
            tail = candidate.group('tail') or ''
            if not candidate.group('label') and not re.search(r'(?i)\b(?:tablet|capsule|take|daily|oral|by\s+mouth|injection|solution|cream)\b',tail):
                continue
            med_name = candidate.group('name').strip()
            # Reject misleading prefix tokens rather than guessing a medication.
            if med_name.lower().split()[0] in {'take','patient','doctor','date','diagnosis','age','received','prescribed'}:
                continue
            warnings=[]
            if HIGH_RISK_COMPLEX.search(stripped) or re.search(r'(?i)\b(?:pediatric|child|weight-based)\b',stripped):
                warnings.append('complex_or_weight_based_instruction_requires_review')
            dose_match = DOSE_RE.search(tail)
            freq = FREQ_RE.search(tail)
            duration = DURATION_RE.search(tail)
            route = next((value for pattern, value in ROUTES if pattern.search(tail)), None)
            strength_unit = candidate.group('unit').replace('μ','µ').lower()
            strength_unit = {'µg':'mcg','ml':'mL'}.get(strength_unit,strength_unit)
            # Product concentrations are not administration instructions.
            # Keep the denominator, including a stated volume (e.g., mg/5 mL).
            denominator = re.match(r'(?i)^\s*/\s*(?P<amount>\d+(?:\.\d+)?)?\s*mL\b', tail)
            if denominator and strength_unit != 'mL':
                fraction = (f"{_decimal_value(denominator['amount'])} " if denominator['amount'] else '') + 'mL'
                strength_unit += '/' + fraction
            # Do not silently claim a multi-ingredient product was fully parsed.
            if re.match(r'(?i)^\s*/\s*[A-Za-z][A-Za-z -]+?\s+\d+(?:\.\d+)?\s*(?:mg|g|mcg)\b', tail):
                warnings.append('possible_combination_product_requires_review')
            medications.append({
                'raw_name':med_name, 'normalized_name':None, 'rxcui':None,
                'strength':{'value':_decimal_value(candidate.group('strength')),'unit':strength_unit},
                'dose': {'raw':dose_match.group(0),'quantity':_decimal_value(dose_match.group(1)), 'form':dose_match.group(2).lower()} if dose_match else None,
                'route':route, 'frequency':freq.group(0) if freq else None,
                'duration':duration.group(0) if duration else None,
                'explicit_indication':None, 'source':span,
                'extraction_method':'rule_baseline', 'status':'manual_review_required',
                'warnings':warnings + (['frequency_missing'] if not freq else []) + (['dose_missing'] if not dose_match else [])
            })
    if extraction == 'ocr':
        flags.append({'code':'ocr_uncertainty','note':'OCR output is unverified; this pipeline has no word-level confidence or page bounding boxes.'})
    if not medications:
        flags.append({'code':'no_medication_confidently_extracted','note':'The document may contain medications, but the conservative baseline could not identify them.'})
    return {'version': VERSION,'document':{'name':name,'sha256':digest,'pages':len(pages),'extraction':extraction,
                                      'kind':'synthea_simulated_medication_history' if is_synthea else 'research_document'},
            'medications':medications, 'symptoms':symptoms, 'labs':labs, 'explicit_context':explicit_context,
            'review_flags':flags,'review_required':True,'clinical_decision_supported':False,
            'notice':'Source-extracted candidates only. A prescription does not establish the patient\'s symptoms, diagnosis or treatment appropriateness.'}


def analyze_document(filename: str, data: bytes) -> dict:
    pages, metadata = extract_pages(filename, data)
    return analyze_pages(metadata['name'],metadata['sha256'],pages, metadata['extraction'])
