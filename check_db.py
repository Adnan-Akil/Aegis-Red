import sqlite3

db = sqlite3.connect("data/framework.db")
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])

for table_name in [t[0] for t in tables]:
    count = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  {table_name}: {count} rows")
