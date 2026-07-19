from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Text


class Base(DeclarativeBase):
    pass


class Artworks(Base):
    __tablename__ = "artworks"

    object_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    object_number: Mapped[str] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(Text)
    maker: Mapped[str | None] = mapped_column(Text)
    date: Mapped[str] = mapped_column(Text)
    year_start: Mapped[int] = mapped_column(Integer)
    geography: Mapped[str | None] = mapped_column(Text)
    culture: Mapped[str | None] = mapped_column(Text)
    medium: Mapped[str] = mapped_column(Text)
    dimensions: Mapped[str | None] = mapped_column(Text)
    height_cm: Mapped[float | None] = mapped_column(Float)
    width_cm: Mapped[float | None] = mapped_column(Float)
    depth_cm: Mapped[float | None] = mapped_column(Float)
    credit_line: Mapped[str] = mapped_column(Text)
    curatorial_department: Mapped[str] = mapped_column(Text)