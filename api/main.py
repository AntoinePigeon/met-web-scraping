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
    """A single artwork, shaped for a human reader rather than for machine processing.

Includes the Met's original display strings for dates and dimensions alongside the
parsed numeric columns, since parsing discards qualifiers a reader needs.
"""
    model_config = ConfigDict(from_attributes=True)

    # identity
    id: int
    number: str
    highlight: bool
    department: str
    # description
    name: str | None
    title: str | None
    culture: str | None
    # physical
    medium: str | None
    classification: str | None
    dimensions: str | None
    height_cm: float | None
    width_cm: float | None
    depth_cm: float | None
    # provenance
    date: str | None
    year_start: int
    year_end: int
    # artist
    artist_name: str | None
    credit_line: str | None
    # source metadata
    link: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/artworks/{object_id}", response_model=ArtworkResponse)
def get_artwork(object_id: int, db: Session = Depends(get_db)):
    artwork = db.get(Artworks, object_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork