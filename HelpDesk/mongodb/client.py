import os

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()

DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

client = AsyncMongoClient(
    f"mongodb://{DB_USER}:{DB_PASSWORD}@localhost:27017/"
    "?directConnection=true&authSource=admin"
)