"""
pdf_parser.py

Extracts plain text from an uploaded PDF resume so it can be fed into
the same matching logic we already built (matcher.py expects plain text).

Uses pdfplumber, which handles real-world resume PDFs (multi-column
layouts, tables, varied fonts) better than simpler libraries like
PyPDF2, which often mangle spacing or drop text from styled PDFs.
"""

import pdfplumber
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    full_text = "\n".join(text_parts)
    
    # Join lines that were wrapped mid-sentence (no punctuation at end)
    # so "I'm a dedicated..." and "classes 5-10." merge into one line
    import re
    full_text = re.sub(r'(?<![.!?:\-])\n(?=[a-z])', ' ', full_text)
    
    return full_text