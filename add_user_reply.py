import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Add user_reply column if it doesn't exist
try:
    c.execute("ALTER TABLE claims ADD COLUMN user_reply TEXT")
except sqlite3.OperationalError:
    # Column already exists
    pass

conn.commit()
conn.close()
print("user_reply column added (or already exists).")
