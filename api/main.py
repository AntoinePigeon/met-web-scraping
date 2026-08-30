from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from api.db import get_db
from pipeline.models import Artworks

app = FastAPI(
    title="Met Museum API",
    description="an ETL pipeline feeding a real API over CC0 Met data",
    version="0.1.0",
)
class ArtworkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    object_id: int
    title: str
    maker: str | None
    date: str
    year_start: int
    medium: str
    dimensions: str | None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/artworks/{object_id}", response_model=ArtworkResponse)
def get_artwork(object_id: int, db: Session = Depends(get_db)):
    artwork = db.get(Artworks, object_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork