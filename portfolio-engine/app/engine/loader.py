import json
import os
from typing import Dict, Any


def load_parsed_cas(file_path: str) -> Dict[str, Any]:
    """
    Loads and validates the parsed CAS JSON file.
    Returns a Python dictionary containing the raw folio data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Parsed CAS file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if "folios" not in data:
        raise ValueError(f"Invalid format: 'folios' key missing in {file_path}")
        
    return data
