import aitsm.models  # noqa: F401  - registers every table on Base.metadata
from aitsm.core.database import Base, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    created = sorted(Base.metadata.tables)
    if not created:
        raise RuntimeError("No table registered on Base.metadata: models were not imported.")
    print(f"Database tables created: {', '.join(created)}")


main()
