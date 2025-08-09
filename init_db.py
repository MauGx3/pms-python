from app.db import Base, engine
from app import models


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized at ./pms.db")
