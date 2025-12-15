# utils.py
import os
import json
from config import DATA_DIR, CONTRACTS_DIR, ORIGINALS_DIR, REGS_FILE, CONTRACT_INDEX

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CONTRACTS_DIR, exist_ok=True)
    os.makedirs(ORIGINALS_DIR, exist_ok=True)
    if not os.path.exists(REGS_FILE):
        with open(REGS_FILE, "w") as f:
            json.dump([], f, indent=2)
    if not os.path.exists(CONTRACT_INDEX):
        with open(CONTRACT_INDEX, "w") as f:
            json.dump({}, f, indent=2)

def read_json(path):
    with open(path, "r") as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def next_contract_id():
    idx = read_json(CONTRACT_INDEX)
    existing = len(idx)
    return f"contract_{existing+1:03d}"