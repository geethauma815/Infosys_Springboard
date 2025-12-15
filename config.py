# config.py
import os

DATA_DIR = "data"
REGS_FILE = os.path.join(DATA_DIR, "regulations.json")
CONTRACTS_DIR = os.path.join(DATA_DIR, "contracts")
ORIGINALS_DIR = os.path.join(CONTRACTS_DIR, "originals")
CONTRACT_INDEX = os.path.join(DATA_DIR, "contracts_index.json")