import re


def normalize_vehicle_number(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()
    return cleaned


def validate_vehicle_number(value: str) -> bool:
    value = normalize_vehicle_number(value)
    if not value:
        return False
    if re.fullmatch(r"[A-Z]{2,3}[0-9]{1,2}[A-Z]{0,2}[0-9]{2,4}", value):
        return True
    if re.fullmatch(r"[A-Z]{1,3}[0-9]{1,4}", value):
        return True
    return False


def validate_required_fields(*fields):
    for field in fields:
        if field is None or str(field).strip() == "":
            return False
    return True
