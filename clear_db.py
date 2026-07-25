import sqlite3

db = sqlite3.connect("data/framework.db")

# Show before state
for table in ["targets", "attack_attempts", "evaluation_results", "vulnerability_findings"]:
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  BEFORE | {table}: {count} rows")

# Clear all tables
db.execute("DELETE FROM vulnerability_findings")
db.execute("DELETE FROM evaluation_results")
db.execute("DELETE FROM attack_attempts")
db.execute("DELETE FROM targets")
db.commit()

# Show after state
print()
for table in ["targets", "attack_attempts", "evaluation_results", "vulnerability_findings"]:
    count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  AFTER  | {table}: {count} rows")

db.close()
print("\nDone. framework.db is clean.")
