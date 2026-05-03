from fastapi import UploadFile
from sqlalchemy import select

from app.utils.csv_reader import read_csv_in_chunks
from app.services.validation_service import validate_store_row
from app.services.lookup_service import resolve_store_lookups
from app.db.session import SessionLocal
from app.models.store import Store


async def process_store_file(file: UploadFile):
    results = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "chunks_processed": 0,
        "errors": []
    }

    lookup_cache = {
        "store_brands": {},
        "store_types": {},
        "cities": {},
        "states": {},
        "countries": {},
        "regions": {}
    } # request-scoped cache

    seen_store_ids = set()  # 🔥 in-file dedup

    db = SessionLocal()

    try:
        for chunk in read_csv_in_chunks(file):
            results["chunks_processed"] += 1
            results["total_rows"] += len(chunk)

            valid_rows = []
            chunk_errors = []

            # Step 1: Validation + in-file dedup
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
                valid_rows.append(result)

            results["valid_rows"] += len(valid_rows)
            results["invalid_rows"] += len(chunk_errors)
            results["errors"].extend(chunk_errors)

            if not valid_rows:
                continue

            # Step 2: DB-level dedup
            store_ids = [row["store_id"] for row in valid_rows]

            existing_store_ids = set(
                db.execute(
                    select(Store.store_id).where(Store.store_id.in_(store_ids))
                ).scalars().all()
            )

            # Filter out already existing
            filtered_rows = [
                row for row in valid_rows
                if row["store_id"] not in existing_store_ids
            ]

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

            if store_objects:
                db.bulk_save_objects(store_objects)
                db.commit()

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return results