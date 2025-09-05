# Imports models so SQLAlchemy knows about them, then creates tables.
from app.db.session import db
import app.models.link  # noqa: F401

if __name__ == "__main__":
    db.create_all()
    print("✅ tables created")
