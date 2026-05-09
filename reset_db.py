import os
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'store.db')
if os.path.exists(db_path):
    os.remove(db_path)
from application import init_db
init_db()
print("Database reset!")
