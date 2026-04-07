from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any

from pypdf import PdfReader


@dataclass(frozen=True)
class ProductDoc:
    key: str
    title: str
    source_filename: str
    text_path: Path
    meta_path: Path


def _safe_key(key: str) -> str:
    k = (key or "").strip().lower()
    k = re.sub(r"[^a-z0-9_.-]+", "_", k)
    k = re.sub(r"_+", "_", k).strip("_")
    if not k:
        raise ValueError("product key is empty")
    return k[:80]


def instance_products_dir(instance_dir: Path) -> Path:
    return instance_dir / "products"

def instance_product_sources_dir(instance_dir: Path) -> Path:
    return instance_products_dir(instance_dir) / "_sources"


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def list_product_doc_keys(products_dir: Path) -> list[str]:
    if not products_dir.is_dir():
        return []
    keys = []
    for meta in sorted(products_dir.glob("*.meta.json")):
        keys.append(meta.stem.replace(".meta", ""))
    return keys


def load_product_doc(products_dir: Path, key: str) -> ProductDoc | None:
    k = _safe_key(key)
    meta_path = products_dir / f"{k}.meta.json"
    text_path = products_dir / f"{k}.txt"
    if not meta_path.exists() or not text_path.exists():
        return None
    meta = json.loads(_read_text(meta_path))
    return ProductDoc(
        key=k,
        title=str(meta.get("title") or k),
        source_filename=str(meta.get("source_filename") or ""),
        text_path=text_path,
        meta_path=meta_path,
    )


def extract_pdf_to_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt.strip():
            parts.append(f"\n--- page {i+1} ---\n{txt}")
    return "\n".join(parts).strip()


def _tesseract_available() -> bool:
    try:
        import pytesseract  # type: ignore

        # get_tesseract_version throws if binary not available
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_pdf_to_text(pdf_path: Path, *, lang: str = "tur+eng", max_pages: int = 200) -> str:
    """
    OCR for scanned/image-only PDFs.

    Requirements:
    - Tesseract OCR must be installed and available on PATH for pytesseract to work.
    """
    import pytesseract
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf_path))
    n = min(len(doc), int(max_pages))
    parts: list[str] = []
    for i in range(n):
        page = doc[i]
        # Render at higher DPI-ish scale for OCR quality
        pil = page.render(scale=2.0).to_pil()
        txt = pytesseract.image_to_string(pil, lang=lang) or ""
        if txt.strip():
            parts.append(f"\n--- page {i+1} (ocr) ---\n{txt}")
    return "\n".join(parts).strip()

def ingest_pdf(
    *,
    products_dir: Path,
    key: str,
    title: str,
    pdf_path: Path,
) -> ProductDoc:
    products_dir.mkdir(parents=True, exist_ok=True)
    k = _safe_key(key)
    # Keep a stable local copy under the instance so we don't depend on Cursor workspaceStorage paths.
    sources_dir = (products_dir / "_sources")
    sources_dir.mkdir(parents=True, exist_ok=True)
    pdf_local = sources_dir / f"{k}{pdf_path.suffix.lower() or '.pdf'}"
    shutil.copyfile(pdf_path, pdf_local)
    method = "pypdf_text"
    text = extract_pdf_to_text(pdf_local)
    if not text.strip():
        # Some PDFs are scanned/image-only; attempt OCR only if available.
        if not _tesseract_available():
            method = "ocr_unavailable"
            text = (
                "PDF text extraction returned empty text.\n"
                "OCR skipped because Tesseract OCR is not available on this machine.\n"
                f"Local PDF copy: {pdf_local}\n"
                "Fix: install Tesseract OCR (and Turkish language pack) or re-ingest on a machine with OCR.\n"
            )
        else:
            method = "tesseract_ocr"
            try:
                text = ocr_pdf_to_text(pdf_local)
            except Exception as e:
                # Keep the PDF copy, but store a diagnostic stub.
                method = "ocr_failed"
                text = (
                    f"PDF text extraction returned empty text; OCR attempt failed.\n"
                    f"error={e.__class__.__name__}: {e}\n"
                    f"Local PDF copy: {pdf_local}\n"
                    "Fix: verify Tesseract install + language packs; then re-ingest.\n"
                )
    text_path = products_dir / f"{k}.txt"
    meta_path = products_dir / f"{k}.meta.json"
    text_path.write_text(text, encoding="utf-8")
    meta = {
        "key": k,
        "title": title,
        "source_filename": pdf_path.name,
        "source_local_path": str(pdf_local),
        "type": "pdf_text",
        "extraction_method": method,
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return ProductDoc(key=k, title=title, source_filename=pdf_path.name, text_path=text_path, meta_path=meta_path)


def search_text(text: str, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    ql = q.lower()
    hits: list[dict[str, Any]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if ql in line.lower():
            hits.append({"line": idx, "text": line.strip()[:500]})
            if len(hits) >= limit:
                break
    return hits

