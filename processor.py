# processor.py
import os
import shutil
from datetime import datetime
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Import from our new modules
from config import CONTRACTS_DIR, ORIGINALS_DIR, CONTRACT_INDEX
from utils import ensure_dirs, next_contract_id, read_json, write_json

def read_contract_text(path):
    ext = path.split('.')[-1].lower()
    if ext == "txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == "pdf":
        reader = PdfReader(path)
        text = ""
        for p in reader.pages:
            text += p.extract_text() or ""
        return text
    return None

def save_pdf(file_path, text, title=None, footer=None):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    top_margin = height - 50
    x = 50
    y = top_margin

    # Title
    if title:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, title)
        y -= 24
        c.setFont("Helvetica", 10)

    c.setFont("Helvetica", 10)
    for line in text.split("\n"):
        # simple word wrap
        if len(line) > 120:
            chunks = [line[i:i+110] for i in range(0, len(line), 110)]
        else:
            chunks = [line]

        for chunk in chunks:
            c.drawString(x, y, chunk)
            y -= 14
            if y < 60:
                if footer:
                    c.setFont("Helvetica-Oblique", 8)
                    c.drawString(x, 40, footer)
                    c.setFont("Helvetica", 10)
                c.showPage()
                y = top_margin

    if footer:
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(x, 40, footer)
    c.save()

def save_uploaded_contract(uploaded_file):
    """
    Saves uploaded file into originals folder and creates a versioned v1 file in CONTRACTS_DIR.
    Returns (cid, versioned_path, extracted_text)
    """
    ensure_dirs()
    cid = next_contract_id()
    ext = uploaded_file.name.split(".")[-1].lower()
    
    # safe filenames
    orig_name = f"{cid}-original.{ext}"
    orig_path = os.path.join(ORIGINALS_DIR, orig_name)

    # write original file bytes
    with open(orig_path, "wb") as f:
        f.write(uploaded_file.read())

    # read text from original
    text = read_contract_text(orig_path) or ""

    # create v1 version in CONTRACTS_DIR:
    v1_filename = f"{cid}-v1.pdf"
    v1_path = os.path.join(CONTRACTS_DIR, v1_filename)

    # If original is PDF, copy directly to v1 (preserve content)
    if ext == "pdf":
        shutil.copyfile(orig_path, v1_path)
    else:
        # if original is txt, convert to PDF using save_pdf
        title = uploaded_file.name
        footer = f"{cid} • Version 1 • Uploaded {datetime.now().strftime('%Y-%m-%d')}"
        save_pdf(v1_path, text, title=title, footer=footer)

    # update index
    index = read_json(CONTRACT_INDEX)
    index[cid] = {
        "original_file": os.path.relpath(orig_path, start="."),
        "file": v1_filename,
        "version": 1,
        "original_name": uploaded_file.name,
        "uploaded_at": datetime.now().isoformat(),
        "last_updated": None
    }
    write_json(CONTRACT_INDEX, index)

    return cid, v1_path, text