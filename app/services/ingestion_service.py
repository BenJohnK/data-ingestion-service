from fastapi import UploadFile
from sqlalchemy import select
from app.utils.csv_reader import read_csv_in_chunks
from app.services.validation_service import validate_store_row
from app.services.lookup_service import resolve_store_lookups
from app.db.session import SessionLocal
from app.models.store import Store
from app.models.user import User
from app.services.validation_service import validate_user_row
from app.services.validation_service import validate_pjp_row
from app.models.mapping import PermanentJourneyPlan
from sqlalchemy import select, tuple_
import csv
from datetime import datetime


async def process_store_file(file: UploadFile):
    results = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "chunks_processed": 0,
    }

    # Create error CSV file
    error_filename = f"errors_store_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    error_file = open(error_filename, "w", newline="")
    error_writer = csv.writer(error_file)
    error_writer.writerow(["row", "field", "message"])

    # Request-scoped in-memory cache (name -> id) to avoid repeated DB lookups
    # for reference tables (store_brand, city, etc.) within a single ingestion request.
    lookup_cache = {
        "store_brands": {},
        "store_types": {},
        "cities": {},
        "states": {},
        "countries": {},
        "regions": {}
    }

    seen_store_ids = set()

    db = SessionLocal()

    try:
        for chunk in read_csv_in_chunks(file):
            results["chunks_processed"] += 1
            results["total_rows"] += len(chunk)

            valid_rows = []
            chunk_errors = []

            # =========================
            # Step 1: Validation + in-file dedup
            # =========================
            for row_number, row in chunk:
                is_valid, result = validate_store_row(row_number, row)

                if not is_valid:
                    chunk_errors.append(result)
                    continue

                store_id = result["store_id"]

                if store_id in seen_store_ids:
                    chunk_errors.append({
                        "row": row_number,
                        "errors": [{"field": "store_id", "message": "Duplicate in file"}]
                    })
                    continue

                seen_store_ids.add(store_id)
                valid_rows.append((row_number, result))  # keep row_number

            # =========================
            # Write validation errors to CSV
            # =========================
            for err in chunk_errors:
                row_num = err.get("row")
                for e in err["errors"]:
                    error_writer.writerow([row_num, e["field"], e["message"]])

            results["invalid_rows"] += len(chunk_errors)

            if not valid_rows:
                continue

            # =========================
            # Step 2: DB-level dedup
            # =========================
            store_ids = [row["store_id"] for _, row in valid_rows]

            existing_store_ids = set(
                db.execute(
                    select(Store.store_id).where(Store.store_id.in_(store_ids))
                ).scalars().all()
            )

            filtered_rows = []
            db_duplicate_errors = []

            for row_number, row in valid_rows:
                if row["store_id"] in existing_store_ids:
                    db_duplicate_errors.append({
                        "row": row_number,
                        "errors": [{"field": "store_id", "message": "Already exists in DB"}]
                    })
                else:
                    filtered_rows.append(row)

            # Write DB duplicate errors
            for err in db_duplicate_errors:
                for e in err["errors"]:
                    error_writer.writerow([err["row"], e["field"], e["message"]])

            results["invalid_rows"] += len(db_duplicate_errors)

            if not filtered_rows:
                continue

            # =========================
            # Step 3: Create ORM objects
            # =========================
            store_objects = []

            for clean_row in filtered_rows:
                lookup_ids = resolve_store_lookups(db, clean_row, lookup_cache)

                store = Store(
                    store_id=clean_row["store_id"],
                    store_external_id=clean_row["store_external_id"],
                    name=clean_row["name"],
                    title=clean_row["title"],
                    latitude=clean_row["latitude"],
                    longitude=clean_row["longitude"],
                    is_active=clean_row["is_active"],
                    **lookup_ids
                )

                store_objects.append(store)

            # =========================
            # Step 4: Bulk insert
            # =========================
            if store_objects:
                db.bulk_save_objects(store_objects)
                db.commit()

                results["valid_rows"] += len(store_objects)

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()
        error_file.close()

    # Return file reference instead of huge JSON
    results["error_file"] = error_filename

    return results


