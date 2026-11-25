"""Coarse reject-only identifier screen for locally authorized de-identified research.

This is NOT anonymization, DICOM de-identification or a HIPAA safe harbor test.
Any positive flag blocks the request; a negative result is not a privacy guarantee.
"""
from __future__ import annotations
import re

# Flag unmistakable labels and identifiers, not ordinary clinical dates or dosages.
FLAGS = {
    'email_address': re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I),
    'social_security_number': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'medical_record_number': re.compile(r'(?i)\b(?:MRN|medical\s+record\s+(?:number|no\.?))\s*[:#]\s*[A-Z0-9-]{4,}\b'),
    'date_of_birth': re.compile(r'(?i)\b(?:DOB|date\s+of\s+birth)\s*:\s*(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})'),
    'contact_phone': re.compile(r'(?i)\b(?:phone|mobile|tel|contact)\s*:\s*(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    'person_name': re.compile(r'(?im)^\s*(?:patient\s+name|full\s+name|patient)\s*:\s*[A-Z][a-zA-Z\-]+\s+[A-Z][a-zA-Z\-]+\s*$'),
}


def identifier_flags(text: str) -> list[str]:
    return [code for code, pattern in FLAGS.items() if pattern.search(text)]


class PrivacyBoundaryError(ValueError):
    pass


def assert_research_document_safe(filename: str, pages: list[tuple[int,str]]):
    # Read both filename and the extracted text. Never log or report the matched value.
    combined = filename + '\n' + '\n'.join(text for _, text in pages)
    codes = identifier_flags(combined)
    if codes:
        raise PrivacyBoundaryError('Potential direct identifiers detected (' + ', '.join(codes) + '). '
                                   'Remove all identifying information and retry locally. '
                                   'Automated screening cannot certify de-identification.')
