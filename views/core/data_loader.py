from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.logger import log


class DataLoader:
    """All database queries in one place."""

    # ------------------------------------------------------------------
    # Connexion
    # ------------------------------------------------------------------
    @property
    def conn(self):
        return db.server_conn

    def _cursor(self):
        c = self.conn
        if not c:
            raise ConnectionError("Aucune connexion base de données.")
        return c.cursor()

    # ------------------------------------------------------------------
    # Terme actif
    # ------------------------------------------------------------------
    def get_active_term(self) -> int:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT id FROM larcauth_term
                WHERE start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE
                LIMIT 1
            """)
            r = cur.fetchone()
            return int(r[0]) if r else 0
        except Exception as e:
            log(f"DataLoader.get_active_term: {e}")
            return 0

    def get_term_id(self) -> int:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT t.id FROM larcauth_term t, larcauth_academicyear ay
                WHERE ay.s_id = 1 AND t.trim = ay.current_term_number
                ORDER BY t.id LIMIT 1
            """)
            r = cur.fetchone()
            return r[0] if r else 0
        except Exception as e:
            log(f"DataLoader.get_term_id: {e}")
            return 0

    def get_current_term_label(self) -> str:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT t.label
                FROM larcauth_term t, larcauth_academicyear ay
                WHERE ay.s_id = 1 AND t.trim = ay.current_term_number
                LIMIT 1
            """)
            r = cur.fetchone()
            return r[0] if r else ""
        except Exception as e:
            log(f"DataLoader.get_current_term_label: {e}")
            return ""

    def get_unit_periods(self) -> list[dict]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT up.id, up.unit_nr, up.label, up.start_date, up.end_date,
                       up.fk_language
                FROM larcauth_unit_period up
                JOIN larcauth_academicyear ay ON ay.s_id = 1
                WHERE up.start_date BETWEEN ay.start_date AND ay.end_date
                ORDER BY up.unit_nr, up.fk_language
            """)
            rows = cur.fetchall()
            # Une entrée par unit_nr, en préférant le français (fk_language=2)
            best: dict[int, dict] = {}
            for r in rows:
                nr = r[1]
                lang = r[5]
                d = {'id': r[0], 'unit_nr': nr, 'label': r[2],
                     'start_date': r[3].isoformat(),
                     'end_date': r[4].isoformat(),
                     'fk_language': lang}
                if nr not in best or lang == 2:
                    best[nr] = d
            return [best[k] for k in sorted(best)]
        except Exception as e:
            log(f"DataLoader.get_unit_periods: {e}")
            return []

    # ------------------------------------------------------------------
    # Programmes et classes
    # ------------------------------------------------------------------
    def get_programs(self) -> dict[int, dict]:
        try:
            cur = self._cursor()
            cur.execute("SELECT id, sigle, label FROM larcauth_program ORDER BY sigle")
            return {r[0]: {'sigle': r[1], 'label': r[2]} for r in cur.fetchall()}
        except Exception as e:
            log(f"DataLoader.get_programs: {e}")
            return {}

    def get_classes(self) -> list[tuple]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT c.id, c.label, l.fk_program_id, p.sigle
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE c.enabled = TRUE AND p.sigle IN ('PEI', 'MYP', 'DPEn', 'DPFr')
                ORDER BY p.sigle, c.label
            """)
            return cur.fetchall()
        except Exception as e:
            log(f"DataLoader.get_classes: {e}")
            return []

    def get_all_classrooms(self) -> list[tuple]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT c.id, c.label FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE c.enabled = TRUE
                ORDER BY c.label
            """)
            return cur.fetchall()
        except Exception as e:
            log(f"DataLoader.get_all_classrooms: {e}")
            return []

    def get_student_classroom(self, student_id: int) -> dict:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT s.s_classroom_id, c.label
                FROM larcauth_student s
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                WHERE s.aecuser_ptr_id = %s
            """, (student_id,))
            r = cur.fetchone()
            if r:
                return {'classroom_id': r[0], 'label': r[1]}
            return {}
        except Exception as e:
            log(f"DataLoader.get_student_classroom: {e}")
            return {}

    # ------------------------------------------------------------------
    # Statistiques de groupe (mode agrégé)
    # ------------------------------------------------------------------
    def _build_class_filter(self, mode: str) -> str:
        if mode == 'grp_all':
            return "AND p.sigle IN ('PEI', 'MYP', 'DPEn', 'DPFr')"
        if mode == 'grp_college':
            return "AND (p.sigle ILIKE 'PEI' OR p.sigle ILIKE 'MYP')"
        if mode == 'grp_lycee':
            return "AND (p.sigle ILIKE 'DPEn' OR p.sigle ILIKE 'DPFr')"
        sigle = mode.split('_')[1]
        return f"AND p.sigle ILIKE '{sigle}'"

    def get_class_stats(self, mode: str, date_from: str, date_to: str) -> list[dict]:
        try:
            cur = self._cursor()
            cf = self._build_class_filter(mode)
            cur.execute(f"""
                SELECT c.id, c.label,
                       COUNT(DISTINCT se.event_id) AS event_count,
                       COUNT(DISTINCT CASE WHEN se.event_type = %s OR se.event_type ILIKE %s THEN se.event_id END) AS abs_count,
                       COUNT(DISTINCT CASE WHEN se.event_type = %s OR se.event_type ILIKE %s OR se.event_type ILIKE %s THEN se.event_id END) AS exit_count,
                       COUNT(DISTINCT s.aecuser_ptr_id) AS student_count
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                LEFT JOIN larcauth_student s ON s.s_classroom_id = c.id AND s.enabled = TRUE
                LEFT JOIN student_event se ON se.student_id = s.aecuser_ptr_id
                    AND DATE(se.event_at) BETWEEN %s AND %s
                WHERE c.enabled = TRUE {cf}
                GROUP BY c.id, c.label
                ORDER BY c.label
            """, ('absence', 'Suivi > Absence%', 'exit', 'Sortie%', '%Fuite%', date_from, date_to))
            return [
                {'id': r[0], 'label': r[1], 'event_count': r[2],
                 'abs_count': r[3], 'exit_count': r[4], 'student_count': r[5]}
                for r in cur.fetchall()
            ]
        except Exception as e:
            log(f"DataLoader.get_class_stats: {e}")
            return []

    def get_attendance_trend(self, mode: str, date_from: str, date_to: str) -> list[dict]:
        try:
            cur = self._cursor()
            cf = self._build_class_filter(mode)
            cur.execute(f"""
                SELECT DATE(se.event_at) AS d, COUNT(*) AS cnt
                FROM student_event se
                JOIN larcauth_student s ON s.aecuser_ptr_id = se.student_id
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE (se.event_type = %s OR se.event_type ILIKE %s)
                  AND c.enabled = TRUE {cf}
                  AND DATE(se.event_at) BETWEEN %s AND %s
                GROUP BY d ORDER BY d
            """, ('absence', 'Suivi > Absence%', date_from, date_to))
            return [{'date': r[0], 'count': r[1]} for r in cur.fetchall()]
        except Exception as e:
            log(f"DataLoader.get_attendance_trend: {e}")
            return []

    def get_presence_rate(self, mode: str, date_from: str, date_to: str) -> dict:
        try:
            cur = self._cursor()
            cf = self._build_class_filter(mode)
            cur.execute(f"""
                SELECT COUNT(DISTINCT s.aecuser_ptr_id) FILTER (
                    WHERE NOT EXISTS (
                        SELECT 1 FROM student_event se2
                        WHERE se2.student_id = s.aecuser_ptr_id
                          AND (se2.event_type = %s OR se2.event_type ILIKE %s)
                          AND DATE(se2.event_at) BETWEEN %s AND %s
                    )
                ) AS present,
                COUNT(DISTINCT s.aecuser_ptr_id) FILTER (
                    WHERE EXISTS (
                        SELECT 1 FROM student_event se3
                        WHERE se3.student_id = s.aecuser_ptr_id
                          AND (se3.event_type = %s OR se3.event_type ILIKE %s)
                          AND DATE(se3.event_at) BETWEEN %s AND %s
                    )
                ) AS absent
                FROM larcauth_student s
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE s.enabled = TRUE AND c.enabled = TRUE {cf}
            """, ('absence', 'Suivi > Absence%', date_from, date_to,
                   'absence', 'Suivi > Absence%', date_from, date_to))
            r = cur.fetchone()
            return {'present': r[0] if r else 0, 'absent': r[1] if r else 0}
        except Exception as e:
            log(f"DataLoader.get_presence_rate: {e}")
            return {'present': 0, 'absent': 0}

    # ------------------------------------------------------------------
    # Historique global des événements
    # ------------------------------------------------------------------
    def get_all_event_types(self) -> list[str]:
        try:
            cur = self._cursor()
            cur.execute("SELECT DISTINCT event_type FROM student_event ORDER BY event_type")
            return [r[0] for r in cur.fetchall()]
        except Exception as e:
            log(f"DataLoader.get_all_event_types: {e}")
            return []

    def get_event_history(self, mode: str, date_from: str, date_to: str,
                          class_id=None, type_filter=None) -> list[dict]:
        try:
            cur = self._cursor()
            cf = self._build_class_filter(mode)
            params = []
            if class_id:
                cf += " AND c.id = %s"
                params.append(class_id)
            if type_filter:
                cf += " AND se.event_type ILIKE %s"
                params.append(f'%{type_filter}%')

            cur.execute(f"""
                SELECT se.event_id,
                       aec.last_name || ' ' || aec.first_name AS student_name,
                       c.label AS class_name,
                       se.event_type, se.event_at, se.lieu_label, se.subject_label, se.note,
                       u.last_name || ' ' || u.first_name AS created_by_name,
                       se.validated_by
                FROM student_event se
                JOIN larcauth_student s ON s.aecuser_ptr_id = se.student_id
                JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                LEFT JOIN larcauth_aecuser u ON u.id = se.created_by
                WHERE DATE(se.event_at) BETWEEN %s AND %s {cf}
                ORDER BY se.event_at DESC
                LIMIT 500
            """, (date_from, date_to, *params))

            return [
                {
                    'event_id': r[0], 'student_name': r[1], 'class_name': r[2],
                    'event_type': r[3], 'event_at': r[4], 'lieu_label': r[5],
                    'subject_label': r[6], 'note': r[7], 'created_by': r[8],
                    'validated_by': r[9],
                }
                for r in cur.fetchall()
            ]
        except Exception as e:
            log(f"DataLoader.get_event_history: {e}")
            return []

    # ------------------------------------------------------------------
    # Élèves et détails
    # ------------------------------------------------------------------
    def get_students(self, class_id: int) -> list[dict]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT s.aecuser_ptr_id,
                       aec.last_name, aec.first_name
                FROM larcauth_student s
                JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                WHERE s.s_classroom_id = %s AND s.enabled = TRUE
                ORDER BY aec.last_name
            """, (class_id,))
            return [
                {'id': r[0], 'last_name': r[1], 'first_name': r[2]}
                for r in cur.fetchall()
            ]
        except Exception as e:
            log(f"DataLoader.get_students: {e}")
            return []

    def get_student_event_stats(self, student_ids: list[int],
                                 date_from: str, date_to: str) -> dict[int, dict]:
        if not student_ids:
            return {}
        try:
            cur = self._cursor()
            ids_sql = ','.join(str(sid) for sid in student_ids)
            cur.execute(f"""
                SELECT se.student_id,
                       COUNT(*) FILTER (WHERE se.event_type = %s OR se.event_type ILIKE %s OR se.event_type ILIKE %s) AS exit_count,
                       CASE WHEN COUNT(*) FILTER (WHERE (se.event_type = %s
                           OR se.event_type ILIKE %s)
                           AND se.validated_by IS NULL) > 0 THEN 'Absent' ELSE 'Présent' END AS presence
                FROM student_event se
                WHERE se.student_id IN ({ids_sql})
                  AND DATE(se.event_at) BETWEEN %s AND %s
                GROUP BY se.student_id
            """, ('exit', 'Sortie%', '%Fuite%', 'absence', 'Suivi > Absence%', date_from, date_to))
            return {r[0]: {'exit_count': r[1], 'presence': r[2]} for r in cur.fetchall()}
        except Exception as e:
            log(f"DataLoader.get_student_event_stats: {e}")
            return {}

    def get_student_info(self, student_id: int) -> dict:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT aec.last_name, aec.first_name,
                       aec.email, aec.emailperso,
                       aec.tel_maison, aec.tel_smartphone_1,
                       aec.date_entree, c.label
                FROM larcauth_student s
                JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                WHERE s.aecuser_ptr_id = %s
            """, (student_id,))
            r = cur.fetchone()
            if not r:
                return {}
            return {
                'last_name': r[0], 'first_name': r[1],
                'email': r[2], 'email_perso': r[3],
                'tel_maison': r[4], 'tel_portable': r[5],
                'date_entree': r[6], 'class_label': r[7],
            }
        except Exception as e:
            log(f"DataLoader.get_student_info: {e}")
            return {}

    def get_student_kpis(self, student_id: int, date_from: str, date_to: str) -> dict:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE event_type = %s OR event_type ILIKE %s) AS abs_count,
                    COUNT(*) FILTER (WHERE event_type = %s OR event_type ILIKE %s OR event_type ILIKE %s) AS exit_count,
                    COUNT(*) AS total
                FROM student_event
                WHERE student_id = %s AND DATE(event_at) BETWEEN %s AND %s
            """, ('absence', 'Suivi > Absence%', 'exit', 'Sortie%', '%Fuite%',
                   student_id, date_from, date_to))
            r = cur.fetchone()
            return {'abs_count': r[0], 'exit_count': r[1], 'total': r[2]} if r else {}
        except Exception as e:
            log(f"DataLoader.get_student_kpis: {e}")
            return {}

    def get_student_absence_trend(self, student_id: int,
                                   term_start: str, term_end: str) -> list[dict]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT DATE(event_at) AS d, COUNT(*) AS cnt
                FROM student_event
                WHERE student_id = %s AND (event_type = %s OR event_type ILIKE %s)
                  AND DATE(event_at) BETWEEN %s AND %s
                GROUP BY d ORDER BY d
            """, (student_id, 'absence', 'Suivi > Absence%', term_start, term_end))
            return [{'date': r[0], 'count': r[1]} for r in cur.fetchall()]
        except Exception as e:
            log(f"DataLoader.get_student_absence_trend: {e}")
            return []

    def get_student_events(self, student_id: int, limit: int = 20) -> list[dict]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT se.event_id, se.event_type, se.event_at, se.lieu_label,
                       se.subject_label, se.note,
                       u.last_name || ' ' || u.first_name AS creator,
                       se.validated_by
                FROM student_event se
                LEFT JOIN larcauth_aecuser u ON u.id = se.created_by
                WHERE se.student_id = %s
                ORDER BY se.event_at DESC
                LIMIT %s
            """, (student_id, limit))
            return [
                {
                    'event_id': r[0], 'event_type': r[1], 'event_at': r[2],
                    'lieu_label': r[3], 'subject_label': r[4], 'note': r[5],
                    'creator': r[6], 'validated_by': r[7],
                }
                for r in cur.fetchall()
            ]
        except Exception as e:
            log(f"DataLoader.get_student_events: {e}")
            return []

    # ------------------------------------------------------------------
    # CRUD événements
    # ------------------------------------------------------------------
    def insert_event(self, data: dict) -> bool:
        try:
            cur = self._cursor()
            cur.execute(
                "INSERT INTO student_event (student_id, event_type, event_at, "
                "lieu_label, subject_label, note, source, created_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (data['student_id'], data['event_type'], data['event_at'],
                 data['lieu_label'], data.get('subject_label', ''),
                 data['note'], data['source'], data['created_by'])
            )
            self.conn.commit()
            return True
        except Exception as e:
            log(f"DataLoader.insert_event: {e}")
            self.conn.rollback()
            return False

    def get_event_details(self, event_id: int) -> dict:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT se.event_type, se.event_at, se.lieu_label, se.subject_label,
                       se.note,
                       aec.last_name || ' ' || aec.first_name AS student_name
                FROM student_event se
                JOIN larcauth_aecuser aec ON aec.id = se.student_id
                WHERE se.event_id = %s
            """, (event_id,))
            r = cur.fetchone()
            if not r:
                return {}
            return {
                'event_type': r[0], 'event_at': r[1], 'lieu_label': r[2],
                'subject_label': r[3], 'note': r[4], 'student_name': r[5],
            }
        except Exception as e:
            log(f"DataLoader.get_event_details: {e}")
            return {}

    def check_event_validated(self, event_id: int):
        try:
            cur = self._cursor()
            cur.execute("SELECT validated_by FROM student_event WHERE event_id = %s", (event_id,))
            r = cur.fetchone()
            return r[0] if r else None
        except Exception as e:
            log(f"DataLoader.check_event_validated: {e}")
            return None

    def toggle_event_validation(self, event_id: int, user_id: int) -> bool:
        try:
            cur = self._cursor()
            cur.execute("SELECT validated_by FROM student_event WHERE event_id = %s", (event_id,))
            r = cur.fetchone()
            if r and r[0] is not None:
                cur.execute("UPDATE student_event SET validated_by = NULL WHERE event_id = %s",
                            (event_id,))
            else:
                cur.execute("UPDATE student_event SET validated_by = %s WHERE event_id = %s",
                            (user_id, event_id))
            self.conn.commit()
            return True
        except Exception as e:
            log(f"DataLoader.toggle_event_validation: {e}")
            self.conn.rollback()
            return False

    def update_event(self, event_id: int, event_type: str, note: str) -> bool:
        try:
            cur = self._cursor()
            cur.execute(
                "UPDATE student_event SET event_type = %s, note = %s WHERE event_id = %s",
                (event_type, note, event_id))
            self.conn.commit()
            return True
        except Exception as e:
            log(f"DataLoader.update_event: {e}")
            self.conn.rollback()
            return False

    def delete_event(self, event_id: int) -> bool:
        try:
            cur = self._cursor()
            cur.execute("DELETE FROM student_event WHERE event_id = %s", (event_id,))
            self.conn.commit()
            return True
        except Exception as e:
            log(f"DataLoader.delete_event: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Lieux
    # ------------------------------------------------------------------
    def get_locations(self) -> list[tuple]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT DISTINCT ON ("s_IDLieu") "IDLieu", "s_IDLieu", "Lieu"
                FROM larcauth_lieu
                WHERE "fk_language" = 2 AND "IDLieu" > 0
                  AND "Lieu" NOT IN ('---', 'Non pr\u00e9cis\u00e9')
                ORDER BY "s_IDLieu", "IDLieu"
            """)
            return cur.fetchall()
        except Exception as e:
            log(f"DataLoader.get_locations: {e}")
            return []

    # ------------------------------------------------------------------
    # Matières
    # ------------------------------------------------------------------
    def get_classroom_subjects(self, classroom_id: int, term_id: int = None) -> list[tuple]:
        try:
            cur = self._cursor()
            try:
                cur.execute("""
                    SELECT cts.id, cts.label, cts.fk_teacher_id,
                           aec.last_name || ' ' || aec.first_name AS teacher_name
                    FROM larcauth_classroom_termsubject cts
                    LEFT JOIN larcauth_aecuser aec ON aec.id = cts.fk_teacher_id
                    WHERE cts.fk_classroom_id = %s
                      AND cts.fk_term_id = %s
                      AND cts.enabled = TRUE
                    ORDER BY cts.label
                """, (classroom_id, term_id))
            except Exception:
                cur.execute("""
                    SELECT cts.id, cts.label, cts.fk_teacher_id,
                           aec.last_name || ' ' || aec.first_name AS teacher_name
                    FROM larcauth_classroom_termsubject cts
                    LEFT JOIN larcauth_aecuser aec ON aec.id = cts.fk_teacher_id
                    WHERE cts.fk_classroom_id = %s
                      AND cts.enabled = TRUE
                    ORDER BY cts.label
                """, (classroom_id,))
            return cur.fetchall()
        except Exception as e:
            log(f"DataLoader.get_classroom_subjects: {e}")
            return []

    # ------------------------------------------------------------------
    # Types d'événements (hiérarchie)
    # ------------------------------------------------------------------
    def get_event_types_tree(self) -> dict[str, dict]:
        try:
            cur = self._cursor()
            cur.execute('''
                SELECT idtypeevent, type_event,
                       COALESCE("Event_Niveau2", '') AS niv2,
                       COALESCE("Event_Niveau3", '') AS niv3
                FROM larcauth_type_event
                WHERE "Enabled" IS NOT FALSE
                ORDER BY idtypeevent
            ''')
            tree = {}
            for _, cat, niv2, niv3 in cur.fetchall():
                if cat not in tree:
                    tree[cat] = {}
                if niv2:
                    if niv2 not in tree[cat]:
                        tree[cat][niv2] = []
                    if niv3:
                        tree[cat][niv2].append(niv3)
            return tree
        except Exception as e:
            log(f"DataLoader.get_event_types_tree: {e}")
            return {}

    # ------------------------------------------------------------------
    # Emploi du temps / TimeSlotGrid
    # ------------------------------------------------------------------
    def get_classroom_timeperiods(self, classroom_id: int, weekday: int,
                                   term_id: int) -> list[dict]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT tp.id, tp.debut, tp.fin, cht.id AS timetable_id
                FROM larcauth_classroom_has_timeperiod cht
                JOIN larcauth_timeperiod tp ON tp.id = cht.fk_timeperiod
                WHERE cht.fk_classroom = %s
                  AND cht.fk_weekday = %s
                  AND cht.fk_term = %s
                ORDER BY tp.debut
            """, (classroom_id, weekday, term_id))
            return [
                {'id': r[0], 'debut': str(r[1])[:5], 'fin': str(r[2])[:5],
                 'timetable_id': r[3]}
                for r in cur.fetchall()
            ]
        except Exception as e:
            log(f"DataLoader.get_classroom_timeperiods: {e}")
            return []

    # ------------------------------------------------------------------
    # TimetableEditor
    # ------------------------------------------------------------------
    def get_timeperiods(self) -> list[tuple]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT id, debut, fin, weekday
                FROM larcauth_timeperiod
                WHERE enabled = TRUE
                ORDER BY weekday, debut
            """)
            return cur.fetchall()
        except Exception as e:
            log(f"DataLoader.get_timeperiods: {e}")
            return []

    def get_classroom_timetable(self, class_id: int, term_id: int) -> dict:
        result = {'cht_map': {}, 'cht_id_map': {}}
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT cht.id, cht.fk_timeperiod, cht.fk_weekday,
                       coalesce(cht.s_classroom_termsubject, cht.ref_classroom_termsubject, '')
                FROM classroom_has_timeperiod cht
                WHERE cht.fk_classroom = %s AND cht.fk_term = %s
            """, (class_id, term_id))
            for cht_id, tp_id, wd, subj in cur.fetchall():
                result['cht_map'][(wd, tp_id)] = subj
                result['cht_id_map'][(wd, tp_id)] = cht_id
            return result
        except Exception as e:
            log(f"DataLoader.get_classroom_timetable: {e}")
            return result

    def get_available_subjects(self, class_id: int) -> list[str]:
        try:
            cur = self._cursor()
            cur.execute("""
                SELECT DISTINCT sub.label
                FROM classroom_has_timeperiod cht
                JOIN larcauth_subject sub ON sub.id = cht.ref_classroom_termsubject
                WHERE cht.fk_classroom = %s AND cht.ref_classroom_termsubject IS NOT NULL
                ORDER BY sub.label
            """, (class_id,))
            return [''] + [r[0] for r in cur.fetchall()]
        except Exception as e:
            log(f"DataLoader.get_available_subjects: {e}")
            return ['']

    def get_subject_id_by_label(self, label: str):
        try:
            cur = self._cursor()
            cur.execute("SELECT id FROM larcauth_subject WHERE label = %s", (label,))
            r = cur.fetchone()
            return r[0] if r else None
        except Exception as e:
            log(f"DataLoader.get_subject_id_by_label: {e}")
            return None

    def update_timetable_slot(self, cht_id: int, subj_id) -> bool:
        try:
            cur = self._cursor()
            if subj_id:
                cur.execute(
                    "UPDATE classroom_has_timeperiod SET ref_classroom_termsubject = %s WHERE id = %s",
                    (subj_id, cht_id))
            else:
                cur.execute(
                    "UPDATE classroom_has_timeperiod SET ref_classroom_termsubject = NULL WHERE id = %s",
                    (cht_id,))
            self.conn.commit()
            return True
        except Exception as e:
            log(f"DataLoader.update_timetable_slot: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Authentification (DB part only)
    # ------------------------------------------------------------------
    def find_user_by_email(self, email: str):
        try:
            cur = self._cursor()
            cur.execute(
                "SELECT id, first_name, last_name, email, password, "
                "type_director, type_coordonator, type_supervisor "
                "FROM public.larcauth_aecuser WHERE email = %s",
                (email,)
            )
            r = cur.fetchone()
            if not r:
                return None
            return {
                'user_id': r[0], 'first_name': r[1], 'last_name': r[2],
                'email': r[3], 'password_hash': r[4],
                'is_director': r[5], 'is_coord': r[6], 'is_supervisor': r[7],
            }
        except Exception as e:
            log(f"DataLoader.find_user_by_email: {e}")
            return None

    def get_student_name(self, student_id: int) -> str:
        try:
            cur = self._cursor()
            cur.execute(
                "SELECT aec.last_name || ' ' || aec.first_name FROM larcauth_student s "
                "JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id WHERE s.aecuser_ptr_id = %s",
                (student_id,)
            )
            r = cur.fetchone()
            return r[0] if r else ""
        except Exception as e:
            log(f"DataLoader.get_student_name: {e}")
            return ""
