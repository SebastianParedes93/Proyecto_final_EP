import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # lee el archivo .env

def get_engine():
    url = os.environ["SUPABASE_DB_URL"]
    return create_engine(url, pool_pre_ping=True)