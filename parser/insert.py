import os
import json
import shutil
import logging
import psycopg2
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import quote
from helper import get_logger

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
print(f"BASE_DIR: {BASE_DIR}")

load_dotenv(dotenv_path=BASE_DIR / ".env")

PENDING_DIR   = os.getenv("PENDING_DIR",   str(BASE_DIR / "data/pending"))
PROCESSED_DIR = os.getenv("PROCESSED_DIR", str(BASE_DIR / "data/processed"))
FAILED_DIR    = os.getenv("FAILED_DIR",    str(BASE_DIR / "data/failed"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PASSWORD  = quote(DB_PASSWORD) if DB_PASSWORD else ""
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "home_expenses")
LOG_FILE      = os.getenv("LOG_FILE",      str(BASE_DIR / "inserter.log"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 30))   # seconds
if not DB_PASSWORD:
    raise ValueError("DB_PASS is not set in .env file!")

#set posgres connection string
DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── Directory Setup ───────────────────────────────────────────────────────────
os.makedirs(PENDING_DIR,   exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR,    exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────

log = get_logger(LOG_FILE)

# ── Validation ────────────────────────────────────────────────────────────────
def validate(data: dict) -> list:
    """Return list of validation errors. Empty list = valid."""
    errors = []
    if not data.get("amount"):
        errors.append("missing amount")
    if not data.get("upi_ref"):
        errors.append("missing upi_ref")
    if not data.get("bank"):
        errors.append("missing bank")
    if not data.get("merchant"):
        errors.append("missing merchant")
    if not data.get("date"):
        errors.append("missing transaction date")
    if not data.get("email_date"):
        errors.append("missing alert_date")
    #DEBUG
    print(f"Validation errors: {errors}")
    return errors


# ── JSON → DB Row Mapper ──────────────────────────────────────────────────────
def is_iso_format(date_str):
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False

def parse_date(date_str: str, date_format: str) -> datetime | None:
    """Safely parse a date string into a datetime object."""
    try:
        if is_iso_format(date_str):
            return datetime.fromisoformat(date_str)
        else:
            return datetime.strptime(date_str, date_format)
    except ValueError:
        print(f"⚠ Warning: Failed to parse date '{date_str}' with format '{date_format}'")
        return None

def parse_txnSign(txn_type: str) -> int:
    """Determine transaction sign based on type."""
    # if txn_type is either debit or dr or withdrawal or paid then return -1 else if credit or cr or received then return +1 else return 0
    if txn_type:
        txn_type = txn_type.lower()
        if any(x in txn_type for x in ["debit", "dr", "withdrawal", "paid"]):
            return -1
        elif any(x in txn_type for x in ["credit", "cr", "received"]):
            return 1
    return 0   
   

def map_to_row(data: dict) -> dict:
    """Map JSON fields to DB column names."""

    # Parse dates safely
    txn_date   = parse_date(data.get("date"), "%Y-%m-%d") # type: ignore
    alert_date = parse_date(data.get("email_date"), "%Y-%m-%dT%H:%M:%S.%f%z") # Updated to handle microseconds
    fetched_at = parse_date(data.get("fetched_at", datetime.now()), "%Y-%m-%dT%H:%M:%S.%f%z") # Updated to handle microseconds
    txn_type =       data.get("type","").lower()
    
    txn_sign  = parse_txnSign(txn_type)
    return {
        "bank":          data.get("bank"),
        "email_id":      data.get("email_id"),
        "amount":        data.get("amount"),
        "currency":      data.get("currency", "INR"),
        "account":       data.get("account"),
        "vpa":           data.get("vpa"),
        "merchant":      data.get("merchant"),
        "txn_date":      txn_date,
        "txn_type":      txn_type,
        "txn_sign":      txn_sign,
        "upi_ref":       data.get("upi_ref"),
        "email_date":    alert_date,
        "email_subject": data.get("email_subject"),
        "fetched_at":    fetched_at,
    }


# ── Process Single File ───────────────────────────────────────────────────────
def process_file(cur, filepath: Path) -> str:
    """
    Process one JSON file.
    Returns: 'inserted' | 'duplicate' | 'skipped' | 'failed'
    """
    filename = filepath.name

    # Load JSON
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log.error(f"❌ Invalid JSON {filename}: {e}")
        return "failed"

    # Validate
    errors = validate(data)
    if errors:
        log.warning(f"⚠ Validation failed {filename}: {errors}")
        return "failed"

    # Map to DB row
    row = map_to_row(data)
    
    # Insert
    try:
        cur.execute("""
        INSERT INTO account_txn_notification (
            email_id,bank, amount, currency, account, merchant,
            txn_date, txn_type, txn_sign, upi_ref, alert_date, alert_subject, fetched_at
        )
        VALUES (
            %(email_id)s, %(bank)s, %(amount)s, %(currency)s, %(account)s, %(merchant)s,
            %(txn_date)s, %(txn_type)s, %(txn_sign)s, %(upi_ref)s, %(email_date)s, %(email_subject)s, %(fetched_at)s
        )
        ON CONFLICT (upi_ref) DO NOTHING;
        """, row)
        # cur.execute(INSERT_SQL, row)
        if cur.rowcount == 0:
            log.info(f"⏭ Duplicate skipped | UPI Ref: {row['upi_ref']}")
            return "duplicate"
        else:
            log.info(f"✓ Inserted | Bank: {row['bank']} | Merchant: {row['merchant']} | Amount: {row['amount']} | Ref: {row['upi_ref']}")
            return "inserted"

    except psycopg2.Error as e:
        log.error(f"❌ DB error {filename}: {e}")
        return "failed"
# end of process_file function

# ── Main Loop ─────────────────────────────────────────────────────────────────
def run():
    # Validate DB config
    if not DB_DSN:
        log.error("❌ DB_DSN is not set in .env file!")
        exit(1)

    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(DB_DSN)
        conn.autocommit = False
        log.info("✓ Connected to PostgreSQL")
    except psycopg2.Error as e:
        log.error(f"❌ Failed to connect to PostgreSQL: {e}")
        exit(1)


    log.info(f"👀 Watching: {PENDING_DIR} every {POLL_INTERVAL}s")
    log.info("Press Ctrl+C to stop")

    import time
    while True:
        # try:
        files = sorted(Path(PENDING_DIR).glob("*.json"))

        if files:
            log.info(f"Found {len(files)} file(s) to process")
            inserted = duplicates = skipped = failed = 0

            for filepath in files:
                cur = conn.cursor()
                result = process_file(cur, filepath)

                if result == "inserted":
                    conn.commit()
                    shutil.move(str(filepath), str(Path(PROCESSED_DIR) / filepath.name))
                    inserted += 1

                elif result == "duplicate":
                    conn.commit()
                    shutil.move(str(filepath), str(Path(PROCESSED_DIR) / filepath.name))
                    duplicates += 1

                elif result == "failed":
                    conn.rollback()
                    shutil.move(str(filepath), str(Path(FAILED_DIR) / filepath.name))
                    failed += 1

                cur.close()

            log.info(f"── Batch done | Inserted: {inserted} | Duplicates: {duplicates} | Failed: {failed}")

        # except KeyboardInterrupt:
        #     log.info("Stopped by user")
        #     break
        # except Exception as e:
        #     log.error(f"❌ Unexpected error: {e}")
        #     conn.rollback()

        time.sleep(POLL_INTERVAL)

    conn.close()
    log.info("DB connection closed")
#end of run function

if __name__ == "__main__":
    run()