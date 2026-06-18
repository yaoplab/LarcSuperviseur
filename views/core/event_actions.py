from typing import Optional

from PySide6.QtWidgets import QMenu, QTableWidget

from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.logger import log


class EventActions:
    """CRUD operations on student_event."""

    def __init__(self):
        self._conn = db.server_conn

    @property
    def conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = db.server_conn
        return self._conn

    def get_event_by_id(self, event_id: int) -> Optional[dict]:
        conn = self.conn
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT se.event_id, se.student_id, se.event_type, se.event_at,
                       se.lieu_label, se.subject_label, se.note, se.validated_by,
                       se.agenda_day_id, se.created_by, se.created_at, se.source,
                       aec.last_name || ' ' || aec.first_name AS student_name
                FROM student_event se
                JOIN larcauth_aecuser aec ON aec.id = se.student_id
                WHERE se.event_id = %s
            """, (event_id,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in cur.description]
            return dict(zip(cols, row))
        except Exception as e:
            log(f"EventActions.get_event_by_id: {e}")
            return None

    def edit_event(self, event_id: int, data: dict) -> bool:
        conn = self.conn
        if not conn:
            return False
        allowed = {'event_type', 'note', 'lieu_label', 'subject_label', 'event_at'}
        sets = []
        params = []
        for key in allowed:
            if key in data:
                sets.append(f"{key} = %s")
                params.append(data[key])
        if not sets:
            return False
        params.append(event_id)
        try:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE student_event SET {', '.join(sets)} WHERE event_id = %s",
                params
            )
            conn.commit()
            return True
        except Exception as e:
            log(f"EventActions.edit_event: {e}")
            conn.rollback()
            return False

    def toggle_validation(self, event_id: int, validate: bool) -> bool:
        conn = self.conn
        if not conn:
            return False
        try:
            cur = conn.cursor()
            if validate:
                cur.execute(
                    "UPDATE student_event SET validated_by = %s WHERE event_id = %s",
                    (session.user_id, event_id)
                )
            else:
                cur.execute(
                    "UPDATE student_event SET validated_by = NULL WHERE event_id = %s",
                    (event_id,)
                )
            conn.commit()
            return True
        except Exception as e:
            log(f"EventActions.toggle_validation: {e}")
            conn.rollback()
            return False

    def delete_event(self, event_id: int) -> bool:
        conn = self.conn
        if not conn:
            return False
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM student_event WHERE event_id = %s", (event_id,))
            conn.commit()
            return True
        except Exception as e:
            log(f"EventActions.delete_event: {e}")
            conn.rollback()
            return False

    def get_context_menu(self, event_id: int, parent=None) -> QMenu:
        event = self.get_event_by_id(event_id)
        is_validated = event is not None and event.get('validated_by') is not None
        menu = QMenu(parent)
        menu.addAction("✏️ Modifier")
        menu.addAction("🔒 Dévalider" if is_validated else "✅ Valider")
        menu.addAction("🗑️ Supprimer")
        return menu

    @staticmethod
    def get_event_id_from_table(table: QTableWidget) -> Optional[int]:
        idx = table.currentRow()
        if idx < 0:
            return None
        item = table.item(idx, 0)
        return int(item.text()) if item and item.text().isdigit() else None

    @staticmethod
    def get_event_id_from_row(table: QTableWidget, row: int) -> Optional[int]:
        item = table.item(row, 0)
        return int(item.text()) if item and item.text().isdigit() else None
