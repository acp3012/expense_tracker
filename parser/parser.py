import re, yaml
from datetime import datetime

with open("bank_templates.yaml") as f:
    TEMPLATES = yaml.safe_load(f)["banks"]


def identify_bank(sender: str, subject: str) -> str | None:
    """Match email sender/subject to a bank template."""
    for bank_name, config in TEMPLATES.items():
        rule = config.get("identify_by", {})
        if "sender_contains" in rule:
            if rule["sender_contains"].lower() in sender.lower():
                return bank_name
        if "subject_contains" in rule:
            if rule["subject_contains"].lower() in subject.lower():
                return bank_name
    return None


def extract_field(body: str, field_config: dict) -> str | None:
    """Extract a single field using its pattern config."""
    pattern = field_config.get("pattern")
    if not pattern:
        return None

    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None

    value = match.group(1).strip()

    # Remove unwanted characters (e.g. commas in "1,500.00")
    if "remove_chars" in field_config:
        for char in field_config["remove_chars"]:
            value = value.replace(char, "")

    return value


def parse_email(body: str, sender: str, subject: str = "", email_id: str = "") -> dict | None:
    """Main entry point — identify bank and extract all fields."""
    bank = identify_bank(sender, subject)
    if not bank:
        print(f"⚠ Unknown bank for sender: {sender}")
        return None

    template = TEMPLATES[bank]["fields"]
    result = {"bank": bank, "currency": "INR", "email_id": email_id}

    # --- Amount ---
    raw_amount = extract_field(body, template["amount"])
    result["amount"] = float(raw_amount) if raw_amount else None

    # --- Account ---
    result["account"] = extract_field(body, template.get("account", {}))

    # --- Merchant ---
    result["merchant"] = extract_field(body, template.get("merchant", {}))

    # --- UPI Ref ---
    result["upi_ref"] = extract_field(body, template.get("upi_ref", {}))

    # --- Date ---
    date_config = template.get("date", {})
    raw_date = extract_field(body, date_config)
    if raw_date and "format" in date_config:
        try:
            result["date"] = datetime.strptime(raw_date, date_config["format"]).strftime("%Y-%m-%d")
        except ValueError:
            result["date"] = raw_date
    else:
        result["date"] = raw_date

    # --- Txn Type ---
    txn_config = template.get("txn_type", {})
    if txn_config.get("debit_if_contains", "").lower() in body.lower():
        result["type"] = "debit"
    elif txn_config.get("credit_if_contains", "").lower() in body.lower():
        result["type"] = "credit"
    else:
        result["type"] = "unknown"

    return result