async def process_user_file(file: UploadFile):
    results = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "chunks_processed": 0,
    }

    # Error CSV
    error_filename = f"errors_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    error_file = open(error_filename, "w", newline="")
    error_writer = csv.writer(error_file)
    error_writer.writerow(["row", "field", "message"])

    seen_usernames = set()

    # store only required mappings WITH row number
    supervisor_mappings = []

    db = SessionLocal()

    try:
        # =========================
        # Phase 1: Insert users
        # =========================
        for chunk in read_csv_in_chunks(file):
            results["chunks_processed"] += 1
            results["total_rows"] += len(chunk)

            valid_rows = []
            chunk_errors = []

            for row_number, row in chunk:
                is_valid, result = validate_user_row(row_number, row)

                if not is_valid:
                    chunk_errors.append(result)
                    continue

                username = result["username"]

                if username in seen_usernames:
                    chunk_errors.append({
                        "row": row_number,
                        "errors": [{"field": "username", "message": "Duplicate in file"}]
                    })
                    continue

                seen_usernames.add(username)
                valid_rows.append((row_number, result))  # keep row_number

            # write validation errors
            for err in chunk_errors:
                row_num = err.get("row")
                for e in err["errors"]:
                    error_writer.writerow([row_num, e["field"], e["message"]])

            results["invalid_rows"] += len(chunk_errors)

            if not valid_rows:
                continue

            # =========================
            # DB-level dedup
            # =========================
            usernames = [row["username"] for _, row in valid_rows]

            existing_usernames = set(
                db.execute(
                    select(User.username).where(User.username.in_(usernames))
                ).scalars().all()
            )

            filtered_rows = []
            db_duplicate_errors = []

            for row_number, row in valid_rows:
                if row["username"] in existing_usernames:
                    db_duplicate_errors.append({
                        "row": row_number,
                        "errors": [{"field": "username", "message": "Already exists in DB"}]
                    })
                else:
                    filtered_rows.append((row_number, row))

            # write DB duplicate errors
            for err in db_duplicate_errors:
                for e in err["errors"]:
                    error_writer.writerow([err["row"], e["field"], e["message"]])

            results["invalid_rows"] += len(db_duplicate_errors)

            if not filtered_rows:
                continue

            # =========================
            # Insert users
            # =========================
            user_objects = []

            for row_number, clean_row in filtered_rows:
                user = User(
                    username=clean_row["username"],
                    first_name=clean_row["first_name"],
                    last_name=clean_row["last_name"],
                    email=clean_row["email"],
                    user_type=clean_row["user_type"],
                    phone_number=clean_row["phone_number"],
                    is_active=clean_row["is_active"],
                    supervisor_id=None
                )

                user_objects.append(user)

                # store mapping WITH row_number
                if clean_row.get("supervisor_username"):
                    supervisor_mappings.append((
                        row_number,
                        clean_row["username"],
                        clean_row["supervisor_username"]
                    ))

            db.bulk_save_objects(user_objects)
            db.commit()

            results["valid_rows"] += len(user_objects)

        # =========================
        # Phase 2: Resolve supervisors
        # =========================
        if supervisor_mappings:
            usernames_needed = set()

            for _, username, supervisor_username in supervisor_mappings:
                usernames_needed.add(username)
                usernames_needed.add(supervisor_username)

            users = db.execute(
                select(User.id, User.username).where(User.username.in_(usernames_needed))
            ).all()

            username_to_id = {username: user_id for user_id, username in users}

            updates = []

            for row_number, username, supervisor_username in supervisor_mappings:
                user_id = username_to_id.get(username)
                supervisor_id = username_to_id.get(supervisor_username)

                if user_id:
                    updates.append({
                        "id": user_id,
                        "supervisor_id": supervisor_id
                    }) # As of now, if the supervisor_id is not found, the user row is not counted as invalid and it is also stored in the user table with supervisor_id as NULL.

            if updates:
                db.bulk_update_mappings(User, updates)
                db.commit()

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()
        error_file.close()

    results["error_file"] = error_filename

    return results


