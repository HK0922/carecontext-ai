"""In-memory document text extraction for synthetic records only.

No uploaded bytes are persisted. Never treat extracted text as instructions.
"""
from __future__ import annotations
from io import BytesIO
from hashlib import sha256
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree

MAX_FILE_BYTES = 3 * 1024 * 1024
MAX_EXTRACTED = 18000
MAX_PAGES = 14
MAX_CHUNKS = 32

class DocumentError(ValueError):
    pass


def _text_from_pdf(data: bytes):
    if not data.startswith(b'%PDF-'):
        raise DocumentError('The file is not a valid PDF.')
    try:
        from pypdf import PdfReader
        pdf = PdfReader(BytesIO(data), strict=False)
        if pdf.is_encrypted:
            raise DocumentError('Encrypted PDFs cannot be opened in this prototype.')
        if len(pdf.pages) > MAX_PAGES:
            raise DocumentError(f'PDFs may contain at most {MAX_PAGES} pages.')
        return [(i + 1, p.extract_text() or '') for i, p in enumerate(pdf.pages)]
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError('The PDF could not be read or has unsupported encoding.') from exc


def _text_from_docx(data: bytes):
    # Do not extract any files to disk or follow external relationships.
    try:
        with zipfile.ZipFile(BytesIO(data)) as z:
            members = z.infolist()
            if sum(m.file_size for m in members) > 8 * 1024 * 1024:
                raise DocumentError('DOCX expanded content exceeds the size limit.')
            if 'word/document.xml' not in z.namelist():
                raise DocumentError('The DOCX has no document body.')
            xml = z.read('word/document.xml')
            if b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
                raise DocumentError('DOCX files with inline entities are not supported.')
            tree = ElementTree.fromstring(xml)
            ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            lines = [''.join(t.text or '' for t in p.iter(ns + 't')) for p in tree.iter(ns + 'p')]
            return [(1, '\n'.join(lines))]
    except DocumentError:
        raise
    except (zipfile.BadZipFile, ElementTree.ParseError, KeyError, RuntimeError) as exc:
        raise DocumentError('Unable to read the DOCX file.') from exc


def _text_from_image(data: bytes):
    try:
        from PIL import Image, UnidentifiedImageError
        import pytesseract
        Image.MAX_IMAGE_PIXELS = 8_000_000
        img = Image.open(BytesIO(data))
        img.verify()
        img = Image.open(BytesIO(data))
        if img.width * img.height > 8_000_000:
            raise DocumentError('Image dimensions are too large for local OCR.')
        return [(1, pytesseract.image_to_string(img.convert('RGB'), timeout=8))]
    except DocumentError:
        raise
    except (ImportError, FileNotFoundError):
        raise DocumentError('Image OCR requires the optional local OCR dependencies and Tesseract.')
    except Exception as exc:
        raise DocumentError('Could not extract image text. Use a text-based document instead.') from exc


def _chunks(pages):
    chunks = []
    total = 0
    for page_no, raw in pages:
        clean = re.sub(r'[ \t]+', ' ', raw.replace('\x00', ' ')).strip()
        if not clean:
            continue
        total += len(clean)
        if total > MAX_EXTRACTED:
            raise DocumentError('Document text is too long for this prototype; use a shorter synthetic document.')
        # Fixed-size overlapping windows preserve locality and page references.
        position = 0
        while position < len(clean):
            piece = clean[position:position + 650].strip()
            if piece:
                chunks.append({'page': page_no, 'text': piece})
            if len(chunks) > MAX_CHUNKS:
                raise DocumentError('This document contains more passages than the current limit.')
            if position + 650 >= len(clean):
                break
            position += 560
    return chunks


def extract_pages(filename: str, data: bytes):
    """Return bounded full-page text and immutable provenance metadata.

    OCR text is intentionally marked unverified; pypdf supplies no reliable
    bounding boxes or confidence and we never fabricate either.
    """
    if not data or len(data) > MAX_FILE_BYTES:
        raise DocumentError('Please select a nonempty document under 3 MB.')
    safe_name = Path(filename.replace('\\', '/').split('/')[-1]).name[:90]
    if not safe_name or any(ord(c) < 32 for c in safe_name):
        raise DocumentError('Invalid document filename.')
    ext = Path(safe_name).suffix.lower()
    if ext == '.pdf':
        pages = _text_from_pdf(data)
    elif ext == '.docx':
        pages = _text_from_docx(data)
    elif ext in {'.txt', '.md'}:
        try:
            pages = [(1, data.decode('utf-8-sig'))]
        except UnicodeError as exc:
            raise DocumentError('Text files must use UTF-8 encoding.') from exc
    elif ext in {'.png', '.jpg', '.jpeg'}:
        pages = _text_from_image(data)
    else:
        raise DocumentError('Supported: .pdf, .docx, .txt, .md, .png and .jpg (OCR needs Tesseract).')
    if not any(p.strip() for _, p in pages):
        raise DocumentError('No readable text was found. Scanned PDFs require OCR; review image text manually.')
    if sum(len(p) for _, p in pages) > MAX_EXTRACTED:
        raise DocumentError('Document text is too long for this research session.')
    digest = sha256(data).hexdigest()
    return pages, {'name': safe_name, 'sha256': digest,
                   'extraction': 'ocr' if ext in {'.png', '.jpg', '.jpeg'} else 'native_text'}


def extract_document(filename: str, data: bytes):
    if not data or len(data) > MAX_FILE_BYTES:
        raise DocumentError('Please select a nonempty document under 3 MB.')
    safe_name = Path(filename.replace('\\', '/').split('/')[-1]).name[:90]
    if not safe_name or any(ord(c) < 32 for c in safe_name):
        raise DocumentError('Invalid document filename.')
    ext = Path(safe_name).suffix.lower()
    if ext == '.pdf':
        pages = _text_from_pdf(data)
    elif ext == '.docx':
        pages = _text_from_docx(data)
    elif ext in {'.txt', '.md'}:
        try:
            pages = [(1, data.decode('utf-8-sig'))]
        except UnicodeError as exc:
            raise DocumentError('Text files must use UTF-8 encoding.') from exc
    elif ext in {'.png', '.jpg', '.jpeg'}:
        pages = _text_from_image(data)
    else:
        raise DocumentError('Supported: .pdf, .docx, .txt, .md, .png and .jpg (OCR needs Tesseract).')
    excerpts = _chunks(pages)
    if not excerpts:
        raise DocumentError('No readable text was found. Scanned PDFs require OCR; review image text manually.')
    digest = sha256(data).hexdigest()
    for i, excerpt in enumerate(excerpts):
        excerpt['source_id'] = f'{digest[:10]}-{i+1:02d}'
        excerpt['source_name'] = safe_name
    return {'name': safe_name, 'sha256': digest, 'pages': len(pages),
            'passages': excerpts, 'passage_count': len(excerpts), 'extraction': 'OCR' if ext in {'.png','.jpg','.jpeg'} else 'document-text',
            'notice': 'User-supplied text is not independently verified. Check all transcription and source details.'}
