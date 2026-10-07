from sqlalchemy import text
from src.db import get_engine

engine = get_engine()

with engine.connect() as conn:
    print(conn.execute(text("select version()")).scalar())
    print(conn.execute(text(
        "select schema_name from information_schema.schemata "
        "where schema_name = 'gold'"
    )).scalar())