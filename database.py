from sqlalchemy.dialects.postgresql import insert
from config import engine, logger
from models import Base, Artworks


def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(engine)


def load_records(records):
    """Upsert records into the artworks table (idempotent)."""
    stmt = insert(Artworks).values(records)

    update_columns = [col for col in Artworks.__table__.columns.keys() if col != "object_id"]
    stmt = stmt.on_conflict_do_update(
        index_elements=["object_id"],
        set_={col: stmt.excluded[col] for col in update_columns},
    )

    with engine.begin() as conn:
        conn.execute(stmt)

    logger.info(f"Upserted {len(records)} records!")