from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QDialog,
)
from PySide6.QtCore import Qt, Signal
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.theme import theme_manager
# EventGenerator imported lazily in _open_event_dialog to avoid circular import


class TimeSlotGrid(QWidget):
    slotClicked = Signal(int, str, str)  # student_id, timeperiod_id, timetable_id

    def __init__(self):
        super().__init__()
        self._grid = QGridLayout()
        self._grid.setSpacing(1)
        self.setLayout(self._grid)
        self._slots: dict[str, QPushButton] = {}
        self._current_student_id: int = 0
        self._timeperiods: list[dict] = []

    def load(self, classroom_id: int, term_id: int, weekday: int, student_id: int = 0):
        for i in reversed(range(self._grid.count())):
            w = self._grid.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._slots.clear()
        self._timeperiods.clear()
        self._current_student_id = student_id

        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT tp.id, tp.debut, tp.fin, cht.id AS timetable_id
                FROM larcauth_classroom_has_timeperiod cht
                JOIN larcauth_timeperiod tp ON tp.id = cht.fk_timeperiod
                WHERE cht.fk_classroom = %s
                  AND cht.fk_weekday = %s
                  AND cht.fk_term = %s
                ORDER BY tp.debut
            """, (classroom_id, weekday, term_id))
            rows = cur.fetchall()
        except Exception as e:
            log(f"TimeSlotGrid.load: {e}")
            return

        if not rows:
            return

        # En-têtes : heures
        self._timeperiods = [
            {'id': r[0], 'debut': str(r[1])[:5], 'fin': str(r[2])[:5], 'timetable_id': r[3]}
            for r in rows
        ]

        for col, tp in enumerate(self._timeperiods):
            label = QLabel(f"{tp['debut']}-{tp['fin']}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                f"font-weight: bold; font-size: {theme_manager.font_size(10)}px; padding: 2px; "
                f"color: {theme_manager.palette.text_strong};")
            self._grid.addWidget(label, 0, col)

        btn = QPushButton("Ajouter événement")
        p = theme_manager.palette
        s = theme_manager.font_size
        btn.setStyleSheet(
            f"font-size: {s(9)}px; padding: 4px; "
            f"background: {p.surface_variant}; border: 1px solid {p.outline_variant}; "
            f"color: {p.text_strong};")
        btn.clicked.connect(lambda: self._open_event_dialog(0, '', ''))
        self._grid.addWidget(btn, 1, 0, 1, len(self._timeperiods))

    def set_student(self, student_id: int):
        self._current_student_id = student_id
        self._update_student_labels()

    def _update_student_labels(self):
        for key, btn in self._slots.items():
            sid, tp_id = map(int, key.split(':'))
            if self._current_student_id and sid != self._current_student_id:
                btn.setVisible(False)
            else:
                btn.setVisible(True)

    def _open_event_dialog(self, timetable_id=None, timeperiod_id=None, slot_label=None):
        if not self._current_student_id:
            QMessageBox.information(self, "Info",
                "Sélectionnez d'abord un élève dans la liste de gauche.")
            return
        from LarcSuperviseur.views.dialogs.event_generator import EventGenerator
        dlg = EventGenerator(self._current_student_id, self)
        if dlg.exec():
            data = dlg.get_data()
            conn = db.server_conn
            if not conn:
                QMessageBox.warning(self, "Erreur", "Aucune connexion base de données.")
                return
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO student_event (student_id, event_type, event_at, lieu_label, subject_label, note, source, created_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (data['student_id'], data['event_type'], data['event_at'],
                     data['lieu_label'], data.get('subject_label', ''),
                     data['note'], data['source'], session.user_id)
                )
                conn.commit()
            except Exception as e:
                log(f"_open_event_dialog insert: {e}")
                conn.rollback()
                QMessageBox.critical(self, "Erreur", f"Échec de l'enregistrement : {e}")
                return
            self.window().refresh_all()


class TimetableEditor(QDialog):
    DAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']

    def __init__(self, class_id: int, class_label: str, term_id: int, parent=None):
        super().__init__(parent)
        self._class_id = class_id
        self._term_id = term_id
        self.setWindowTitle(f"Emploi du temps — {class_label}")
        self.setMinimumSize(800, 500)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        layout = QVBoxLayout(self)

        # Grille
        self._tt_grid = QTableWidget()
        self._tt_grid.setAlternatingRowColors(True)
        self._tt_grid.horizontalHeader().setStretchLastSection(True)
        self._tt_grid.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._tt_grid, 1)

        # Boutons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.setMinimumHeight(36)
        save_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; font-weight: bold; "
            f"font-size: {s(12)}px; padding: 6px 20px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}")
        save_btn.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _load_data(self):
        conn = db.server_conn
        if not conn:
            return

        try:
            cur = conn.cursor()

            # Tous les timeperiods triés par weekday, debut
            cur.execute("""
                SELECT id, debut, fin, weekday
                FROM larcauth_timeperiod
                WHERE enabled = TRUE
                ORDER BY weekday, debut
            """)
            all_tps = cur.fetchall()

            # Regrouper par jour
            from collections import defaultdict
            self._tp_by_day: dict[int, list[tuple]] = defaultdict(list)
            for tp_id, debut, fin, wd in all_tps:
                self._tp_by_day[wd].append((tp_id, debut, fin))

            # classroom_has_timeperiod pour cette classe et ce term
            cur.execute("""
                SELECT cht.id, cht.fk_timeperiod, cht.fk_weekday,
                       coalesce(cht.s_classroom_termsubject, cht.ref_classroom_termsubject, '')
                FROM classroom_has_timeperiod cht
                WHERE cht.fk_classroom = %s AND cht.fk_term = %s
            """, (self._class_id, self._term_id))
            existing = cur.fetchall()
            # Map: (weekday, tp_id) → subject
            self._cht_map: dict[tuple[int, int], str] = {}
            self._cht_id_map: dict[tuple[int, int], str] = {}  # (wd, tp) → cht.id
            for cht_id, tp_id, wd, subj in existing:
                self._cht_map[(wd, tp_id)] = subj
                self._cht_id_map[(wd, tp_id)] = cht_id

            # Matières disponibles pour cette classe
            cur.execute("""
                SELECT DISTINCT sub.label
                FROM classroom_has_timeperiod cht
                JOIN larcauth_subject sub ON sub.id = cht.ref_classroom_termsubject
                WHERE cht.fk_classroom = %s AND cht.ref_classroom_termsubject IS NOT NULL
                ORDER BY sub.label
            """, (self._class_id,))
            self._subjects = [''] + [r[0] for r in cur.fetchall()]

            # Construire la grille
            self._build_grid()

        except Exception as e:
            log(f"TimetableEditor._load_data: {e}")
            QMessageBox.critical(self, "Erreur", str(e))

    def _build_grid(self):
        p = theme_manager.palette

        # Déterminer le nombre max de créneaux par jour
        max_slots = max(len(v) for v in self._tp_by_day.values()) if self._tp_by_day else 0

        self._tt_grid.setColumnCount(6)  # Heure + 5 jours
        self._tt_grid.setHorizontalHeaderLabels(['Heure'] + self.DAYS)
        self._tt_grid.setRowCount(max_slots)

        # Stocker les combos pour la sauvegarde
        self._cell_combos: dict[tuple[int, int], QComboBox] = {}  # (row, day)

        for row in range(max_slots):
            for day_idx in range(1, 6):  # 1=Lundi ... 5=Vendredi
                tp_list = self._tp_by_day.get(day_idx, [])
                if row < len(tp_list):
                    tp_id, debut, fin = tp_list[row]
                    debut_str = debut.strftime('%H:%M') if debut else ''
                    fin_str = fin.strftime('%H:%M') if fin else ''
                    time_label = f"{debut_str}-{fin_str}"

                    # Colonne Heure (col 0)
                    if day_idx == 1:
                        time_item = QTableWidgetItem(time_label)
                        time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
                        self._tt_grid.setItem(row, 0, time_item)

                    # Combo matière
                    combo = QComboBox()
                    combo.addItems(self._subjects)
                    current_subj = self._cht_map.get((day_idx, tp_id), '')
                    idx = combo.findText(current_subj)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                    # Stocker tp_id et cht_id dans le combo
                    combo.setProperty('tp_id', tp_id)
                    combo.setProperty('cht_id', self._cht_id_map.get((day_idx, tp_id), ''))
                    combo.setProperty('day', day_idx)
                    self._cell_combos[(row, day_idx)] = combo
                    self._tt_grid.setCellWidget(row, day_idx, combo)

        self._tt_grid.resizeColumnsToContents()
        self._tt_grid.setColumnWidth(0, 80)
        for c in range(1, 6):
            self._tt_grid.setColumnWidth(c, 140)

    def _save(self):
        conn = db.server_conn
        if not conn:
            return

        p = theme_manager.palette
        try:
            cur = conn.cursor()
            updated = 0

            for (row, day), combo in self._cell_combos.items():
                tp_id = combo.property('tp_id')
                cht_id = combo.property('cht_id')
                subj = combo.currentText().strip()

                if not cht_id:
                    continue  # ligne classroom_has_timeperiod manquante

                # Trouver l'id matière
                cur.execute("SELECT id FROM larcauth_subject WHERE label = %s", (subj,))
                r = cur.fetchone()
                subj_id = r[0] if r else None

                if subj_id:
                    cur.execute(
                        "UPDATE classroom_has_timeperiod SET ref_classroom_termsubject = %s WHERE id = %s",
                        (subj_id, cht_id))
                    updated += cur.rowcount
                else:
                    cur.execute(
                        "UPDATE classroom_has_timeperiod SET ref_classroom_termsubject = NULL WHERE id = %s",
                        (cht_id,))
                    updated += cur.rowcount

            conn.commit()
            QMessageBox.information(self, "Succès", f"{updated} créneau(x) mis à jour.")
            self.accept()

        except Exception as e:
            log(f"TimetableEditor._save: {e}")
            conn.rollback()
            QMessageBox.critical(self, "Erreur", str(e))
