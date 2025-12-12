# app/evals/run_all.py

import sys
from pathlib import Path
import pytest

# Add project root to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[2]  # twin_engine/
sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    raise SystemExit(pytest.main(["app/evals", "-q"]))