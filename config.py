from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "college_xi_d1.sqlite3"
SEASON = 2026
DIVISION = "D1"
PORT = int(os.getenv("PORT", "5012"))
HOST = os.getenv("HOST", "127.0.0.1")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 8
REQUEST_DELAY_SECONDS = 0.18
FANTASY_BUDGET = 120.0
