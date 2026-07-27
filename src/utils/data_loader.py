import json
from pathlib import Path
from typing import Any

def load_json(relative_path: str) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root / relative_path
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)
