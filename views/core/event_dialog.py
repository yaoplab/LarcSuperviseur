from larccommon.l10n import _
from phibuilder.widgets import M3Button, M3ComboBox, M3Dialog, M3Label, M3TextEdit
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QVBoxLayout,
)

from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.theme import theme_manager


class EventEditDialog(M3Dialog):
    def __init__(self, event_id: int, parent=None):
        super().__init__(parent)
        self._event_id = event_id
        self._conn = db.server_conn
        self.setWindowTitle(_("event_dialog.title").format(id=event_id))
        self.setMinimumSize(480, 400)
        self._setup_ui()
        self._load_event()

    def _setup_ui(self):
        p = theme_manager.palette
        layout = QVBoxLayout(self)

        self._info = M3Label()
        self._info.setWordWrap(True)
        self._info.setTextFormat(Qt.RichText)
        layout.addWidget(self._info)

        layout.addWidget(M3Label(_("event_dialog.type")))
        self._type_input = M3ComboBox()
        layout.addWidget(self._type_input)

        layout.addWidget(M3Label(_("event_dialog.note")))
        self._note_input = M3TextEdit()
        self._note_input.setMaximumHeight(120)
        layout.addWidget(self._note_input)

        btn_row = QHBoxLayout()
        save_btn = M3Button(_("event_dialog.save_button"))
        save_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; }}"
        )
        save_btn.clicked.connect(self._save)
        cancel_btn = M3Button(_("event_dialog.cancel_button"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _load_event(self):
        conn = self._conn
        if not conn:
            QMessageBox.warning(self, _("common.dialog.error"), _("event_dialog.no_connection"))
            self.reject()
            return
        cur = conn.cursor()
        cur.execute(
            """
            SELECT se.event_type, se.event_at, se.lieu_label, se.subject_label, se.note,
                   aec.last_name || ' ' || aec.first_name AS student_name
            FROM student_event se
            JOIN larcauth_aecuser aec ON aec.id = se.student_id
            WHERE se.event_id = %s
        """,
            (self._event_id,),
        )
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, _("common.dialog.error"), _("event_dialog.not_found"))
            self.reject()
            return
        etype, e_at, lieu, subject, note, student_name = row
        p = theme_manager.palette
        s = theme_manager.font_size
        self._info.setText(
            f"<b>{student_name}</b> — {etype}<br>"
            f"<span style='color:{p.text_disabled};font-size:{s(10)}px;'>"
            f"{e_at.strftime('%d/%m/%Y %H:%M') if e_at else ''} | {lieu or ''}"
            f"{' | ' + subject if subject else ''}</span>"
        )
        cur2 = conn.cursor()
        cur2.execute("SELECT DISTINCT event_type FROM student_event ORDER BY event_type")
        self._type_input.addItems([et for (et,) in cur2.fetchall()])
        self._type_input.setCurrentText(etype)
        self._note_input.setText(note or "")

    def _save(self):
        conn = self._conn
        if not conn:
            return
        cur = conn.cursor()
        cur.execute(
            "UPDATE student_event SET event_type = %s, note = %s WHERE event_id = %s",
            (
                self._type_input.currentText(),
                self._note_input.toPlainText().strip(),
                self._event_id,
            ),
        )
        conn.commit()
        self.accept()
