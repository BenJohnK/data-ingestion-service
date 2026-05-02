from fastapi import UploadFile
from app.utils.csv_reader import read_csv_in_chunks


async def process_store_file(file: UploadFile):
    results = {
        "total_rows": 0,
        "chunks_processed": 0
    }

    for chunk in read_csv_in_chunks(file):
        results["chunks_processed"] += 1
        results["total_rows"] += len(chunk)

    return results