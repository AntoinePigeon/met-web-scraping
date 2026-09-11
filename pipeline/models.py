from sqlalchemy import Boolean, Float, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Artworks(Base):
    __tablename__ = "artworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    highlight: Mapped[bool] = mapped_column(Boolean)
    department: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    culture: Mapped[str | None] = mapped_column(Text)
    medium: Mapped[str | None] = mapped_column(Text)
    classification: Mapped[str | None] = mapped_column(Text)
    dimensions: Mapped[str | None] = mapped_column(Text)
    height_cm: Mapped[float | None] = mapped_column(Float)
    width_cm: Mapped[float | None] = mapped_column(Float)
    depth_cm: Mapped[float | None] = mapped_column(Float)
    number: Mapped[str] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    date: Mapped[str | None] = mapped_column(Text)
    year_start: Mapped[int] = mapped_column(Integer)
    year_end: Mapped[int] = mapped_column(Integer)
    artist_name: Mapped[str | None] = mapped_column(Text)
    artist_role: Mapped[str | None] = mapped_column(Text)
    artist_bio: Mapped[str | None] = mapped_column(Text)
    artist_nationality: Mapped[str | None] = mapped_column(Text)
    artist_birth: Mapped[str | None] = mapped_column(Text)
    artist_death: Mapped[str | None] = mapped_column(Text)
    credit_line: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    county: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    subregion: Mapped[str | None] = mapped_column(Text)
    rights: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str] = mapped_column(Text)
    accession_year: Mapped[int | None] = mapped_column(Integer)