async def process_pjp_file(file: UploadFile):
    results = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "chunks_processed": 0,
    }

    # Error CSV
    error_filename = f"errors_pjp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    error_file = open(error_filename, "w", newline="")
    error_writer = csv.writer(error_file)
    error_writer.writerow(["row", "field", "message"])

    seen_keys = set()  # (username, store_id, date)

    db = SessionLocal()

    try:
        for chunk in read_csv_in_chunks(file):
            results["chunks_processed"] += 1
            results["total_rows"] += len(chunk)

            valid_rows = []
            chunk_errors = []

            # =========================
            # Step 1: validation + in-file dedup
            # =========================
            for row_number, row in chunk:
                is_valid, result = validate_pjp_row(row_number, row)

                if not is_valid:
                    chunk_errors.append(result)
                    continue

                key = (result["username"], result["store_id"], result["date"])

                if key in seen_keys:
                    chunk_errors.append({
                        "row": row_number,
                        "errors": [{"field": "duplicate", "message": "Duplicate in file"}]
                    })
                    continue

                seen_keys.add(key)
                valid_rows.append((row_number, result))

            # write validation errors
            for err in chunk_errors:
                row_num = err.get("row")
                for e in err["errors"]:
                    error_writer.writerow([row_num, e["field"], e["message"]])

            results["invalid_rows"] += len(chunk_errors)

            if not valid_rows:
                continue

            # =========================
            # Step 2: bulk resolve users + stores
            # =========================
            usernames = list({row["username"] for _, row in valid_rows})
            store_ids = list({row["store_id"] for _, row in valid_rows})

            users = db.execute(
                select(User.id, User.username).where(User.username.in_(usernames))
            ).all()

            stores = db.execute(
                select(Store.id, Store.store_id).where(Store.store_id.in_(store_ids))
            ).all()

            username_to_id = {u.username: u.id for u in users}
            storeid_to_pk = {s.store_id: s.id for s in stores}

            # =========================
            # Step 3: resolve + filter invalid references
            # =========================
            resolved_rows = []
            resolution_errors = []

            for row_number, row in valid_rows:
                user_id = username_to_id.get(row["username"])
                store_pk = storeid_to_pk.get(row["store_id"])

                if not user_id:
                    resolution_errors.append({
                        "row": row_number,
                        "errors": [{"field": "username", "message": "User not found"}]
                    })
                    continue

                if not store_pk:
                    resolution_errors.append({
                        "row": row_number,
                        "errors": [{"field": "store_id", "message": "Store not found"}]
                    })
                    continue

                resolved_rows.append((
                    row_number,
                    {
                        "user_id": user_id,
                        "store_id": store_pk,
                        "date": row["date"],
                        "is_active": row["is_active"]
                    }
                ))

            # write resolution errors
            for err in resolution_errors:
                for e in err["errors"]:
                    error_writer.writerow([err["row"], e["field"], e["message"]])

            results["invalid_rows"] += len(resolution_errors)

            if not resolved_rows:
                continue

            # =========================
            # Step 4: DB-level dedup
            # =========================
            keys = [
                (r["user_id"], r["store_id"], r["date"])
                for _, r in resolved_rows
            ]

            existing = set(
                db.execute(
                    select(
                        PermanentJourneyPlan.user_id,
                        PermanentJourneyPlan.store_id,
                        PermanentJourneyPlan.date
                    ).where(
                        tuple_(
                            PermanentJourneyPlan.user_id,
                            PermanentJourneyPlan.store_id,
                            PermanentJourneyPlan.date
                        ).in_(keys)
                    )
                ).all()
            )

            filtered_rows = []
            db_duplicate_errors = []

            for row_number, r in resolved_rows:
                key = (r["user_id"], r["store_id"], r["date"])
                if key in existing:
                    db_duplicate_errors.append({
                        "row": row_number,
                        "errors": [{"field": "duplicate", "message": "Already exists in DB"}]
                    })
                else:
                    filtered_rows.append(r)

            # write DB duplicate errors
            for err in db_duplicate_errors:
                for e in err["errors"]:
                    error_writer.writerow([err["row"], e["field"], e["message"]])

            results["invalid_rows"] += len(db_duplicate_errors)

            if not filtered_rows:
                continue

            # =========================
            # Step 5: bulk insert
            # =========================
            pjp_objects = [
                PermanentJourneyPlan(**row)
                for row in filtered_rows
            ]

            if pjp_objects:
                db.bulk_save_objects(pjp_objects)
                db.commit()

                results["valid_rows"] += len(pjp_objects)

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()
        error_file.close()

    results["error_file"] = error_filename

    return results