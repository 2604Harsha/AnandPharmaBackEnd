import uuid
from datetime import datetime

def generate_payment_id() -> str:
    date_part = datetime.utcnow().strftime("%Y%m%d")
    rand = uuid.uuid4().hex[:8].upper()
    return f"PAY-{date_part}-{rand}"
