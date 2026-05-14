from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FOLDERS = [
    "00_inbox",
    "01_products",
    "02_marketing",
    "03_images",
    "04_smartstore",
    "05_naver_ads",
    "06_apps",
    "07_agents",
    "08_reports",
    "09_approval",
    "10_meetings",
    "11_memory",
    "12_logs",
    "data",
]

def ensure_folders() -> None:
    for folder in FOLDERS:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
