from datetime import datetime
from pathlib import Path

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def write_report(folder: Path, prefix: str, content: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{prefix}_{now_stamp()}.md"
    path.write_text(content, encoding="utf-8")
    return path
