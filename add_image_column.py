import sqlite3

# Connect to your existing database
conn = sqlite3.connect("database.db")
c = conn.cursor()

# Add a new column named 'image' (only runs once)
try:
    c.execute("ALTER TABLE items ADD COLUMN image TEXT;")
    print("✅ Column 'image' added successfully!")
except sqlite3.OperationalError as e:
    print("⚠️ Skipping -", e)

conn.commit()
conn.close()
