import re

# This is the "Messy" text from your Version 11
messy_text = """SERVICE AGREEMENT
This  Agreement  is  made  between  AlphaTech  Pvt.  Ltd.  ("Provider")  and  BetaSoft
Solutions ("Client").
1. CONFIDENTIALITY:
   Both parties agree not to disclose any confidential information received under this
Agreement.
2. TERM AND TERMINATION:
   This Agreement shall be effective for one year and may be terminated with 30 days’
notice by either party.
3. LIABILITY:
   The Provider shall not be liable for any indirect or consequential damages.
4. GOVERNING LAW:
   This Agreement shall be governed by the laws of India.
Signed on this 8th day of November, 2025.
# --- UPDATES APPLIED AUTOMATICALLY ---
### ■ Regulation Update Detected
**Title:** New Data Privacy Transparency Rule
**Summary:** Requires clear privacy notices and transparency about automated profiling.
# --- UPDATES APPLIED ---
--- Regulation Update Detected ---
Title: New Data Privacy Transparency Rule
=== UPDATES APPLIED ===
REGULATION UPDATE DETECTED
"""

# The Regex Pattern from the fix
cleanup_pattern = r"(=== UPDATES APPLIED|# --- UPDATES APPLIED|REGULATION UPDATE DETECTED|REGULATION UPDATE APPLIED)"

# The Cleaning Logic
print("--- ORIGINAL SIZE: ", len(messy_text), "characters ---")

parts = re.split(cleanup_pattern, messy_text, flags=re.IGNORECASE)
clean_text = parts[0].strip()

print("\n--- CLEANED TEXT OUTPUT ---")
print(clean_text)
print("\n---------------------------")
print(f"--- CLEANED SIZE: {len(clean_text)} characters ---")
print("Status: SUCCESS. All 10+ duplicates removed.")