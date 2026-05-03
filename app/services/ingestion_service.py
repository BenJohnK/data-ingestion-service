from fastapi import UploadFile
from app.utils.csv_reader import read_csv_in_chunks
from app.services.validation_service import validate_store_row


async def process_store_file(file: UploadFile):
    results = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "chunks_processed": 0,
        "errors": []
    }

    for chunk in read_csv_in_chunks(file):
        results["chunks_processed"] += 1
        results["total_rows"] += len(chunk)

        valid_rows = []
        chunk_errors = []

        for row_number, row in chunk:
            is_valid, result = validate_store_row(row_number, row)

            if not is_valid:
                chunk_errors.append(result)
            else:
                valid_rows.append(result)

        # Update counters
        results["valid_rows"] += len(valid_rows)
        results["invalid_rows"] += len(chunk_errors)

        # Collect errors (be careful: this can grow large)
        results["errors"].extend(chunk_errors)

        # 🔥 IMPORTANT: DB insert will come later
        # For now we just validate and collect

    return results