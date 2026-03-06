from dotenv import load_dotenv
import os 
import logging
from  datetime import datetime
import json
# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

IMAP_HOST  = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
YAHOO_USER  = os.getenv("YAHOO_USER")
YAHOO_PASS  = os.getenv("YAHOO_PASS")
PENDING_DIR = os.getenv("PENDING_DIR", "data/pending")
STATE_FILE  = os.getenv("STATE_FILE",  "state.json")
LOG_FILE    = os.getenv("LOG_FILE",    "fetcher.log")

os.makedirs(PENDING_DIR, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
def get_logger(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()         # also print to terminal
        ]
    )
    return logging.getLogger(__name__)

# ── State Management (last run timestamp) ─────────────────────────────────────
def load_state(state_file ) -> datetime | None:
    """Read last successful run time from state.json"""
    if not os.path.exists(state_file):
        return None
    try:
        with open(state_file) as f:
            data = json.load(f)
        ts = data.get("last_run")
        if ts:
            dt = datetime.fromisoformat(ts)
            # log.info(f"✓ State loaded: last_run = {dt.isoformat()}")
            return dt
    except Exception as e:
        raise IOError(f"Failed to read state file: {e}")
    return None


def save_state(file_name:str,dt: datetime, log: logging.Logger):
    """Save current run time to state.json"""
    try:
        with open(file_name, "w") as f:
            json.dump({"last_run": dt.isoformat()}, f, indent=2)
            return True
    except Exception as e:
        raise IOError(f"Failed to write state file: {e}")
        