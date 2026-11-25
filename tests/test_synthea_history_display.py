"""Regression tests: a Synthea medication history is not dosing instructions."""
from pathlib import Path

from carecontext.clinical_extract import analyze_document


SYNTHETIC_HISTORY = b'''SYNTHEA_030: converted simulated medication history
Source: Synthea sample CSV medication records
NOTE: This is not an original clinical prescription. All patients are simulated.

Medication: cetirizine hydrochloride 5 MG Oral Tablet
Recorded start: 2015-02-17T09:30:32Z

Medication: NDA020800 0.3 ML Epinephrine 1 MG/ML Auto-Injector
Recorded start: 2015-02-17T09:30:32Z

Medication: predniSONE 5 MG Oral Tablet
Recorded start: 2018-07-26T18:02:44Z

Medication: Hydrocortisone 10 MG/ML Topical Cream
Recorded start: 2019-09-19T10:56:44Z
Reason recorded in Synthea simulation: Atopic dermatitis (disorder)

Medication: Amoxicillin 250 MG / Clavulanate 125 MG Oral Tablet
Recorded start: 2020-04-16T06:56:44Z
Reason recorded in Synthea simulation: Sinusitis (disorder)

Medication: Hydrocortisone 10 MG/ML Topical Cream
Recorded start: 2020-09-10T00:56:44Z
Reason recorded in Synthea simulation: Atopic dermatitis (disorder)

Medication: Acetaminophen 160 MG Chewable Tablet
Recorded start: 2020-10-14T09:39:23Z

Medication: Amoxicillin 250 MG / Clavulanate 125 MG Oral Tablet
Recorded start: 2020-11-24T08:56:44Z
Reason recorded in Synthea simulation: Viral sinusitis (disorder)
'''


def test_synthea_preserves_eight_distinct_dated_entries():
    result = analyze_document('SYNTHEA_030.txt', SYNTHETIC_HISTORY)
    meds = result['medications']
    assert result['document']['kind'] == 'synthea_simulated_medication_history'
    assert len(meds) == 8
    assert not result['review_flags']
    assert len([m for m in meds if m['raw_name'] == 'Hydrocortisone']) == 2
    assert len([m for m in meds if m['raw_name'] == 'Amoxicillin / Clavulanate']) == 2
    assert meds[0]['strength'] == {'value': '5', 'unit': 'mg'}
    assert meds[0]['recorded_start'] == '2015-02-17T09:30:32Z'
    assert all(m['dose'] is None and m['frequency'] is None for m in meds)
    assert all('complex_or_weight_based_instruction_requires_review' not in m['warnings'] for m in meds)
    assert all('administration_instructions_not_in_source' in m['warnings'] for m in meds)
    assert result['review_required'] is True
    assert result['clinical_decision_supported'] is False


def test_synthea_auto_injector_and_concentrations_are_product_descriptions():
    meds = analyze_document('history.txt', SYNTHETIC_HISTORY)['medications']
    epi = meds[1]
    assert epi['raw_name'] == 'Epinephrine'
    assert epi['product_code'] == 'NDA020800'
    assert epi['package_volume'] == {'value': '0.3', 'unit': 'mL'}
    assert epi['strength'] == {'value': '1', 'unit': 'mg/mL'}
    assert epi['product_form'] == 'Auto-Injector'
    assert epi['dose'] is None
    hydro = meds[3]
    assert hydro['strength'] == {'value': '10', 'unit': 'mg/mL'}
    assert hydro['recorded_reason'] == 'Atopic dermatitis (disorder)'
    assert hydro['explicit_indication'] is None


def test_combination_ingredients_and_original_source_spans():
    result = analyze_document('SYNTHEA_030.txt', SYNTHETIC_HISTORY)
    med = result['medications'][4]
    assert med['raw_name'] == 'Amoxicillin / Clavulanate'
    assert med['strength'] is None  # avoid misrepresenting the 250/125 mg pair
    assert med['ingredients'] == [
        {'name': 'Amoxicillin', 'strength': {'value': '250', 'unit': 'mg'}},
        {'name': 'Clavulanate', 'strength': {'value': '125', 'unit': 'mg'}},
    ]
    assert med['recorded_reason'] == 'Sinusitis (disorder)'
    for item in result['medications']:
        for field in ['source', 'recorded_start_source', 'recorded_reason_source']:
            source = item[field]
            if source:
                text = SYNTHETIC_HISTORY.decode('utf-8')
                assert text[source['start']:source['end']] == source['text']
    # Never transform a recorded reason into an independently verified diagnosis.
    assert all(item['explicit_indication'] is None for item in result['medications'])
    assert result['symptoms'] == []


def test_synthea_rules_are_not_triggered_by_filename_alone():
    result = analyze_document('SYNTHEA_030.txt', b'Medication: Metformin 500 mg tablet - Take 1 tablet orally twice daily.')
    assert result['document']['kind'] == 'research_document'
    assert result['medications'][0]['dose']['quantity'] == '1'
    assert result['medications'][0]['frequency'] == 'twice daily'


def test_complex_warnings_are_for_directions_not_concentrations():
    product = analyze_document('product.txt', b'Medication: Hydrocortisone 10 MG/ML Topical Cream')
    assert len(product['medications']) == 1
    assert product['medications'][0]['strength'] == {'value':'10','unit':'mg/mL'}
    assert 'complex_or_weight_based_instruction_requires_review' not in product['medications'][0]['warnings']
    tapered = analyze_document('directions.txt', b'Medication: Prednisone 5 mg tablet - take according to schedule.')
    assert 'complex_or_weight_based_instruction_requires_review' in tapered['medications'][0]['warnings']


def test_generic_concentration_denominator_is_preserved():
    r = analyze_document('solution.txt', b'Medication: Cefalexin 250 mg/5 mL solution')
    assert r['medications'][0]['strength'] == {'value':'250', 'unit':'mg/5 mL'}
    assert r['medications'][0]['dose'] is None
    assert 'complex_or_weight_based_instruction_requires_review' not in r['medications'][0]['warnings']


def test_ambiguous_generic_combination_requires_source_review():
    r = analyze_document('combo.txt', b'Medication: Amoxicillin 250 mg / Clavulanate 125 mg tablet')
    assert len(r['medications']) == 1
    assert 'possible_combination_product_requires_review' in r['medications'][0]['warnings']
