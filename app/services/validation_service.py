import re

ALLOWED_USER_TYPES = {1, 2, 3, 7}


def validate_email(field_name, value, errors):
    if value:
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, value):
            errors.append((field_name, "Invalid email format"))


def validate_user_type(field_name, value, errors):
    try:
        val = int(value)
        if val not in ALLOWED_USER_TYPES:
            errors.append((field_name, "Invalid user_type"))
    except (ValueError, TypeError):
        errors.append((field_name, "Invalid user_type"))


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


def validate_user_row(row_number, row):
    errors = []

    # Required
    validate_required("username", row.get("username"), errors)
    validate_required("email", row.get("email"), errors)

    # Length
    validate_length("username", row.get("username"), 150, errors)
    validate_length("first_name", row.get("first_name"), 150, errors)
    validate_length("last_name", row.get("last_name"), 150, errors)
    validate_length("email", row.get("email"), 254, errors)
    validate_length("phone_number", row.get("phone_number"), 32, errors)

    # Email
    validate_email("email", row.get("email"), errors)

    # User type
    if row.get("user_type"):
        validate_user_type("user_type", row.get("user_type"), errors)

    # Boolean
    if row.get("is_active"):
        validate_boolean("is_active", row.get("is_active"), errors)

    if errors:
        return False, {
            "row": row_number,
            "errors": [{"field": f, "message": m} for f, m in errors]
        }

    # Cleaned data
    cleaned_data = {
        "username": row.get("username").strip(),
        "first_name": row.get("first_name", "").strip(),
        "last_name": row.get("last_name", "").strip(),
        "email": row.get("email").strip().lower(),
        "user_type": int(row.get("user_type") or 1),
        "phone_number": row.get("phone_number", "").strip(),
        "supervisor_username": row.get("supervisor_username", "").strip(),
        "is_active": str(row.get("is_active", "true")).lower() in ("true", "1")
    }

    return True, cleaned_data