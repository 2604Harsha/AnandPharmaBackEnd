
DOCTOR_KEYWORDS = [
    "dr.",
    "doctor",
    "mbbs",
    "md",
    "bams",
    "bhms",
    "consultant"
]


def has_doctor_details(text: str) -> bool:
    """
    NEW RULE:

    REQUIRED:
    ✅ Doctor identity must exist

    OPTIONAL (ignored):
    ❌ Hospital
    ❌ Stamp
    ❌ Signature

    If doctor missing → reject
    """

    if not text:
        return False

    text_lower = text.lower()

    doctor_found = any(keyword in text_lower for keyword in DOCTOR_KEYWORDS)

    return doctor_found
