from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.services.ingestion_service import process_store_file, process_user_file, process_pjp_file
from app.db.session import SessionLocal
from app.models.user import User
from app.models.store import Store
from sqlalchemy import select
import time

router = APIRouter()


@router.post("/upload/stores")
async def upload_stores(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    start_time = time.time()

    result = await process_store_file(file)

    end_time = time.time()

    result["processing_time_seconds"] = round(end_time - start_time, 2)

    print(f"Processing time: {result['processing_time_seconds']} seconds")

    return result


@router.post("/upload/users")
async def upload_users(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    result = await process_user_file(file)
    return result


@router.post("/upload/pjp")
async def upload_pjp(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    db = SessionLocal()
    try:
        has_users = db.execute(select(User.id).limit(1)).first()
        has_stores = db.execute(select(Store.id).limit(1)).first()

        if not has_users or not has_stores:
            raise HTTPException(
                status_code=400,
                detail="Stores and Users must be uploaded before uploading PJP mapping."
            )
    finally:
        db.close()

    result = await process_pjp_file(file)
    return result


@router.get("/download-errors/{filename}")
def download_errors(filename: str):
    return FileResponse(path=filename, filename=filename)