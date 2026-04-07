"""Document parser — extract plain text from PDF, DOCX, TXT, CSV."""

import csv
import io


def parse_pdf(content: bytes) -> str:
    """Extract text from a PDF file bytes."""
    import PyPDF2

    reader = PyPDF2.PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def parse_docx(content: bytes) -> str:
    """Extract text from a DOCX file bytes."""
    import docx

    doc = docx.Document(io.BytesIO(content))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def parse_txt(content: bytes) -> str:
    """Decode plain text, try utf-8 then latin-1 fallback."""
    try:
        return content.decode("utf-8").strip()
    except UnicodeDecodeError:
        return content.decode("latin-1").strip()


def parse_csv(content: bytes) -> str:
    """Convert CSV to a readable text representation."""
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append(", ".join(cell.strip() for cell in row))
    return "\n".join(rows)


def parse_document(filename: str, content: bytes) -> str:
    """Dispatch to the correct parser based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return parse_pdf(content)
    elif ext == "docx":
        return parse_docx(content)
    elif ext == "csv":
        return parse_csv(content)
    else:
        # txt and anything else — treat as plain text
        return parse_txt(content)
