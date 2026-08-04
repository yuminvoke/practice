from pymongo import AsyncMongoClient

client = AsyncMongoClient("mongodb://localhost:27017/?directConnection=true")