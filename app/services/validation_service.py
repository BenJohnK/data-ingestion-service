import re

ALLOWED_USER_TYPES = {1, 2, 3, 7}


def normalize_string(value: str):
    if value is None:
        return None
    return value.strip().lower()


def validate_required(field_name, value, errors):
    if value is None or str(value).strip() == "":
        errors.append((field_name, "This field is required"))


def validate_length(field_name, value, max_length, errors):
    if value and len(value) > max_length:
        errors.append((field_name, f"Max length exceeded ({max_length})"))


def validate_float(field_name, value, errors):
    try:
        float(value)
    except (ValueError, TypeError):
        errors.append((field_name, "Invalid float value"))


def validate_boolean(field_name, value, errors):
    if str(value).lower() not in {"true", "false", "1", "0"}:
        errors.append((field_name, "Invalid boolean value"))


def validate_store_row(row_number, row):
    errors = []

    # Required fields
    validate_required("store_id", row.get("store_id"), errors)
    validate_required("name", row.get("name"), errors)
    validate_required("title", row.get("title"), errors)

    # Length checks
    validate_length("store_id", row.get("store_id"), 255, errors)
    validate_length("name", row.get("name"), 255, errors)
    validate_length("title", row.get("title"), 255, errors)

    # Float fields
    if row.get("latitude"):
        validate_float("latitude", row.get("latitude"), errors)

    if row.get("longitude"):
        validate_float("longitude", row.get("longitude"), errors)

    # Boolean
    if row.get("is_active"):
        validate_boolean("is_active", row.get("is_active"), errors)

    if errors:
        return False, {
            "row": row_number,
            "errors": [{"field": f, "message": m} for f, m in errors]
        }

    # Normalize data (important for lookup later)
    cleaned_data = {
        "store_id": row.get("store_id").strip(),
        "store_external_id": row.get("store_external_id", "").strip(),
        "name": row.get("name").strip(),
        "title": row.get("title").strip(),
        "store_brand": normalize_string(row.get("store_brand")),
        "store_type": normalize_string(row.get("store_type")),
        "city": normalize_string(row.get("city")),
        "state": normalize_string(row.get("state")),
        "country": normalize_string(row.get("country")),
        "region": normalize_string(row.get("region")),
        "latitude": float(row.get("latitude") or 0.0),
        "longitude": float(row.get("longitude") or 0.0),
        "is_active": str(row.get("is_active", "true")).lower() in ("true", "1")
    }

    return True, cleaned_data