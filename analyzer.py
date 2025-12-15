# analyzer.py
import re
import time
from datetime import datetime

from config import REGS_FILE
from utils import read_json, write_json

# Section parsing (Heading-based)
HEADING_RE = re.compile(r'^[A-Z0-9 \-&(),]{3,}$')

def split_into_sections(text):
    """
    Splits text into sections based on ALL CAPS headers.
    """
    lines = [ln.rstrip() for ln in text.splitlines()]
    sections = []
    current_heading = "Preamble"
    current_lines = []

    for ln in lines:
        if ln.strip() == "":
            current_lines.append("")
            continue

        # Check if line looks like a Header
        if HEADING_RE.match(ln.strip()):
            if current_lines or sections:
                sections.append((current_heading.strip(), "\n".join(current_lines).strip()))
            current_heading = ln.strip()
            current_lines = []
        else:
            current_lines.append(ln)

    # Append the last section
    sections.append((current_heading.strip(), "\n".join(current_lines).strip()))
    return sections

def sections_to_text(sections):
    """
    Joins sections back into a single string.
    """
    out = []
    for h, c in sections:
        if h and h != "Preamble":
            out.append(h)
        if c:
            out.append(c)
        out.append("")  # blank line
    return "\n".join(out).strip()

def inject_clause_smartly(original_text, new_clause_text):
    """
    Inserts a new clause before specific sections to ensure it appears 
    INSIDE the contract body, not at the end.
    """
    # EXPANDED PATTERNS: The code stops at the FIRST match it finds.
    # We prioritize "User Guide" or "Sample" text to catch the end of the real contract content.
    target_patterns = [
        # 1. PRIORITY: Markers that appear right after the last real clause in your template
        r'(?i)^\s*This\s+is\s+a\s+sample',  # Matches "This is a sample of the..."
        r'(?i)^\s*USER\s+GUIDE',            # Matches "USER GUIDE"
        
        # 2. Standard Legal Headers (If the above aren't found)
        r'(?i)^\s*\d*\.?\s*TERM\s+AND\s+TERMINATION', 
        r'(?i)^\s*\d*\.?\s*WARRANTIES',                
        r'(?i)^\s*\d*\.?\s*LIMITATION\s+OF\s+LIABILITY',
        r'(?i)^\s*\d*\.?\s*GENERAL\s+PROVISIONS',
        r'(?i)^\s*\d*\.?\s*INDEMNIFICATION',
        
        # 3. Fallback Markers (Insert before signatures/annexes if nothing else matches)
        r'(?i)^\s*IN\s+WITNESS\s+WHEREOF',
        r'(?i)^\s*SIGNATURES?',
        r'(?i)^\s*ANNEXES',
        r'(?i)^\s*GENERAL\s+RECOMMENDATIONS'
    ]

    insertion_index = -1
    
    # Search for the best insertion point
    for pattern in target_patterns:
        match = re.search(pattern, original_text, re.MULTILINE)
        if match:
            insertion_index = match.start()
            break 

    # Insert or Fallback
    if insertion_index != -1:
        part_1 = original_text[:insertion_index].rstrip()
        part_2 = original_text[insertion_index:]
        
        # Add visual separators (\n\n) to ensure clean formatting
        updated_text = f"{part_1}\n\n{new_clause_text}\n\n{part_2}"
        return updated_text
    else:
        # Fallback: If absolutely no headers found, append to end
        return f"{original_text}\n\n{new_clause_text}"

def apply_updates_inline(sections, regs):
    """
    Legacy function: Injects regulation update clauses into sections where keywords match.
    (Kept for compatibility with Contract_Analysis.py if needed)
    """
    new_sections = []
    inserted_any = False

    for heading, content in sections:
        if re.search(r"REGULATION UPDATE APPLIED", content, flags=re.IGNORECASE):
            new_sections.append((heading, content))
            continue

        content_clean = re.split(r"REGULATION UPDATE APPLIED", content, flags=re.IGNORECASE)[0].strip()
        sec_text = f"{heading}\n{content_clean}".lower()
        updates_for_section = ""
        
        for reg in regs:
            added_for_this_reg = False
            for kw in reg.get("keywords", []):
                if kw.lower() in sec_text:
                    updates_for_section += (
                        f"REGULATION UPDATE APPLIED ({reg['date_published']})\n"
                        f"Title: {reg['title']}\n"
                        f"Suggested Update: Parties agree to implement transparency measures regarding {kw}.\n"
                        "--------------------------------------------------------------\n\n"
                    )
                    inserted_any = True
                    added_for_this_reg = True
                    break
            if added_for_this_reg:
                continue

        if updates_for_section:
            new_content = (content_clean + "\n\n" + updates_for_section.strip()).strip()
        else:
            new_content = content_clean

        new_sections.append((heading, new_content))

    return new_sections, inserted_any

def mock_fetch_regulations():
    """
    Fetches a new regulation.
    Cycles through 3 different regulations to make the demo dynamic.
    """
    regs = read_json(REGS_FILE)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    options = [
        {
            "id": f"reg-privacy-{int(time.time())}",
            "title": "New Data Privacy Transparency Rule",
            "jurisdiction": "GLOBAL",
            "date_published": now,
            "summary": "Requires clear privacy notices and transparency about automated profiling.",
            "keywords": ["privacy", "transparency", "profiling", "notice", "personal data"],
            "source_url": "https://example.org/privacy-rule"
        },
        {
            "id": f"reg-ai-{int(time.time())}",
            "title": "AI Algorithmic Accountability Act",
            "jurisdiction": "EU",
            "date_published": now,
            "summary": "Mandates audit trails for AI decisions affecting user termination.",
            "keywords": ["artificial intelligence", "automated decision", "algorithm", "terminate"],
            "source_url": "https://example.org/ai-act"
        },
        {
            "id": f"reg-liab-{int(time.time())}",
            "title": "Digital Services Liability Standard",
            "jurisdiction": "USA",
            "date_published": now,
            "summary": "Prevents unlimited liability clauses in digital service contracts.",
            "keywords": ["liability", "indemnification", "damages", "unlimited"],
            "source_url": "https://example.org/liability-std"
        }
    ]

    existing_titles = [r["title"] for r in regs]
    
    new_reg = None
    for opt in options:
        if opt["title"] not in existing_titles:
            new_reg = opt
            break
            
    if not new_reg:
        return None 

    regs.append(new_reg)
    write_json(REGS_FILE, regs)
    return new_reg

def match_regulation_to_contract(reg, text):
    """
    Returns a score and list of matched keywords.
    """
    matches = []
    for kw in reg.get("keywords", []):
        if kw.lower() in text.lower():
            matches.append(kw)
    return len(matches) * 2, matches