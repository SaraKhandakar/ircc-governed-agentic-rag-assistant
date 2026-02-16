import os
import re
import json
import time
from urllib.parse import urlparse

import pandas as pd
import requests
from tqdm import tqdm
import pdfplumber
from bs4 import BeautifulSoup

# -----------------------------
# Config
# -----------------------------
CATALOG_PATH = "catalog/approved_source_catalog.csv"

RAW_PDF_DIR = "data_raw/pdf"
RAW_CSV_DIR = "data_raw/csv"
RAW_HTML_DIR = "data_raw/html"
TEXT_DIR = "data_text"
CHUNKS_DIR = "chunks"
LOGS_DIR = "logs"

os.makedirs(RAW_PDF_DIR, exist_ok=True)
os.makedirs(RAW_CSV_DIR, exist_ok=True)
os.makedirs(RAW_HTML_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

DOWNLOAD_TIMEOUT = 60
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; IRCC-RAG-Student-Project/1.0)"
}

# Chunking defaults (good starting point)
CHUNK_WORDS = 500
OVERLAP_WORDS = 80

# -----------------------------
# Helpers
# -----------------------------
def normalise_yes_no(val: str) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ["yes", "y", "true", "1", "approved"]

def safe_filename(s: str, max_len: int = 120) -> str:
    s = re.sub(r"[^\w\-\. ]+", "", s)
    s = s.strip().replace(" ", "_")
    return s[:max_len] if s else "untitled"

def guess_type_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith(".csv"):
        return "csv"
    if path.endswith(".html") or path.endswith(".htm"):
        return "html"
    return "html"  # default fallback

def log_line(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(os.path.join(LOGS_DIR, "pipeline.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def download_file(url: str, out_path: str) -> bool:
    try:
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=DOWNLOAD_TIMEOUT)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        log_line(f"DOWNLOAD FAILED: {url} -> {e}")
        return False

def extract_text_from_pdf(pdf_path: str) -> str:
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text)
    except Exception as e:
        log_line(f"PDF TEXT EXTRACTION FAILED: {pdf_path} -> {e}")
    return "\n".join(text_parts)

def extract_text_from_html_file(html_path: str) -> str:
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        soup = BeautifulSoup(html, "lxml")

        # Remove junk
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Keep headings and paragraphs
        chunks = []
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            t = el.get_text(" ", strip=True)
            if t:
                chunks.append(t)

        return "\n".join(chunks)
    except Exception as e:
        log_line(f"HTML TEXT EXTRACTION FAILED: {html_path} -> {e}")
        return ""

def extract_text_from_csv_file(csv_path):
    # 1) Quick check: sometimes a "csv" download is actually an HTML error page
    with open(csv_path, "rb") as f:
        head = f.read(400).lower()

    if b"<html" in head or b"<!doctype html" in head:
        raise ValueError("Downloaded file looks like HTML (not a real CSV). Check download_url or site redirect.")

    # 2) Try reading with common encodings and separators
    read_errors = []

    for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin1"]:
        for sep in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(csv_path, encoding=encoding, sep=sep, engine="python", on_bad_lines="skip")
                if df.shape[1] < 2:
                    # Likely wrong delimiter, try next
                    continue

                # Keep it lightweight: limit rows/cols so we don't explode memory
                df = df.head(2000)  # adjust if needed
                df = df.iloc[:, :30]

                # Convert to text
                df = df.fillna("")
                text = df.astype(str).apply(lambda r: " | ".join(r.values), axis=1).str.cat(sep="\n")
                return text

            except Exception as e:
                read_errors.append(f"encoding={encoding}, sep={sep} -> {type(e).__name__}: {e}")

    # If we got here, everything failed
    raise ValueError("Failed to parse CSV. Tried multiple encodings/separators.\n" + "\n".join(read_errors[:8]))


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)   # collapse spaces
    return text.strip()

def section_aware_split(text: str) -> list[str]:
    """
    Lightweight “section-aware” split:
    break on lines that look like headings (ALL CAPS or numbered headings).
    """
    lines = text.split("\n")
    sections = []
    current = []

    heading_re = re.compile(r"^(\d+(\.\d+)*\s+.+|[A-Z][A-Z\s\-]{6,})$")

    for line in lines:
        l = line.strip()
        if not l:
            continue

        if heading_re.match(l) and len(current) > 0:
            sections.append("\n".join(current))
            current = [l]
        else:
            current.append(l)

    if current:
        sections.append("\n".join(current))

    if len(sections) <= 1:
        return [text]
    return sections

