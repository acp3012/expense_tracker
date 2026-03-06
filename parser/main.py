from dotenv import load_dotenv
import os 
import logging
from helper import get_logger, load_state, save_state
from fetch import fetch_emails

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

# print(f"STATE_FILE: {STATE_FILE}")
logger = get_logger("fetcher.log")

if __name__ == "__main__":
    fetch_emails(host =HOST,
                 port=PORT, 
                 user=EMAIL_ID, 
                 password=PASSWORD, 
                 state_file=STATE_FILE,
                 pending_dir=PENDING_DIR,
                 log=logger,
                 since_last=SINCE_LAST)
    
