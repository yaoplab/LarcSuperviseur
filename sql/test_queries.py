import sys
sys.path.insert(0, 'C:/Projets')

from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.logger import log

ok = db.connect_intranet()
print(f'Intranet connected: {ok}')

conn = db.server_conn
cur = conn.cursor()

# 1. Current term
cur.execute("""
    SELECT id FROM larcauth_term
    WHERE start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE
    ORDER BY id LIMIT 1
""")
r = cur.fetchone()
term_id = int(r[0]) if r else 0
print(f'Current term: {term_id}')

# 2. Classes
cur.execute("""
    SELECT c.id, c.label, l.fk_program_id, p.sigle
    FROM larcauth_classroom c
    JOIN larcauth_level l ON l.id = c.fk_level_id
    JOIN larcauth_program p ON p.id = l.fk_program_id
    WHERE c.enabled = TRUE
    ORDER BY p.sigle, c.label
""")
classes = cur.fetchall()
print(f'Classes: {len(classes)}')
for c in classes[:3]:
    print(f'  id={c[0]} label={c[1]} prog={c[3]}')

if not classes:
    print('NO CLASSES FOUND')
    db.disconnect_all()
    exit()

# 3. Group stats
date_from, date_to = '2026-06-01', '2026-06-30'
cur.execute("""
    SELECT c.id, c.label,
           COUNT(DISTINCT se.event_id) AS event_count,
           COUNT(DISTINCT CASE WHEN se.event_type = 'absence' THEN se.event_id END) AS abs_count,
           COUNT(DISTINCT CASE WHEN se.event_type = 'exit' THEN se.event_id END) AS exit_count,
           COUNT(DISTINCT s.aecuser_ptr_id) AS student_count
    FROM larcauth_classroom c
    JOIN larcauth_level l ON l.id = c.fk_level_id
    JOIN larcauth_program p ON p.id = l.fk_program_id
    LEFT JOIN larcauth_student s ON s.s_classroom_id = c.id AND s.enabled = TRUE
    LEFT JOIN student_event se ON se.student_id = s.aecuser_ptr_id
        AND DATE(se.event_at) BETWEEN %s AND %s
    WHERE c.enabled = TRUE
    GROUP BY c.id, c.label
    ORDER BY c.label
    LIMIT 5
""", (date_from, date_to))
rows = cur.fetchall()
print(f'Group stats: {len(rows)} rows')
for r in rows[:3]:
    print(f'  class={r[1]} events={r[2]} abs={r[3]} exit={r[4]} students={r[5]}')

# 4. Students in first class
cid = classes[0][0]
cur.execute("""
    SELECT s.aecuser_ptr_id,
           aec.last_name || ' ' || aec.first_name AS full_name
    FROM larcauth_student s
    JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
    WHERE s.s_classroom_id = %s AND s.enabled = TRUE
    ORDER BY aec.last_name
""", (cid,))
students = cur.fetchall()
print(f'Students for class {cid}: {len(students)}')
for s in students[:3]:
    print(f'  id={s[0]} name={s[1]}')

if students:
    sid = students[0][0]
    cur.execute("""
        SELECT aec.last_name || ' ' || aec.first_name
        FROM larcauth_student s
        JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
        WHERE s.aecuser_ptr_id = %s
    """, (sid,))
    name = cur.fetchone()
    print(f'Student name from EventGenerator query: {name[0]}')

# 5. Timetable
from datetime import datetime
weekday = datetime.now().isoweekday()  # 1=Monday
# Convert to PostgreSQL weekday (0=Monday or 1=Monday depending on schema)
# Using isoweekday (1=Monday, 7=Sunday)
cur.execute("""
    SELECT tp.id, tp.debut, tp.fin, cht.id AS timetable_id
    FROM larcauth_classroom_has_timeperiod cht
    JOIN larcauth_timeperiod tp ON tp.id = cht.fk_timeperiod
    WHERE cht.fk_classroom = %s
      AND cht.fk_weekday = %s
      AND cht.fk_term = %s
    ORDER BY tp.debut
""", (cid, weekday, term_id))
tp_rows = cur.fetchall()
print(f'Timetable slots for class {cid} on weekday {weekday}: {len(tp_rows)}')
for t in tp_rows[:3]:
    print(f'  tp={t[0]} {t[1]}-{t[2]} table_id={t[3]}')

db.disconnect_all()
print('ALL TESTS OK')
