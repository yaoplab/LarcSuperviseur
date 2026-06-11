"""Audit trail — traçabilité centralisée PostgreSQL.

Usage :
    from common.audit import audit
    audit.log('add_event', 'event', 123101, 'Sortie élève')
"""
from common.database import db
from common.session import session
from common.logger import log


def _insert(action: str, target_type: str, target_id: int | None,
            detail: str, source: str | None = None) -> None:
    conn = db.server_conn
    if not conn:
        log("audit: pas de connexion serveur, log ignoré")
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_trail
                (secretary_id, secretary_name, action, target_type,
                 target_id, detail, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            getattr(session, 'user_id', None),
            getattr(session, 'full_name', None),
            action, target_type, target_id,
            (detail or '')[:500],
            source or getattr(session, 'conn_mode', None) or 'intranet',
        ))
    except Exception as e:
        log(f"audit: echec INSERT audit_trail: {e}")


class AuditLogger:
    """Points d'entrée métier pour l'audit."""

    @staticmethod
    def login(supervisor_id: int, supervisor_name: str, mode: str) -> None:
        _insert('login', 'session', supervisor_id,
                f"Connexion {mode} — {supervisor_name}",
                source=mode)

    @staticmethod
    def logout(supervisor_id: int, supervisor_name: str) -> None:
        _insert('logout', 'session', supervisor_id,
                f"Déconnexion — {supervisor_name}")

    @staticmethod
    def add_event(student_id: int, event_type: str, note: str = '') -> None:
        detail = f"Événement {event_type}"
        if note:
            detail += f" : {note[:200]}"
        _insert('add_event', 'event', student_id, detail)

    @staticmethod
    def delete_event(event_id: int, detail: str) -> None:
        _insert('delete_event', 'event', event_id, detail)

    @staticmethod
    def update_timetable(count: int) -> None:
        _insert('update_timetable', 'timetable', None,
                f"{count} créneau(x) modifié(s)")

    @staticmethod
    def validate_event(event_id: int, detail: str) -> None:
        _insert('validate_event', 'event', event_id, detail)


audit = AuditLogger()
