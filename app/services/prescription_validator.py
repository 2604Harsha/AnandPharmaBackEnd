import re
 
def has_doctor_details(text: str) -> bool:
    """
    Returns True ONLY if doctor/hospital/stamp info is present
    """
    if not text:
        return False
 
    patterns = [
        r"\bdr\b",
        r"\bdoctor\b",
        r"\bhospital\b",
        r"\bclinic\b",
        r"\breg\.?\s?no\b",
        r"\bmedical council\b",
        r"\bstamp\b"
    ]
 
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
 
    return False
 
 