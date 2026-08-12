import sys
import sqlite3
from database import DatabaseManager

db = DatabaseManager()
results = db.search_products("1", limit=15)
print("Results:", results)