def chunk_by_words(text: str, chunk_words: int, overlap_words: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    step = max(1, chunk_words - overlap_words)

    while start < len(words):
        end = start + chunk_words
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += step

    return chunks

def make_chunks(text: str, chunk_words: int = CHUNK_WORDS, overlap_words: int = OVERLAP_WORDS) -> list[str]:
    sections = section_aware_split(text)
    out = []
    for sec in sections:
        sec = clean_text(sec)
        if not sec:
            continue
        out.extend(chunk_by_words(sec, chunk_words, overlap_words))
    return out

# -----------------------------
# Catalog loader
# -----------------------------
def load_catalog(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Map your column names to these standard fields.
    # If your CSV uses different names, add them here.
    col_map_candidates = {
        "title": ["title", "document_title", "name"],
        "url": ["url", "link", "source_url"],
        "type": ["type", "format", "file_type"],
        "approved": ["approved", "approval", "is_approved", "status"],
        "owner": ["owner", "publisher", "department"],
        "last_updated": ["last_updated", "updated", "last_modified", "date"],
        "tags": ["tags", "tag", "topics", "category"]
    }

    def pick_col(possible):
        for c in possible:
            if c in df.columns:
                return c
        return None

    selected = {}
    for target, candidates in col_map_candidates.items():
        selected[target] = pick_col(candidates)

    if not selected["url"]:
        raise ValueError("Catalog must contain a URL column (e.g., url/link/source_url).")

    df_std = pd.DataFrame()
    df_std["title"] = df[selected["title"]] if selected["title"] else ""
    df_std["url"] = df[selected["url"]]
    df_std["type"] = df[selected["type"]] if selected["type"] else df_std["url"].apply(guess_type_from_url)
    df_std["approved"] = df[selected["approved"]].apply(normalise_yes_no) if selected["approved"] else True
    df_std["owner"] = df[selected["owner"]] if selected["owner"] else ""
    df_std["last_updated"] = df[selected["last_updated"]] if selected["last_updated"] else ""
    df_std["tags"] = df[selected["tags"]] if selected["tags"] else ""

    df_std["title"] = df_std["title"].fillna("").astype(str).str.strip()
    df_std["url"] = df_std["url"].fillna("").astype(str).str.strip()
    df_std["type"] = df_std["type"].fillna("").astype(str).str.lower().str.strip()

    df_std = df_std[df_std["approved"] == True].reset_index(drop=True)
    return df_std

# -----------------------------
# Main pipeline
# -----------------------------
def pipeline():
    log_line("Starting pipeline...")
    catalog = load_catalog(CATALOG_PATH)
    log_line(f"Approved sources loaded: {len(catalog)}")

    all_chunk_records = []
    failed_sources = []

    for idx, row in tqdm(catalog.iterrows(), total=len(catalog)):
        title = row["title"] if row["title"] else f"source_{idx+1}"
        url = row["url"]
        ftype = row["type"] if row["type"] else guess_type_from_url(url)

        base_name = safe_filename(title) or f"source_{idx+1}"
        source_id = f"IRCC_{idx+1:04d}"

        # Download path
        if ftype == "pdf":
            raw_path = os.path.join(RAW_PDF_DIR, f"{source_id}_{base_name}.pdf")
        elif ftype == "csv":
            raw_path = os.path.join(RAW_CSV_DIR, f"{source_id}_{base_name}.csv")
        else:
            raw_path = os.path.join(RAW_HTML_DIR, f"{source_id}_{base_name}.html")

        # Download
        if not os.path.exists(raw_path):
            ok = download_file(url, raw_path)
            if not ok:
                failed_sources.append({"source_id": source_id, "title": title, "url": url, "reason": "download_failed"})
                continue

        # Extract text
        if ftype == "pdf":
            text = extract_text_from_pdf(raw_path)
        elif ftype == "csv":
            text = extract_text_from_csv_file(raw_path)
        else:
            text = extract_text_from_html_file(raw_path)

        text = clean_text(text)
        if not text or len(text.split()) < 50:
            failed_sources.append({"source_id": source_id, "title": title, "url": url, "reason": "no_text_or_too_short"})
            continue

        # Save extracted text
        text_path = os.path.join(TEXT_DIR, f"{source_id}_{base_name}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Chunk
        chunks = make_chunks(text, CHUNK_WORDS, OVERLAP_WORDS)
        if not chunks:
            failed_sources.append({"source_id": source_id, "title": title, "url": url, "reason": "chunking_failed"})
            continue

        # Chunk records
        for c_idx, c_text in enumerate(chunks, start=1):
            chunk_id = f"{source_id}_C{c_idx:04d}"
            rec = {
                "chunk_id": chunk_id,
                "source_id": source_id,
                "title": title,
                "url": url,
                "type": ftype,
                "owner": row.get("owner", ""),
                "last_updated": row.get("last_updated", ""),
                "tags": row.get("tags", ""),
                "text": c_text
            }
            all_chunk_records.append(rec)

    # Write outputs
    out_jsonl = os.path.join(CHUNKS_DIR, "chunks.jsonl")
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for rec in all_chunk_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    out_csv = os.path.join(CHUNKS_DIR, "chunks.csv")
    pd.DataFrame(all_chunk_records).to_csv(out_csv, index=False, encoding="utf-8")

    fail_path = os.path.join(LOGS_DIR, "failed_sources.json")
    with open(fail_path, "w", encoding="utf-8") as f:
        json.dump(failed_sources, f, ensure_ascii=False, indent=2)

    log_line(f"Done. Chunks created: {len(all_chunk_records)}")
    log_line(f"Chunk files saved: {out_jsonl} and {out_csv}")
    log_line(f"Failures logged: {fail_path}")

if __name__ == "__main__":
    pipeline()
