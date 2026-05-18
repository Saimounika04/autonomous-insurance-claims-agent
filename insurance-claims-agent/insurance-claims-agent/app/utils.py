"""Document text extraction utilities (PDF, TXT, OCR fallback)."""
from __future__ import annotations

import io
import logging
from typing import Optional

import pdfplumber
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_txt(data: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def extract_text_from_pdf(data: bytes) -> str:
    """Try pdfplumber, fall back to PyPDF2, then OCR if needed."""
    text = ""

    # Primary: pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception as exc:  # pragma: no cover
        logger.warning("pdfplumber failed: %s", exc)

    if text.strip():
        return text

    # Fallback: PyPDF2
    try:
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as exc:  # pragma: no cover
        logger.warning("PyPDF2 failed: %s", exc)

    if text.strip():
        return text

    # Last resort: OCR (scanned PDF)
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(data)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
    except Exception as exc:  # pragma: no cover
        logger.warning("OCR failed: %s", exc)

    return text


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(data)
    if name.endswith(".txt"):
        return extract_text_from_txt(data)
    # Try PDF first, then TXT
    text = extract_text_from_pdf(data)
    return text or extract_text_from_txt(data)


# ---------------- Azure Blob Storage placeholder ----------------
def upload_to_azure_blob(filename: str, data: bytes) -> Optional[str]:
    """Upload original document to Azure Blob Storage. Returns blob URL or None.

    This is a placeholder — wire AZURE_STORAGE_CONNECTION_STRING in .env to enable.
    """
    import os

    conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container = os.getenv("AZURE_STORAGE_CONTAINER", "claims")
    if not conn:
        logger.info("Azure Blob not configured; skipping upload.")
        return None
    try:
        from azure.storage.blob import BlobServiceClient

        client = BlobServiceClient.from_connection_string(conn)
        blob = client.get_blob_client(container=container, blob=filename)
        blob.upload_blob(data, overwrite=True)
        return blob.url
    except Exception as exc:  # pragma: no cover
        logger.error("Azure upload failed: %s", exc)
        return None
