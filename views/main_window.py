from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDateEdit, QFrame, QScrollArea, QGridLayout,
    QSplitter, QDialog, QDialogButtonBox, QTextEdit, QRadioButton,
    QButtonGroup, QSizePolicy, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, QDate, QTimer, QSize, Signal
from PySide6.QtGui import QColor, QBrush, QPixmap, QFont, QIcon, QPainter, QPainterPath
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session, UserRole
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.network import detect_network


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
EVENT_ICONS = {
    'arrival': '▲', 'departure': '▼', 'exit': '→', 'return': '←',
    'absence': '✕', 'justified': '✓', 'late': '⏰',
}
EVENT_COLORS = {
    'arrival': '#27ae60', 'departure': '#2980b9', 'exit': '#e67e22',
    'return': '#2ecc71', 'absence': '#e74c3c', 'justified': '#95a5a6',
    'late': '#f1c40f',
}


# ---------------------------------------------------------------------------
# Carte élève
# ---------------------------------------------------------------------------
class StudentCard(QFrame):
    clicked = Signal(int)  # student_id

    def __init__(self, student_id: int, name: str, photo_path: str = ''):
        super().__init__()
        self._sid = student_id
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            StudentCard {
                background: #f8f9fa; border: 1px solid #dee2e6;
                border-radius: 8px; padding: 8px;
            }
            StudentCard:hover {
                background: #e9ecef; border-color: #adb5bd;
            }
        """)
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # Photo
        self._photo = QLabel()
        self._photo.setFixedSize(80, 80)
        self._photo.setAlignment(Qt.AlignCenter)
        if photo_path:
            pix = QPixmap(photo_path)
            if not pix.isNull():
                self._photo.setPixmap(
                    pix.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        # Photo par défaut (rond gris)
        if not self._photo.pixmap() or self._photo.pixmap().isNull():
            default = QPixmap(80, 80)
            default.fill(QColor('#dee2e6'))
            self._photo.setPixmap(default)

        # Nom
        self._name_label = QLabel(name)
        self._name_label.setAlignment(Qt.AlignCenter)
        self._name_label.setWordWrap(True)
        self._name_label.setStyleSheet("font-weight: bold; font-size: 11px;")

        # Statut
        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("font-size: 10px;")

        # Nb sorties
        self._exit_label = QLabel()
        self._exit_label.setAlignment(Qt.AlignCenter)
        self._exit_label.setStyleSheet("font-size: 10px; color: #6c757d;")

        layout.addWidget(self._photo)
        layout.addWidget(self._name_label)
        layout.addWidget(self._status_label)
        layout.addWidget(self._exit_label)
        self.setLayout(layout)

    def mousePressEvent(self, event):
        self.clicked.emit(self._sid)
        super().mousePressEvent(event)

    def set_status(self, text: str, color: str = '#6c757d'):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"font-size: 10px; color: {color};")

    def set_exit_count(self, count: int):
        self._exit_label.setText(f"{count} sortie(s)" if count else '')


# ---------------------------------------------------------------------------
# Grille emploi du temps
# ---------------------------------------------------------------------------
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
            label.setStyleSheet("font-weight: bold; font-size: 10px; padding: 2px;")
            self._grid.addWidget(label, 0, col)

        btn = QPushButton("Ajouter événement")
        btn.setStyleSheet(
            "font-size: 9px; padding: 4px; background: #e9ecef; border: 1px solid #dee2e6;"
        )
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

    def _open_event_dialog(self, timetable_id, timeperiod_id, slot_label):
        if not self._current_student_id:
            QMessageBox.information(self, "Info",
                "Sélectionnez d'abord un élève dans la liste de gauche.")
            return
        dlg = EventGenerator(self._current_student_id, timeperiod_id, slot_label, self)
        if dlg.exec():
            self.window().refresh_all()


# ---------------------------------------------------------------------------
# Écran génération d'événement
# ---------------------------------------------------------------------------
class EventGenerator(QDialog):
    def __init__(self, student_id: int, timeperiod_id: str, slot_label: str, parent=None):
        super().__init__(parent)
        self._student_id = student_id
        self.setWindowTitle(f"Événement — élève #{student_id}")
        self.setMinimumWidth(500)
        self._init_ui(timeperiod_id, slot_label)

    def _init_ui(self, timeperiod_id: str, slot_label: str):
        layout = QVBoxLayout()

        # Infos élèves
        conn = db.server_conn
        student_name = f"Élève #{self._student_id}"
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT lastname || ' ' || firstname FROM larcauth_student WHERE aecuser_ptr_id = %s",
                    (self._student_id,)
                )
                r = cur.fetchone()
                if r:
                    student_name = r[0]
            except Exception:
                pass

        info = QLabel(f"<b>{student_name}</b>")
        info.setStyleSheet("font-size: 16px; padding: 10px;")

        if slot_label:
            heure = QLabel(f"Créneau : {slot_label}")
            heure.setStyleSheet("color: #6c757d; font-size: 12px;")
        else:
            heure = QLabel()
        self._source_label = QLabel()
        self._update_source_label()

        # Type d'événement
        type_group = QButtonGroup(self)
        type_layout = QHBoxLayout()
        event_types = [
            ('arrival', '▲ Arrivée'), ('departure', '▼ Départ'), ('exit', '→ Sortie'),
            ('return', '← Retour'), ('absence', '✕ Absence'), ('late', '⏰ Retard'),
            ('justified', '✓ Justifié'),
        ]
        self._selected_type = None
        for value, label in event_types:
            rb = QRadioButton(label)
            rb.toggled.connect(lambda checked, v=value: self._on_type_changed(v) if checked else None)
            type_group.addButton(rb)
            type_layout.addWidget(rb)

        # Note
        self._note_input = QTextEdit()
        self._note_input.setPlaceholderText("Note optionnelle (200 caractères max)")
        self._note_input.setMaximumHeight(80)

        # Boutons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(info)
        layout.addWidget(heure)
        layout.addWidget(self._source_label)
        layout.addSpacing(10)
        layout.addWidget(QLabel("<b>Type d'événement :</b>"))
        layout.addLayout(type_layout)
        layout.addSpacing(10)
        layout.addWidget(QLabel("<b>Note :</b>"))
        layout.addWidget(self._note_input)
        layout.addSpacing(10)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _update_source_label(self):
        intranet_ok, _ = detect_network()
        if intranet_ok and db.is_server_connected:
            self._source_label.setText("Source : Intranet (écriture)")
            self._source_label.setStyleSheet("color: #27ae60; font-size: 10px;")
        else:
            self._source_label.setText("Source : Cloud (écriture)")
            self._source_label.setStyleSheet("color: #2980b9; font-size: 10px;")

    def _on_type_changed(self, value: str):
        self._selected_type = value

    def _validate(self):
        if not self._selected_type:
            QMessageBox.warning(self, "Erreur", "Sélectionnez un type d'événement.")
            return
        self.accept()

    def get_data(self) -> dict:
        dt = QDate.currentDate().toString('yyyy-MM-dd')
        from datetime import datetime
        now = datetime.now().strftime('%H:%M:%S')
        return {
            'student_id': self._student_id,
            'event_type': self._selected_type,
            'event_at': f"{dt} {now}",
            'note': self._note_input.toPlainText().strip(),
            'source': 'cloud' if not detect_network()[0] else 'intranet',
        }


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"LarcSuperviseur — {session.full_name} ({session.role.value})")
        self._current_class_id: int = 0
        self._current_group_mode: str = ''  # 'pei', 'dp', 'etab', 'class'
        self._current_date = QDate.currentDate()
        self._current_period: str = 'day'  # day, week, month, term
        self._current_term_id: int = 0
        self._current_weekday: int = 0
        self._selected_student_id: int = 0
        self._students: list[dict] = []
        self._init_ui()
        self._load_initial_data()
        QTimer.singleShot(30000, self._refresh_timer)

    def _init_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(6)

        # -- Top bar --------------------------------------------------------
        top = QFrame()
        top.setStyleSheet("QFrame { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; }")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(10, 6, 10, 6)

        # Date + Heure (gros)
        self._date_label = QLabel()
        self._date_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        self._time_label = QLabel()
        self._time_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #e67e22;")
        self._update_datetime()

        # Sélecteur groupe/classe
        self._group_combo = QComboBox()
        self._group_combo.setMinimumWidth(200)
        self._group_combo.currentIndexChanged.connect(self._on_group_changed)

        # Période
        self._period_combo = QComboBox()
        self._period_combo.addItem("Jour", 'day')
        self._period_combo.addItem("Semaine", 'week')
        self._period_combo.addItem("Mois", 'month')
        self._period_combo.addItem("Trimestre", 'term')
        self._period_combo.currentIndexChanged.connect(self._on_period_changed)

        # Aujourd'hui
        self._today_btn = QPushButton("Aujourd'hui")
        self._today_btn.clicked.connect(self._go_today)
        self._today_btn.setFixedWidth(100)

        # Rafraîchir
        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setFixedWidth(36)
        self._refresh_btn.clicked.connect(self.refresh_all)

        # Réseau
        self._network_label = QLabel()
        self._update_network_label()

        top_layout.addWidget(self._date_label)
        top_layout.addWidget(self._time_label)
        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("Groupe/Classe :"))
        top_layout.addWidget(self._group_combo)
        top_layout.addSpacing(15)
        top_layout.addWidget(QLabel("Période :"))
        top_layout.addWidget(self._period_combo)
        top_layout.addSpacing(10)
        top_layout.addWidget(self._today_btn)
        top_layout.addWidget(self._refresh_btn)
        top_layout.addStretch()
        top_layout.addWidget(self._network_label)

        # -- Timer pour l'heure ---------------------------------------------
        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_datetime)
        self._clock_timer.start(10000)

        # -- Zone de contenu (splitter) -------------------------------------
        self._content_splitter = QSplitter(Qt.Horizontal)

        # Panneau gauche
        self._left_panel = QFrame()
        self._left_layout = QVBoxLayout(self._left_panel)
        self._left_layout.setContentsMargins(0, 0, 0, 0)

        # Mode groupe: stats classes
        self._stats_group = QFrame()
        self._stats_layout = QVBoxLayout(self._stats_group)
        stats_title = QLabel("<b>Statistiques par classe</b>")
        stats_title.setStyleSheet("font-size: 13px; padding: 4px;")
        self._stats_table = QTableWidget()
        self._stats_table.setAlternatingRowColors(True)
        self._stats_table.horizontalHeader().setStretchLastSection(True)
        self._stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._stats_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._stats_layout.addWidget(stats_title)
        self._stats_layout.addWidget(self._stats_table)

        # Mode classe: cartes élèves
        self._cards_widget = QWidget()
        self._cards_layout = QGridLayout(self._cards_widget)
        self._cards_layout.setSpacing(6)
        self._cards_scroll = QScrollArea()
        self._cards_scroll.setWidget(self._cards_widget)
        self._cards_scroll.setWidgetResizable(True)

        # Empiler stats + cards dans le panneau gauche
        self._left_layout.addWidget(self._stats_group)
        self._left_layout.addWidget(self._cards_scroll)

        # Panneau droit
        self._right_panel = QFrame()
        self._right_layout = QVBoxLayout(self._right_panel)
        self._right_layout.setContentsMargins(0, 0, 0, 0)

        # Mode groupe: historique des events
        self._history_group = QFrame()
        self._history_layout = QVBoxLayout(self._history_group)
        history_title = QLabel("<b>Historique des événements</b>")
        history_title.setStyleSheet("font-size: 13px; padding: 4px;")
        self._history_table = QTableWidget()
        self._history_table.setAlternatingRowColors(True)
        self._history_table.horizontalHeader().setStretchLastSection(True)
        self._history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._history_table.setSortingEnabled(True)
        self._history_layout.addWidget(history_title)
        self._history_layout.addWidget(self._history_table)

        # Mode classe: emploi du temps
        self._timetable_widget = QFrame()
        self._tt_layout = QVBoxLayout(self._timetable_widget)
        tt_title = QLabel("<b>Emploi du temps</b>")
        tt_title.setStyleSheet("font-size: 13px; padding: 4px;")
        self._tt_slots = TimeSlotGrid()
        self._tt_layout.addWidget(tt_title)
        self._tt_layout.addWidget(self._tt_slots)
        self._tt_empty = QLabel("Sélectionnez un élève\npour voir l'emploi du temps")
        self._tt_empty.setAlignment(Qt.AlignCenter)
        self._tt_empty.setStyleSheet("color: #6c757d; font-size: 13px;")

        # Empiler history + timetable dans le panneau droit
        self._right_layout.addWidget(self._history_group)
        self._right_layout.addWidget(self._timetable_widget)
        self._right_layout.addWidget(self._tt_empty)
        self._tt_empty.hide()

        self._content_splitter.addWidget(self._left_panel)
        self._content_splitter.addWidget(self._right_panel)
        self._content_splitter.setSizes([400, 500])

        outer.addWidget(top)
        outer.addWidget(self._content_splitter, 1)
        self.setLayout(outer)

    def _update_datetime(self):
        from datetime import datetime
        now = datetime.now()
        self._date_label.setText(now.strftime("%A %d %B %Y") + '  ')
        self._time_label.setText(now.strftime("%H:%M") + '  ')

    def _update_network_label(self):
        intranet_ok, internet_ok = detect_network()
        if intranet_ok:
            self._network_label.setText("Intranet ●")
            self._network_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif internet_ok:
            self._network_label.setText("Cloud ●")
            self._network_label.setStyleSheet("color: #2980b9; font-weight: bold;")
        else:
            self._network_label.setText("Hors ligne")
            self._network_label.setStyleSheet("color: #e67e22; font-weight: bold;")

    def _go_today(self):
        self._current_date = QDate.currentDate()
        self.refresh_all()

    def _load_initial_data(self):
        conn = db.server_conn
        if not conn:
            QMessageBox.warning(self, "Erreur", "Non connecté au serveur.")
            return

        try:
            cur = conn.cursor()

            # Terme actif
            cur.execute("SELECT id FROM larcib_term WHERE enabled = TRUE ORDER BY id DESC LIMIT 1")
            r = cur.fetchone()
            self._current_term_id = int(r[0]) if r else 0

            # Programmes (PEI, DP, ...)
            cur.execute("SELECT id, sigle, label FROM larcauth_program ORDER BY sigle")
            self._programs = {r[0]: {'sigle': r[1], 'label': r[2]} for r in cur.fetchall()}

            # Classes avec leur programme via level
            cur.execute("""
                SELECT c.id, c.label, l.fk_program_id, p.sigle
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE c.enabled = TRUE
                ORDER BY p.sigle, c.label
            """)
            self._classes = cur.fetchall()

            # Remplir le combo
            self._group_combo.clear()

            # Groupes par programme
            prog_groups = {}
            for cid, label, pid, sigle in self._classes:
                if sigle not in prog_groups:
                    prog_groups[sigle] = []
                    self._group_combo.addItem(f"Tout {sigle}", f"grp_{sigle}")
                prog_groups[sigle].append((cid, label))

            # Établissement (toutes les classes)
            self._group_combo.addItem("Établissement", 'grp_all')

            # Séparateur visuel
            self._group_combo.insertSeparator(self._group_combo.count())

            # Chaque classe individuellement
            for cid, label, pid, sigle in self._classes:
                self._group_combo.addItem(f"  {label} ({sigle})", f"cls_{cid}")

        except Exception as e:
            log(f"_load_initial_data: {e}")
            QMessageBox.critical(self, "Erreur", str(e))

    def _on_group_changed(self, idx: int):
        if idx < 0:
            return
        mode = self._group_combo.itemData(idx)
        if not mode:
            return

        if mode.startswith('grp_'):
            self._current_group_mode = mode
            self._current_class_id = 0
            self._show_group_mode(mode)
        elif mode.startswith('cls_'):
            self._current_class_id = int(mode.split('_')[1])
            self._current_group_mode = 'class'
            self._show_class_mode(self._current_class_id)

    def _on_period_changed(self, idx: int):
        if idx < 0:
            return
        self._current_period = self._period_combo.itemData(idx)
        self.refresh_all()

    # ---- Mode groupe -------------------------------------------------------

    def _show_group_mode(self, mode: str):
        """Affiche les stats par classe + historique des events."""
        self._stats_group.show()
        self._cards_scroll.hide()
        self._history_group.show()
        self._timetable_widget.hide()
        self._tt_empty.hide()

        self._load_group_stats(mode)
        self._load_global_history(mode)

    def _load_group_stats(self, mode: str):
        conn = db.server_conn
        if not conn or not self._current_term_id:
            return

        date_from, date_to = self._period_dates()

        try:
            cur = conn.cursor()

            if mode == 'grp_all':
                class_filter = ""
            else:
                sigle = mode.split('_')[1]
                class_filter = f"AND p.sigle = '{sigle}'"

            cur.execute(f"""
                SELECT c.id, c.label,
                       COUNT(DISTINCT se.event_id) AS event_count,
                       COUNT(DISTINCT CASE WHEN se.event_type = 'absence' THEN se.event_id END) AS abs_count,
                       COUNT(DISTINCT CASE WHEN se.event_type = 'exit' THEN se.event_id END) AS exit_count,
                       COUNT(DISTINCT lht.fk_student_id) AS student_count
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                LEFT JOIN larcauth_learner_has_term lht ON lht.fk_classroom_id = c.id
                    AND lht.fk_term_id = %s AND lht.enabled = TRUE
                LEFT JOIN student_event se ON se.student_id = lht.fk_student_id
                    AND DATE(se.event_at) BETWEEN %s AND %s
                WHERE c.enabled = TRUE {class_filter}
                GROUP BY c.id, c.label
                ORDER BY c.label
            """, (self._current_term_id, date_from, date_to))

            rows = cur.fetchall()
            self._stats_table.setRowCount(len(rows))
            self._stats_table.setColumnCount(5)
            self._stats_table.setHorizontalHeaderLabels(
                ["Classe", "Événements", "Absences", "Sorties", "Élèves"])

            for i, (cid, label, evts, absences, exits, students) in enumerate(rows):
                items = [
                    QTableWidgetItem(label),
                    QTableWidgetItem(str(evts)),
                    QTableWidgetItem(str(absences)),
                    QTableWidgetItem(str(exits)),
                    QTableWidgetItem(str(students)),
                ]
                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._stats_table.setItem(i, 0, items[0])
                self._stats_table.setItem(i, 1, items[1])
                self._stats_table.setItem(i, 2, items[2])
                self._stats_table.setItem(i, 3, items[3])
                self._stats_table.setItem(i, 4, items[4])

            self._stats_table.resizeColumnsToContents()

        except Exception as e:
            log(f"_load_group_stats: {e}")

    def _load_global_history(self, mode: str):
        conn = db.server_conn
        if not conn or not self._current_term_id:
            return

        date_from, date_to = self._period_dates()

        try:
            cur = conn.cursor()

            if mode == 'grp_all':
                class_filter = ""
            else:
                sigle = mode.split('_')[1]
                class_filter = f"AND p.sigle = '{sigle}'"

            cur.execute(f"""
                SELECT se.event_id,
                       s.lastname || ' ' || s.firstname AS student_name,
                       c.label AS class_name,
                       se.event_type, se.event_at, se.note,
                       u.lastname || ' ' || u.firstname AS created_by_name
                FROM student_event se
                JOIN larcauth_student s ON s.id = se.student_id
                JOIN larcauth_learner_has_term lht ON lht.fk_student_id = se.student_id
                    AND lht.fk_term_id = %s AND lht.enabled = TRUE
                JOIN larcauth_classroom c ON c.id = lht.fk_classroom_id
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                LEFT JOIN larcauth_aecuser u ON u.id = se.created_by
                WHERE DATE(se.event_at) BETWEEN %s AND %s {class_filter}
                ORDER BY se.event_at DESC
                LIMIT 500
            """, (self._current_term_id, date_from, date_to))

            rows = cur.fetchall()
            self._history_table.setRowCount(len(rows))
            self._history_table.setColumnCount(7)
            self._history_table.setHorizontalHeaderLabels(
                ["ID", "Élève", "Classe", "Type", "Heure", "Note", "Créé par"])
            self._history_table.setColumnHidden(0, True)  # event_id

            for i, row in enumerate(rows):
                eid, name, cls_name, etype, e_at, note, creator = row
                ei = EVENT_ICONS.get(etype, etype)
                color = EVENT_COLORS.get(etype, '#000')
                display_type = f"{ei} {etype}"

                items = [
                    QTableWidgetItem(str(eid)),
                    QTableWidgetItem(name),
                    QTableWidgetItem(cls_name),
                    QTableWidgetItem(display_type),
                    QTableWidgetItem(e_at.strftime('%H:%M') if e_at else ''),
                    QTableWidgetItem(note or ''),
                    QTableWidgetItem(creator),
                ]
                for j in range(len(items)):
                    if j == 3:
                        items[j].setForeground(QBrush(QColor(color)))
                    items[j].setFlags(items[j].flags() & ~Qt.ItemIsEditable)
                    self._history_table.setItem(i, j, items[j])
            self._history_table.resizeColumnsToContents()

        except Exception as e:
            log(f"_load_global_history: {e}")

    # ---- Mode classe -------------------------------------------------------

    def _show_class_mode(self, class_id: int):
        self._stats_group.hide()
        self._cards_scroll.show()
        self._history_group.hide()
        self._timetable_widget.show()
        self._tt_empty.hide()

        self._load_students(class_id)
        self._load_timetable(class_id)

    def _load_students(self, class_id: int):
        conn = db.server_conn
        if not conn or not self._current_term_id:
            return

        date_from, date_to = self._period_dates()

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.aecuser_ptr_id,
                       s.lastname || ' ' || s.firstname AS full_name
                FROM larcauth_student s
                JOIN larcauth_learner_has_term lht
                    ON lht.fk_student_id = s.aecuser_ptr_id
                WHERE lht.fk_classroom_id = %s
                  AND lht.fk_term_id = %s
                  AND lht.enabled = TRUE
                ORDER BY s.lastname
            """, (class_id, self._current_term_id))
            rows = cur.fetchall()

            self._students = [{'id': r[0], 'name': r[1]} for r in rows]

            # Stats d'events pour chaque élève
            student_ids = [s['id'] for s in self._students]
            event_stats = {}
            if student_ids:
                ids_sql = ','.join(str(sid) for sid in student_ids)
                try:
                    cur.execute(f"""
                        SELECT se.student_id,
                               COUNT(*) FILTER (WHERE se.event_type = 'exit') AS exit_count,
                               CASE WHEN COUNT(*) FILTER (WHERE se.event_type = 'absence'
                                   AND se.validated_by IS NULL) > 0 THEN 'Absent' ELSE 'Présent' END AS presence
                        FROM student_event se
                        WHERE se.student_id IN ({ids_sql})
                          AND DATE(se.event_at) BETWEEN %s AND %s
                        GROUP BY se.student_id
                    """, (date_from, date_to))
                    for sid, exit_count, presence in cur.fetchall():
                        event_stats[sid] = {'exit': exit_count, 'presence': presence}
                except Exception:
                    pass

            # Vider les cartes existantes
            for i in reversed(range(self._cards_layout.count())):
                w = self._cards_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()

            # Remplir les cartes
            cols = 3
            for idx, s in enumerate(self._students):
                sid = s['id']
                card = StudentCard(sid, s['name'])
                stats = event_stats.get(sid, {'exit': 0, 'presence': 'Présent'})
                card.set_exit_count(stats['exit'])
                color = '#e74c3c' if stats['presence'] == 'Absent' else '#27ae60'
                card.set_status(stats['presence'], color)
                card.clicked.connect(self._on_student_selected)
                self._cards_layout.addWidget(card, idx // cols, idx % cols)

            # Étendre la grille
            remaining = len(self._students) % cols
            if remaining:
                for _ in range(cols - remaining):
                    spacer = QWidget()
                    spacer.setFixedSize(160, 200)
                    self._cards_layout.addWidget(spacer, len(self._students) // cols, cols - remaining + _)

        except Exception as e:
            log(f"_load_students: {e}")

    def _on_student_selected(self, student_id: int):
        self._selected_student_id = student_id
        self._tt_slots.set_student(student_id)

        # Charger l'emploi du temps avec l'élève sélectionné
        if self._current_class_id:
            self._load_timetable(self._current_class_id, student_id)

    def _load_timetable(self, class_id: int, student_id: int = 0):
        if not self._current_term_id:
            return

        weekday = QDate.currentDate().dayOfWeek()
        # Convertir Qt dayOfWeek (1=Monday) en weekday de la base
        self._tt_slots.load(class_id, self._current_term_id, weekday, student_id)

    # ---- Utilitaires -------------------------------------------------------

    def _period_dates(self) -> tuple[str, str]:
        today = QDate.currentDate()
        if self._current_period == 'day':
            d = self._current_date.toString('yyyy-MM-dd')
            return d, d
        elif self._current_period == 'week':
            start = today.addDays(-(today.dayOfWeek() - 1))
            end = start.addDays(6)
            return start.toString('yyyy-MM-dd'), end.toString('yyyy-MM-dd')
        elif self._current_period == 'month':
            start = QDate(today.year(), today.month(), 1)
            end = QDate(today.year(), today.month(), today.daysInMonth())
            return start.toString('yyyy-MM-dd'), end.toString('yyyy-MM-dd')
        else:  # term
            # Trimestre = 3 mois glissants
            start = today.addMonths(-3)
            return start.toString('yyyy-MM-dd'), today.toString('yyyy-MM-dd')

    def refresh_all(self):
        self._update_network_label()
        if self._current_group_mode == 'class':
            self._show_class_mode(self._current_class_id)
        elif self._current_group_mode:
            self._show_group_mode(self._current_group_mode)

    def _refresh_timer(self):
        self._update_network_label()
        QTimer.singleShot(30000, self._refresh_timer)
