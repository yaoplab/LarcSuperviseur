import sys, os
sys.path.insert(0, 'C:\\Projets\\eLarcProfPy')
sys.path.insert(0, 'C:\\Projets\\LarcCommon')
from larccommon.database import db

if not db.connect_intranet():
    print("ERREUR : connexion Intranet impossible")
    sys.exit(1)

conn = db.server_conn
cur = conn.cursor()

# Lire le DDL
ddl_path = os.path.join(os.path.dirname(__file__), 'student_event.sql')
with open(ddl_path, encoding='utf-8') as f:
    sql = f.read()

# Exécuter chaque instruction (séparées par ;)
statements = [s.strip() for s in sql.split(';') if s.strip()]
ok = 0
for stmt in statements:
    try:
        cur.execute(stmt)
        ok += 1
        print(f"  OK: {stmt[:60]}...")
    except Exception as e:
        print(f"  SKIP: {e}")

print(f"\n{ok}/{len(statements)} instructions exécutées")
db.disconnect_all()
