import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ---- logging setup (runs once) ---- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---- paths ---- #
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "data" / "raw_artworks.json"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# ---- scraping headers ---- #
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ---- database ---- #
load_dotenv(BASE_DIR / ".env")
engine = create_engine(os.getenv("DATABASE_URL"))