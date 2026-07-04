from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
import os 
import logging
from helper import get_logger, load_state, save_state
from fetch import fetch_emails
from insert import insert_to_db

# Read config from .env
base_path = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_path, ".env"))

STATE_FILE = os.getenv("STATE_FILE",  "state.json")
HOST       = os.getenv("IMAP_HOST")
PORT       = int(os.getenv("IMAP_PORT", 993))
EMAIL_ID   = os.getenv("MAIL_ID")
PASSWORD   = os.getenv("MAIL_PASS")
SINCE_LAST = int(os.getenv("SINCE_LAST_DAYS", 30))
PENDING_DIR = os.getenv("PENDING_DIR", "data/pending")
# insert
BASE_DIR      = Path(__file__).parent
# print(f"BASE_DIR: {BASE_DIR}")

# load_dotenv(dotenv_path=BASE_DIR / ".env")

PENDING_DIR   = os.getenv("PENDING_DIR",   str(BASE_DIR / "data/pending"))
PROCESSED_DIR = os.getenv("PROCESSED_DIR", str(BASE_DIR / "data/processed"))
FAILED_DIR    = os.getenv("FAILED_DIR",    str(BASE_DIR / "data/failed"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PASSWORD  = quote(DB_PASSWORD) if DB_PASSWORD else ""
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "home_expenses")
INSERT_LOG_FILE      = os.getenv("LOG_FILE",      str(BASE_DIR / "inserter.log"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 30))   # seconds
if not DB_PASSWORD:
    raise ValueError("DB_PASS is not set in .env file!")

#set posgres connection string
DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── Directory Setup ───────────────────────────────────────────────────────────
os.makedirs(PENDING_DIR,   exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR,    exist_ok=True)

logger = get_logger("fetcher.log")
insert_logger = get_logger(INSERT_LOG_FILE)
if __name__ == "__main__":
    if not DB_DSN:
        logger.error("❌ DB_DSN is not set in .env file!")
        raise ValueError("DB_DSN is not set in .env file!")
    # fetch emails and save to pending dir
    new_count, skip_count, fail_count = fetch_emails(host =HOST,
                 port=PORT, 
                 user=EMAIL_ID, 
                 password=PASSWORD, 
                 state_file=STATE_FILE,
                 pending_dir=PENDING_DIR,
                 log=logger,
                 since_last=SINCE_LAST)
    logger.info("-" * 60)
    logger.info(f"Done | New: {new_count} | Skipped: {skip_count} | Failed: {fail_count}")
    logger.info("=" * 60)
    logger.info(f"Starting DB insertion process...")
    # insert to db and move files to processed/failed
    insert_to_db(db_dsn=DB_DSN,
                    pending_dir=PENDING_DIR,
                    processed_dir=PROCESSED_DIR,
                    failed_dir=FAILED_DIR,
                    log=insert_logger)
    
    logger.info(f"DB insertion process completed.")