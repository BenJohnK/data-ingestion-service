from fastapi import FastAPI
from app.models.base import Base
from app.db.session import engine
from app.models import lookup, store, user, mapping

app = FastAPI(title="Data Ingestion Service")


@app.get("/")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)