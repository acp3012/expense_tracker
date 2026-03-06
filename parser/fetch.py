import imaplib
import email
import json
import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
from helper import load_state
from parser import parse_email
from helper import save_state

# ── Email Body Extractor ───────────────────────────────────────────────────────
def get_email_body(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:                                      # ← check not None
                    body = payload.decode(errors="ignore")
                    break
            # Fallback: try HTML part if no plain text found
            elif part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True)
        if payload:                                              # ← check not None
            body = payload.decode(errors="ignore")
        else:
            # Some emails have plain string payload (not encoded)
            raw = msg.get_payload()
            if isinstance(raw, str):
                body = raw

    return body.strip()


# ── IMAP Date Filter ───────────────────────────────────────────────────────────
def format_imap_date(dt: datetime) -> str:
    """Format datetime to IMAP SINCE date format: 01-Mar-2026"""
    return dt.strftime("%d-%b-%Y")


# ── Main Fetcher ───────────────────────────────────────────────────────────────
def fetch_emails(host,port,user,password, state_file,pending_dir,log, since_last =  30):
    run_time   = datetime.now(timezone.utc)
    
    last_run   =  load_state(state_file)
    if not last_run:
        log.info(f"No previous state found. This looks like the first run. Will fetch emails from the last {since_last} days.")
    else:
        log.info(f"Last successful run was at: {last_run.isoformat()}")
    
    new_count  = 0
    skip_count = 0
    fail_count = 0

    log.info("=" * 60)
    log.info(f"Fetcher started at {run_time.isoformat()}")
    log.info(f"Last run was: {last_run.isoformat() if last_run else 'Never (first run)'}")

    try:
        # Connect to Yahoo IMAP
        log.info(f"Connecting to {host}...")
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        mail.select("INBOX")
        log.info("Connected and authenticated ✓")

        # Build IMAP search query
        # SINCE filters by date (day level), we fine-filter by exact time below
        if last_run:
            since_date   = format_imap_date(last_run)
            search_query = f'(SINCE "{since_date}")'
        else:
            # First run → fetch last 30 days
            since_date   = format_imap_date(run_time - timedelta(days = since_last))
            search_query = f'(SINCE "{since_date}")'

        log.info(f"IMAP search query: {search_query}")
        _, messages = mail.search(None, search_query)

        msg_ids = messages[0].split()
        log.info(f"Found {len(msg_ids)} emails since {since_date}")

        for msg_id in msg_ids:
            try:
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                msg         = email.message_from_bytes(msg_data[0][1]) # type: ignore

                sender      = msg.get("From",    "")
                subject     = msg.get("Subject", "")
                date_header = msg.get("Date",    "")

                # Parse email date for exact time comparison
                try:
                    email_dt = parsedate_to_datetime(date_header)
                    if email_dt.tzinfo is None:
                        email_dt = email_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    email_dt = None

                # Fine-grained filter: skip emails before last_run exact time
                if last_run and email_dt and email_dt <= last_run:
                    skip_count += 1
                    continue

                body   = get_email_body(msg)
                parsed = parse_email(body, sender=sender, subject=subject, email_id=user)

                if not parsed:
                    log.warning(f"Unknown bank — skipped | From: {sender} | Subject: {subject}")
                    skip_count += 1
                    continue

                if not parsed.get("amount"):
                    log.warning(f"No amount found — skipped | Bank: {parsed.get('bank')} | Subject: {subject}")
                    skip_count += 1
                    continue

                if not parsed.get("upi_ref"):
                    log.warning(f"No UPI ref found — skipped | Bank: {parsed.get('bank')}")
                    skip_count += 1
                    continue

                # Save JSON to pending folder
                filename = f"{pending_dir}/{parsed['upi_ref']}.json"

                if os.path.exists(filename):
                    log.info(f"Already exists — skipped: {parsed['upi_ref']}")
                    skip_count += 1
                    continue

                # Add email metadata to JSON
                parsed["email_date"]    = email_dt.isoformat() if email_dt else None
                parsed["email_subject"] = subject
                parsed["fetched_at"]    = run_time.isoformat()

                with open(filename, "w") as f:
                    json.dump(parsed, f, indent=2)

                log.info(f"✓ Saved | Bank: {parsed['bank']} | Merchant: {parsed['merchant']} | Amount: {parsed['amount']} | Ref: {parsed['upi_ref']}")
                new_count += 1

            except Exception as e:
                log.error(f"Error processing message {msg_id}: {e}")
                fail_count += 1
                continue

        mail.logout()
        # Save state only if run was successful
        try:
            if (save_state(state_file, run_time, log)):
                log.info(f"✓ State saved at: {state_file}")
                log.info(f"✓ Last run set to: {run_time.isoformat()}")
        except Exception as e:
            log.error(f"❌ Failed to save state: {e}")
            log.error(f"❌ Tried to write to: {state_file}")

    except imaplib.IMAP4.error as e:
        log.error(f"IMAP error: {e}")
        return
    except Exception as e:
        log.error(f"Unexpected error: {e}")
    

    

    log.info("-" * 60)
    log.info(f"Done | New: {new_count} | Skipped: {skip_count} | Failed: {fail_count}")
    log.info("=" * 60)


