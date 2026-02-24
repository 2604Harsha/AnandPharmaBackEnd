def normalize(text: str) -> str:
    return text.strip().lower() if text else ""


RX_CATEGORIES = {
    "heart care",
    "heartcare",
    "diabetes",
    "diabetes care",
    "neurology",
    "liver care",
    "livercare",
    "kidney",
    "urinary",
    "respiratory",
    "women",
    "men health",
}

RX_KEYWORDS = {
    "antibiotic",
    "insulin",
    "injection",
    "injectable",
    "steroid",
    "capsule",
    "tablet",
    "mg",
}


def is_prescription_required(category: str, name: str, extra_data=None) -> bool:
    cat = normalize(category)
    nm = normalize(name)

    # 1️⃣ Category rule
    for rc in RX_CATEGORIES:
        if rc in cat:
            return True

    # 2️⃣ Keyword rule
    for kw in RX_KEYWORDS:
        if kw in nm:
            return True

    # 3️⃣ JSON safety (seed / pharmacist add)
    if extra_data:
        blob = normalize(str(extra_data))
        if "prescription" in blob or "doctor" in blob:
            return True

    return False
