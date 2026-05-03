from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ingestion_service import process_store_file, process_user_file, process_pjp_file

router = APIRouter()


@router.post("/upload/stores")
async def upload_stores(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    result = await process_store_file(file)
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

    result = await process_pjp_file(file)

    return result