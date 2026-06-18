from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDateEdit, QFrame, QScrollArea, QGridLayout,
    QSplitter, QDialog, QDialogButtonBox, QTextEdit,
    QButtonGroup, QSizePolicy, QListWidget, QListWidgetItem,
    QMenu, QStackedWidget, QTabWidget, QCheckBox, QTimeEdit,
)
from PySide6.QtCore import Qt, QDate, QTimer, QSize, Signal, QDateTime, QTime, QCoreApplication
from PySide6.QtGui import QColor, QBrush, QPixmap, QFont, QIcon, QPainter, QPainterPath
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis,
    QValueAxis, QPieSeries, QLineSeries, QDateTimeAxis,
)
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session, UserRole
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.network import detect_network
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.photos import get_photo_path
import os, re


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
def _event_icon(event_type: str) -> str:
    icons = {'arrival': '▲', 'departure': '▼', 'exit': '→', 'return': '←',
             'absence': '✕', 'justified': '✓', 'late': '⏰'}
    if event_type in icons:
        return icons[event_type]
    if event_type.startswith('Bureau BI'):
        return '🔴'
    if event_type.startswith('Médical'):
        return '🏥'
    if event_type.startswith('Sortie'):
        return '🚪'
    if event_type.startswith('Suivi'):
        return '👁'
    return '●'

def _event_color(event_type: str) -> str:
    colors = {'arrival': '#27ae60', 'departure': '#2980b9', 'exit': '#e67e22',
              'return': '#2ecc71', 'absence': '#e74c3c', 'justified': '#95a5a6',
              'late': '#f1c40f'}
    if event_type in colors:
        return colors[event_type]
    if event_type.startswith('Bureau BI'):
        return '#d32f2f'
    if event_type.startswith('Médical'):
        return '#1976d2'
    if event_type.startswith('Sortie'):
        return '#e65100'
    if event_type.startswith('Suivi'):
        return '#f9a825'
    return '#555'


# ---------------------------------------------------------------------------
# Carte élève
# ---------------------------------------------------------------------------
class StudentCard(QFrame):
    clicked = Signal(int)  # student_id

    def __init__(self, student_id: int, last_name: str, first_name: str):
        super().__init__()
        self._sid = student_id
        self._last_name = last_name
        self._first_name = first_name
        self.setFrameShape(QFrame.StyledPanel)
        self._default_style = (
            f"StudentCard {{"
            f"  background: {theme_manager.palette.surface};"
            f"  border: 1px solid {theme_manager.palette.outline_variant};"
            f"  border-radius: 8px; padding: 8px;"
            f"}}"
            f"StudentCard:hover {{"
            f"  background: {theme_manager.palette.surface_variant};"
            f"  border-color: {theme_manager.palette.outline};"
            f"}}"
        )
        self.setStyleSheet(self._default_style)
        self.setFixedSize(124, 200)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Nom (en haut)
        self._name_label = QLabel()
        self._name_label.setTextFormat(Qt.RichText)
        self._name_label.setAlignment(Qt.AlignCenter)
        self._name_label.setText(
            f"<b style='font-size:{theme_manager.font_size(13)}px'>{last_name}</b><br>"
            f"<span style='font-size:{theme_manager.font_size(13)}px; color:{theme_manager.palette.text_soft}'>{first_name}</span>"
        )

        # Badge photo (conteneur coloré)
        self._photo_badge = QFrame()
        self._photo_badge.setFixedSize(89, 89)
        self._photo_badge.setStyleSheet(
            f"background: {theme_manager.palette.primary_container};"
            f"border-radius: 8px;"
        )
        badge_layout = QVBoxLayout(self._photo_badge)
        badge_layout.setAlignment(Qt.AlignCenter)
        badge_layout.setContentsMargins(0, 0, 0, 0)

        self._photo = QLabel()
        self._photo.setFixedSize(89, 89)
        self._photo.setAlignment(Qt.AlignCenter)

        pix = QPixmap(get_photo_path(student_id))
        if pix.isNull() or pix.size().isNull():
            pix = self._make_avatar(last_name, first_name)
        else:
            pix = pix.scaled(89, 89, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._photo.setPixmap(pix)

        badge_layout.addWidget(self._photo)

        # Statut
        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(f"font-size: {theme_manager.font_size(13)}px; font-weight: bold;")

        # Nb sorties
        self._exit_label = QLabel()
        self._exit_label.setAlignment(Qt.AlignCenter)
        self._exit_label.setStyleSheet(f"font-size: {theme_manager.font_size(8)}px; color: {theme_manager.palette.text_disabled};")

        layout.addWidget(self._name_label)
        layout.addStretch()
        layout.addWidget(self._photo_badge, 0, Qt.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(self._status_label)
        layout.addWidget(self._exit_label)
        self.setLayout(layout)

    def _make_avatar(self, last_name: str, first_name: str) -> QPixmap:
        initials = (last_name[:1] + first_name[:1]).upper() or '?'
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        c = colors[hash(last_name + first_name) % len(colors)]
        px = QPixmap(89, 89)
        px.fill(Qt.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(c))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 89, 89)
        p.setPen(QColor('#fff'))
        font = p.font()
        font.setPixelSize(34)
        font.setBold(True)
        p.setFont(font)
        p.drawText(px.rect(), Qt.AlignCenter, initials)
        p.end()
        return px

    def mousePressEvent(self, event):
        self.clicked.emit(self._sid)
        super().mousePressEvent(event)

    def set_status(self, text: str, color: str):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(
            f"font-size: {theme_manager.font_size(13)}px; font-weight: bold; color: {color};")

    def set_exit_count(self, count: int):
        self._exit_label.setText(f"{count} sortie(s)" if count else '')

    def set_absent(self, absent: bool):
        p = theme_manager.palette
        if absent:
            self.setStyleSheet(
                f"StudentCard {{"
                f"  background: {p.error_container};"
                f"  border: 2px solid {p.error};"
                f"  border-radius: 8px; padding: 8px;"
                f"}}"
                f"StudentCard:hover {{"
                f"  background: #FFC9C0; border-color: {p.error};"
                f"}}")
        else:
            self.setStyleSheet(self._default_style)


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


# ---------------------------------------------------------------------------
# Écran génération d'événement
# ---------------------------------------------------------------------------
class EventGenerator(QDialog):
    def __init__(self, student_id: int, parent=None):
        super().__init__(parent)
        self._student_id = student_id
        self._subjects = []
        self._locations = []
        self._classroom_lieu_ids = set()
        self._selected_lieu_id = 0
        self._selected_lieu_label = ""
        self._selected_category = None
        self._selected_niv2 = None
        self._selected_type_path = None
        self._type_hierarchy = {}
        self._student_classroom_id = None
        self._student_classroom_label = ""
        self.setWindowTitle(f"Événement — élève #{student_id}")
        self.setMinimumWidth(600)
        self._load_student_classroom()
        self._load_types_from_db()
        self._init_ui()

    def _load_student_classroom(self):
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.s_classroom_id, c.label
                FROM larcauth_student s
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                WHERE s.aecuser_ptr_id = %s
            """, (self._student_id,))
            r = cur.fetchone()
            if r:
                self._student_classroom_id = r[0]
                self._student_classroom_label = r[1]
        except Exception as e:
            log(f"EventGenerator._load_student_classroom: {e}")

    def _get_term_id(self) -> int:
        conn = db.server_conn
        if not conn:
            return 0
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id FROM larcauth_term t, larcauth_academicyear ay
                WHERE ay.s_id = 1 AND t.trim = ay.current_term_number
                ORDER BY t.id LIMIT 1
            """)
            r = cur.fetchone()
            return r[0] if r else 0
        except Exception as e:
            log(f"EventGenerator._get_term_id: {e}")
            return 0

    def _init_ui(self):
        layout = QVBoxLayout()
        p = theme_manager.palette
        s = theme_manager.font_size
        fs = 10
        sp = 8
        rd = 4
        conn = db.server_conn

        # --- 1. Infos élève ---
        student_name = f"Élève #{self._student_id}"
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT aec.last_name || ' ' || aec.first_name FROM larcauth_student s "
                    "JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id WHERE s.aecuser_ptr_id = %s",
                    (self._student_id,)
                )
                r = cur.fetchone()
                if r:
                    student_name = r[0]
            except Exception:
                pass
        top_row = QHBoxLayout()
        name_label = QLabel(f"<b>{student_name}</b>")
        name_label.setStyleSheet(f"font-size: {s(16)}px; padding: 8px; color: {p.text_strong};")
        top_row.addWidget(name_label)
        if self._student_classroom_label:
            top_row.addStretch()
            cls_label = QLabel(f"<b>{self._student_classroom_label}</b>")
            cls_label.setStyleSheet(f"font-size: {s(16)}px; padding: 8px; color: {p.text_soft};")
            top_row.addWidget(cls_label)
        layout.addLayout(top_row)

        # --- 2. Date et Heure séparées ---
        dt_frame = QFrame()
        dt_frame.setStyleSheet(
            f"background: {p.surface_variant}; border-radius: {rd}px; padding: 6px;")
        dt_layout = QHBoxLayout(dt_frame)
        dt_layout.setSpacing(sp)

        dt_layout.addWidget(QLabel("Date :"))
        self._date_edit = QDateEdit(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dddd dd MMMM yyyy")
        self._date_edit.setStyleSheet(
            f"padding: 6px; border: 1px solid {p.outline_variant}; border-radius: {rd}px; "
            f"font-size: {s(12)}px; background: {p.surface}; color: {p.text_strong}; "
            f"font-weight: bold;")
        dt_layout.addWidget(self._date_edit, 1)

        dt_layout.addWidget(QLabel("Heure :"))
        self._time_edit = QTimeEdit(QTime.currentTime())
        self._time_edit.setDisplayFormat("HH:mm")
        self._time_edit.setStyleSheet(
            f"padding: 6px; border: 1px solid {p.outline_variant}; border-radius: {rd}px; "
            f"font-size: {s(12)}px; background: {p.surface}; color: {p.text_strong}; "
            f"font-weight: bold;")
        dt_layout.addWidget(self._time_edit)

        self._source_label = QLabel()
        self._update_source_label()
        dt_layout.addWidget(self._source_label)
        layout.addWidget(dt_frame)

        # --- 3. Lieu ---
        layout.addSpacing(sp)
        lieu_header_row = QHBoxLayout()
        lieu_header_row.addWidget(QLabel("<b>Lieu :</b>"))
        if self._student_classroom_label:
            self._classe_label = QLabel(f"Classe : {self._student_classroom_label}")
            self._classe_label.setStyleSheet(f"font-size: {s(12)}px; color: {p.text_soft}; padding: 4px 8px;")
            lieu_header_row.addStretch()
            lieu_header_row.addWidget(self._classe_label)
        layout.addLayout(lieu_header_row)

        lieu_btn_style = (
            f"QPushButton {{ background: {p.surface}; color: {p.text_strong}; "
            f"border: 1px solid {p.outline_variant}; border-radius: 10px; "
            f"font-size: {s(11)}px; font-weight: bold; padding: 6px 12px; }}"
            f"QPushButton:hover {{ border: 2px solid {p.primary}; }}"
            f"QPushButton:checked {{ background: {p.primary_container}; "
            f"border: 2px solid {p.primary}; }}"
        )

        self._classroom_lieu_ids = set()
        self._lieu_group = QButtonGroup(self)
        self._lieu_group.setExclusive(True)
        lieu_grid = QGridLayout()
        lieu_grid.setSpacing(8)
        self._load_locations()
        for idx, (lid, sid, lieu_name) in enumerate(self._locations):
            btn = QPushButton(lieu_name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(64)
            btn.setStyleSheet(lieu_btn_style)
            if idx == 0:
                btn.setChecked(True)
                self._selected_lieu_id = lid
                self._selected_lieu_label = lieu_name
            self._lieu_group.addButton(btn, lid)
            lieu_grid.addWidget(btn, idx // 4, idx % 4)
            if sid == 1:
                self._classroom_lieu_ids.add(lid)
        self._lieu_group.buttonClicked.connect(self._on_lieu_changed)
        layout.addLayout(lieu_grid)

        # --- 4. Matière ---
        layout.addSpacing(sp)
        self._matiere_group_widget = QWidget()
        matiere_vbox = QVBoxLayout(self._matiere_group_widget)
        matiere_vbox.setContentsMargins(0, 0, 0, 0)
        matiere_vbox.addWidget(QLabel("<b>Matière :</b>"))

        self._subject_group = QButtonGroup(self)
        self._subject_group.setExclusive(True)
        self._subject_grid = QGridLayout()
        self._subject_grid.setSpacing(8)
        matiere_vbox.addLayout(self._subject_grid)
        self._load_subjects()
        layout.addWidget(self._matiere_group_widget)
        self._refresh_matiere_visibility()

        # --- 5. Type d'événement hiérarchique ---
        layout.addSpacing(sp)
        layout.addWidget(QLabel("<b>Type d'événement :</b>"))
        layout.addSpacing(4)

        # Barre de sélection cliquable (remplace _sel_label)
        self._sel_btn = QPushButton("")
        self._sel_btn.setStyleSheet(
            f"QPushButton {{ background: {p.surface_variant}; color: {p.primary}; "
            f"font-size: {s(12)}px; font-weight: bold; padding: 6px 12px; "
            f"border: 1px solid {p.outline_variant}; border-radius: {rd}px; text-align: left; }}"
            f"QPushButton:hover {{ border-color: {p.primary}; }}")
        self._sel_btn.setMinimumHeight(24)
        self._sel_btn.setCursor(Qt.PointingHandCursor)
        self._sel_btn.clicked.connect(self._on_sel_clicked)
        layout.addWidget(self._sel_btn)

        self._cat_colors = {'Bureau BI': '#d32f2f', 'Médical': '#1976d2',
                            'Sortie': '#e65100', 'Suivi': '#f9a825'}
        self._cat_group = QButtonGroup(self)

        # Zone de choix unique (stack)
        self._type_stack = QStackedWidget()

        # Page 0 : catégories
        self._type_page_niv1 = QWidget()
        cat_grid = QGridLayout(self._type_page_niv1)
        cat_grid.setSpacing(10)
        cats = list(self._type_hierarchy.keys())
        for idx, cat in enumerate(cats):
            bg = self._cat_colors.get(cat, '#888')
            fg = '#fff' if cat != 'Suivi' else '#222'
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(64)
            btn.setStyleSheet(
                f"QPushButton {{ background: {bg}; color: {fg}; font-weight: bold; "
                f"border: 2px solid {p.outline_variant}; border-radius: 10px; "
                f"font-size: {s(12)}px; padding: 8px 12px; }}"
                f"QPushButton:hover {{ border: 2px solid #fff; }}"
                f"QPushButton:checked {{ border: 3px solid #fff; background: {bg}; }}"
            )
            btn.toggled.connect(lambda checked, c=cat: self._on_cat_toggled(c) if checked else None)
            self._cat_group.addButton(btn)
            cat_grid.addWidget(btn, idx // 2, idx % 2)
        self._type_stack.addWidget(self._type_page_niv1)

        # Page 1 : niveau 2
        self._type_page_niv2 = QWidget()
        self._niv2_layout = QVBoxLayout(self._type_page_niv2)
        self._niv2_layout.setContentsMargins(0, 0, 0, 0)
        self._niv2_grid = QGridLayout()
        self._niv2_grid.setSpacing(8)
        self._niv2_layout.addLayout(self._niv2_grid)
        self._type_stack.addWidget(self._type_page_niv2)

        # Page 2 : niveau 3
        self._type_page_niv3 = QWidget()
        self._niv3_layout = QVBoxLayout(self._type_page_niv3)
        self._niv3_layout.setContentsMargins(0, 0, 0, 0)
        self._niv3_grid = QGridLayout()
        self._niv3_grid.setSpacing(8)
        self._niv3_layout.addLayout(self._niv3_grid)
        self._type_stack.addWidget(self._type_page_niv3)

        self._type_stack.setCurrentIndex(0)
        self._type_stack.setMinimumHeight(200)
        layout.addWidget(self._type_stack, 1)

        # --- 6. Note ---
        layout.addSpacing(sp)
        layout.addWidget(QLabel("<b>Note :</b>"))
        self._note_input = QTextEdit()
        self._note_input.setPlaceholderText("Note optionnelle (200 caractères max)")
        self._note_input.setMaximumHeight(80)
        self._note_input.setStyleSheet(
            f"padding: 4px; border: 1px solid {p.outline_variant}; border-radius: {rd}px; "
            f"font-size: {s(fs)}px; background: {p.surface}; color: {p.text_strong};")
        layout.addWidget(self._note_input)

        # --- 6. Boutons ---
        layout.addSpacing(sp)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet(f"font-size: {s(fs)}px;")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _load_subjects(self):
        self._clear_grid(self._subject_grid)
        if not self._student_classroom_id:
            return
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            term_id = self._get_term_id()
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
                """, (self._student_classroom_id, term_id))
            except Exception:
                cur.execute("""
                    SELECT cts.id, cts.label, cts.fk_teacher_id,
                           aec.last_name || ' ' || aec.first_name AS teacher_name
                    FROM larcauth_classroom_termsubject cts
                    LEFT JOIN larcauth_aecuser aec ON aec.id = cts.fk_teacher_id
                    WHERE cts.fk_classroom_id = %s
                      AND cts.enabled = TRUE
                    ORDER BY cts.label
                """, (self._student_classroom_id,))
            self._subjects = list(cur.fetchall())
            p = theme_manager.palette
            s = theme_manager.font_size
            subj_style = (
                f"QPushButton {{ background: {p.surface}; color: {p.text_strong}; "
                f"border: 1px solid {p.outline_variant}; border-radius: 10px; "
                f"font-size: {s(11)}px; font-weight: bold; padding: 6px 12px; }}"
                f"QPushButton:hover {{ border: 2px solid {p.primary}; }}"
                f"QPushButton:checked {{ background: {p.primary_container}; "
                f"border: 2px solid {p.primary}; }}"
            )
            for idx, (sid, label, tid, tname) in enumerate(self._subjects):
                display = label
                btn = QPushButton(display)
                btn.setCheckable(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumHeight(60)
                tip = tname or ""
                btn.setToolTip(tip)
                btn.setStyleSheet(subj_style)
                self._subject_group.addButton(btn, sid)
                self._subject_grid.addWidget(btn, idx // 4, idx % 4)
        except Exception as e:
            log(f"EventGenerator._load_subjects: {e}")

    def _load_locations(self):
        self._locations = []
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT ON ("s_IDLieu") "IDLieu", "s_IDLieu", "Lieu"
                FROM larcauth_lieu
                WHERE "fk_language" = 2 AND "IDLieu" > 0
                  AND "Lieu" NOT IN ('---', 'Non pr\u00e9cis\u00e9')
                ORDER BY "s_IDLieu", "IDLieu"
            """)
            self._locations = list(cur.fetchall())
        except Exception as e:
            log(f"EventGenerator._load_locations: {e}")

    def _on_lieu_changed(self, btn):
        lid = self._lieu_group.id(btn)
        self._selected_lieu_id = lid
        self._selected_lieu_label = btn.text()
        self._refresh_matiere_visibility()

    def _refresh_matiere_visibility(self):
        is_classroom = self._selected_lieu_id in self._classroom_lieu_ids
        visible = self._student_classroom_label and is_classroom
        self._matiere_group_widget.setVisible(visible)

    def _update_source_label(self):
        intranet_ok, _ = detect_network()
        p = theme_manager.palette
        s = theme_manager.font_size
        if intranet_ok and db.is_server_connected:
            self._source_label.setText("Intranet")
            self._source_label.setStyleSheet(f"color: {p.success}; font-size: {s(10)}px;")
        else:
            self._source_label.setText("Cloud")
            self._source_label.setStyleSheet(f"color: {p.primary}; font-size: {s(10)}px;")

    def _load_types_from_db(self):
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('''
                SELECT idtypeevent, type_event,
                       COALESCE("Event_Niveau2", '') AS niv2,
                       COALESCE("Event_Niveau3", '') AS niv3
                FROM larcauth_type_event
                WHERE "Enabled" IS NOT FALSE
                ORDER BY idtypeevent
            ''')
            self._type_hierarchy = {}
            for _, cat, niv2, niv3 in cur.fetchall():
                if cat not in self._type_hierarchy:
                    self._type_hierarchy[cat] = {}
                if niv2:
                    if niv2 not in self._type_hierarchy[cat]:
                        self._type_hierarchy[cat][niv2] = []
                    if niv3:
                        self._type_hierarchy[cat][niv2].append(niv3)
        except Exception as e:
            log(f"EventGenerator._load_types_from_db: {e}")
            self._type_hierarchy = {}

    def _on_cat_toggled(self, category: str):
        self._selected_category = category
        self._selected_niv2 = None
        self._selected_type_path = category
        self._populate_niv2(category)
        self._update_selection()

    def _populate_niv2(self, category: str):
        self._clear_grid(self._niv2_grid)
        niv2s = self._type_hierarchy.get(category, {})
        if not niv2s:
            self._type_stack.setCurrentIndex(0)
            return
        p = theme_manager.palette
        s = theme_manager.font_size
        ncols = 3
        for idx, niv2 in enumerate(niv2s):
            btn = QPushButton(niv2)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(60)
            btn.setStyleSheet(
                f"QPushButton {{ background: {p.surface}; color: {p.text_strong}; "
                f"border: 1px solid {p.outline_variant}; border-radius: 10px; "
                f"font-size: {s(11)}px; font-weight: bold; padding: 6px 12px; }}"
                f"QPushButton:hover {{ border: 2px solid {p.primary}; }}"
                f"QPushButton:checked {{ background: {p.primary_container}; "
                f"border: 2px solid {p.primary}; }}"
            )
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=niv2, c=category: self._on_niv2_clicked(n, c))
            self._niv2_grid.addWidget(btn, idx // ncols, idx % ncols)
        self._type_stack.setCurrentIndex(1)

    def _on_niv2_clicked(self, niv2: str, category: str):
        self._selected_niv2 = niv2
        self._selected_type_path = f"{category} > {niv2}"
        self._check_grid_button(self._niv2_grid, niv2)
        niv3s = self._type_hierarchy.get(category, {}).get(niv2, [])
        self._populate_niv3(niv3s)
        self._update_selection()

    def _populate_niv3(self, niv3s: list):
        self._clear_grid(self._niv3_grid)
        if not niv3s:
            self._type_stack.setCurrentIndex(1)
            return
        p = theme_manager.palette
        s = theme_manager.font_size
        for idx, niv3 in enumerate(niv3s):
            btn = QPushButton(niv3)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(60)
            btn.setStyleSheet(
                f"QPushButton {{ background: {p.surface}; color: {p.text_strong}; "
                f"border: 1px solid {p.outline_variant}; border-radius: 10px; "
                f"font-size: {s(11)}px; font-weight: bold; padding: 6px 12px; }}"
                f"QPushButton:hover {{ border: 2px solid {p.primary}; }}"
                f"QPushButton:checked {{ background: {p.tertiary_container}; "
                f"border: 2px solid {p.tertiary}; }}"
            )
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=niv3: self._on_niv3_clicked(n))
            self._niv3_grid.addWidget(btn, 0, idx)
        self._type_stack.setCurrentIndex(2)

    def _on_niv3_clicked(self, niv3: str):
        self._selected_type_path = f"{self._selected_category} > {self._selected_niv2} > {niv3}"
        self._check_grid_button(self._niv3_grid, niv3)
        self._update_selection()

    def _clear_grid(self, grid: QGridLayout):
        while grid.count():
            w = grid.takeAt(0).widget()
            if w: w.deleteLater()

    def _check_grid_button(self, grid: QGridLayout, text: str):
        for i in range(grid.count()):
            w = grid.itemAt(i).widget()
            if isinstance(w, QPushButton):
                w.setChecked(w.text() == text)

    def _update_selection(self):
        if self._selected_type_path:
            self._sel_btn.setText(f"✓ {self._selected_type_path}")
        else:
            self._sel_btn.setText("")

    def _on_sel_clicked(self):
        if not self._selected_type_path:
            return
        parts = self._selected_type_path.split(' > ')
        depth = len(parts)
        if depth == 1:
            self._type_stack.setCurrentIndex(0)
            self._cat_group.checkedButton().setChecked(False)
            self._selected_category = None
            self._selected_niv2 = None
            self._selected_type_path = ''
            self._update_selection()
        elif depth == 2:
            self._selected_niv2 = None
            self._selected_type_path = parts[0]
            self._populate_niv2(parts[0])
            self._type_stack.setCurrentIndex(1)
        elif depth == 3:
            self._populate_niv2(parts[0])
            self._on_niv2_clicked(parts[1], parts[0])
            self._type_stack.setCurrentIndex(2)

    def _validate(self):
        if not self._selected_type_path:
            QMessageBox.warning(self, "Erreur", "Sélectionnez un type d'événement.")
            return
        self.accept()

    def get_data(self) -> dict:
        dt = self._date_edit.dateTime()
        dt.setTime(self._time_edit.time())
        subj_id = self._subject_group.checkedId()
        return {
            'student_id': self._student_id,
            'event_type': self._selected_type_path,
            'event_at': dt.toString('yyyy-MM-dd HH:mm:ss'),
            'classroom_id': self._student_classroom_id,
            'classroom_label': self._student_classroom_label,
            'lieu_id': self._selected_lieu_id,
            'lieu_label': self._selected_lieu_label,
            'subject_id': subj_id if subj_id >= 0 else None,
            'subject_label': self._subject_group.checkedButton().text() if subj_id >= 0 else '',
            'note': self._note_input.toPlainText().strip(),
            'source': 'cloud' if not detect_network()[0] else 'intranet',
        }


# ---------------------------------------------------------------------------
# Fenêtre principale
# ---------------------------------------------------------------------------
class MainWindow(QWidget):
    @property
    def _STYLE(self) -> str:
        p = theme_manager.palette
        f = theme_manager.fonts
        s = theme_manager.font_size
        return f"""
            QFrame#top_bar {{
                background: {p.surface}; border: 1px solid {p.outline_variant};
                border-radius: 6px;
            }}
            QFrame#panel {{
                background: {p.surface}; border: 1px solid {p.outline_variant};
                border-radius: 6px;
            }}
            QLabel#panel_title {{
                font-size: {s(f.title)}px; font-weight: bold; padding: 4px;
                color: {p.text_strong};
            }}
            QTableWidget {{
                background: {p.surface}; color: {p.text_strong};
                gridline-color: {p.outline_variant};
                border: none; font-size: {s(f.base)}px;
            }}
            QTableWidget::item {{
                padding: 2px 6px;
            }}
            QHeaderView::section {{
                background: {p.surface_variant}; color: {p.text_strong};
                padding: 4px; border: none; font-weight: bold; font-size: {s(f.small)}px;
            }}
            QComboBox {{
                background: {p.surface}; color: {p.text_strong};
                border: 1px solid {p.outline_variant}; border-radius: 4px;
                padding: 4px 8px; font-size: {s(f.base)}px;
            }}
            QComboBox:hover {{
                border-color: {p.primary};
            }}
            QComboBox::drop-down {{
                border: none; width: 20px;
            }}
            QPushButton {{
                background: {p.surface}; color: {p.primary};
                border: 1px solid {p.outline_variant}; border-radius: 4px;
                padding: 4px 12px; font-size: {s(f.button)}px;
            }}
            QPushButton:hover {{
                background: {p.primary_container}; border-color: {p.primary};
            }}
            QPushButton:pressed {{
                background: {p.primary}; color: {p.on_primary};
            }}
            QPushButton#today_btn {{
                background: {p.primary}; color: {p.on_primary};
                border: none; font-weight: bold;
            }}
            QPushButton#today_btn:hover {{
                background: {p.primary};
            }}
            QPushButton#theme_btn {{
                background: transparent; border: none; font-size: 18px;
            }}
            QPushButton#section_btn {{
                background: transparent; border: none; font-weight: bold;
                text-align: left; padding: 2px 4px; font-size: {s(f.base)}px;
            }}
            QPushButton#class_btn {{
                border: none; border-radius: 4px; text-align: left;
                padding: 3px 8px; font-size: {s(f.small)}px;
            }}
            QPushButton#class_btn:hover {{
                background: {p.primary_container};
            }}
            QPushButton#class_btn:checked {{
                font-weight: bold;
            }}
        """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"LarcSuperviseur — {session.full_name} ({session.role.value})")
        self._current_class_id: int = 0
        self._current_class_label: str = ''
        self._selected_btn: QPushButton | None = None
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
        self.setStyleSheet(self._STYLE)
        outer = QVBoxLayout()
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(6)

        # -- Top bar (minimal) ------------------------------------------------
        top = QFrame()
        top.setObjectName("top_bar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(10, 6, 10, 6)

        self._date_label = QLabel()
        self._date_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {theme_manager.palette.text_strong};")
        self._time_label = QLabel()
        self._time_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {theme_manager.palette.primary};")
        self._update_datetime()

        self._period_combo = QComboBox()
        self._period_combo.addItem("Jour", 'day')
        self._period_combo.addItem("Semaine", 'week')
        self._period_combo.addItem("Mois", 'month')
        self._period_combo.addItem("Trimestre", 'term')
        self._period_combo.currentIndexChanged.connect(self._on_period_changed)

        self._today_btn = QPushButton("Aujourd'hui")
        self._today_btn.clicked.connect(self._go_today)
        self._today_btn.setFixedWidth(100)

        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setFixedWidth(36)
        self._refresh_btn.clicked.connect(self.refresh_all)

        self._theme_btn = QPushButton("🎨")
        self._theme_btn.setObjectName("theme_btn")
        self._theme_btn.setFixedWidth(36)
        self._theme_menu = QMenu()
        for key, label in theme_manager.names():
            a = self._theme_menu.addAction(label)
            a.setData(key)
        self._theme_menu.triggered.connect(self._on_theme_selected)
        self._theme_btn.setMenu(self._theme_menu)

        self._network_label = QLabel()
        self._update_network_label()

        top_layout.addWidget(self._date_label)
        top_layout.addWidget(self._time_label)
        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("Période :"))
        top_layout.addWidget(self._period_combo)
        top_layout.addSpacing(10)
        top_layout.addWidget(self._today_btn)
        top_layout.addWidget(self._refresh_btn)
        top_layout.addWidget(self._theme_btn)
        self._loading_label = QLabel()
        self._loading_label.setStyleSheet(
            f"font-size: 13px; color: {theme_manager.palette.primary}; font-weight: bold;")
        self._loading_label.setVisible(False)
        top_layout.addWidget(self._loading_label)
        top_layout.addStretch()
        top_layout.addWidget(self._network_label)

        # -- Clock timer ------------------------------------------------------
        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_datetime)
        self._clock_timer.start(10000)

        # -- Main area (sidebar + content) ------------------------------------
        main_h = QHBoxLayout()
        main_h.setSpacing(6)

        # Sidebar gauche
        self._sidebar = QFrame()
        self._sidebar.setObjectName("panel")
        self._sidebar.setFixedWidth(260)
        self._sidebar_layout = QVBoxLayout(self._sidebar)
        self._sidebar_layout.setContentsMargins(6, 6, 6, 6)
        self._sidebar_layout.setSpacing(2)

        # Content area
        self._content_stack = QStackedWidget()

        # Page 0: Mode groupe (KPIs + charts + tables)
        self._group_page = QWidget()
        self._group_scroll = QScrollArea()
        self._group_scroll.setWidgetResizable(True)
        self._group_scroll.setWidget(self._group_page)
        self._group_scroll.setFrameShape(QFrame.NoFrame)
        group_layout = QVBoxLayout(self._group_page)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(8)

        # -- Ligne KPIs (4 cartes) --
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(8)
        self._kpi_cards = {}
        for k, label in [('total', 'Total élèves'), ('present', 'Présents'),
                          ('absent', 'Absents'), ('exit', 'Sorties')]:
            card = QFrame()
            card.setObjectName("kpi_card")
            card.setFixedHeight(80)
            card.setStyleSheet(
                f"QFrame#kpi_card {{ background: {theme_manager.palette.surface_variant}; "
                f"border-radius: 8px; padding: 4px; }}")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 4, 8, 4)
            val = QLabel("—")
            val.setObjectName("kpi_value")
            val.setStyleSheet(
                f"font-size: {theme_manager.font_size(24)}px; font-weight: bold; "
                f"color: {theme_manager.palette.primary};")
            val.setAlignment(Qt.AlignCenter)
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"font-size: {theme_manager.font_size(10)}px; color: {theme_manager.palette.text_soft};")
            lbl.setAlignment(Qt.AlignCenter)
            cl.addWidget(val)
            cl.addWidget(lbl)
            self._kpi_cards[k] = val
            kpi_row.addWidget(card)
        group_layout.addLayout(kpi_row)

        # -- Historique événements (juste après les KPIs) --
        self._history_group = QFrame()
        self._history_group.setObjectName("panel")
        self._history_layout = QVBoxLayout(self._history_group)
        history_title = QLabel("<b>Historique des événements</b>")
        history_title.setObjectName("panel_title")
        self._history_table = QTableWidget()
        self._history_table.setAlternatingRowColors(True)
        self._history_table.horizontalHeader().setStretchLastSection(True)
        self._history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._history_table.setSortingEnabled(True)
        self._history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._history_table.customContextMenuRequested.connect(
            lambda pos: self._show_event_context_menu(self._history_table, pos))
        self._history_table.cellDoubleClicked.connect(self._on_event_table_dblclick)
        self._history_layout.addWidget(history_title)
        # -- Filtres --
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        self._history_filter_class = QComboBox()
        self._history_filter_class.setMinimumWidth(150)
        self._history_filter_class.addItem("Toutes les classes", '')
        filter_row.addWidget(QLabel("Classe:"))
        filter_row.addWidget(self._history_filter_class)
        self._history_filter_type = QComboBox()
        self._history_filter_type.setMinimumWidth(180)
        self._history_filter_type.setEditable(True)
        self._history_filter_type.lineEdit().setPlaceholderText("Type événement...")
        filter_row.addWidget(QLabel("Type:"))
        filter_row.addWidget(self._history_filter_type)
        filter_row.addSpacing(10)
        self._history_filter_date_from = QDateEdit()
        self._history_filter_date_from.setCalendarPopup(True)
        self._history_filter_date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_row.addWidget(QLabel("Du:"))
        filter_row.addWidget(self._history_filter_date_from)
        self._history_filter_date_to = QDateEdit()
        self._history_filter_date_to.setCalendarPopup(True)
        self._history_filter_date_to.setDate(QDate.currentDate())
        filter_row.addWidget(QLabel("Au:"))
        filter_row.addWidget(self._history_filter_date_to)
        filter_btn = QPushButton("Filtrer")
        filter_btn.setCursor(Qt.PointingHandCursor)
        filter_btn.clicked.connect(lambda: self._load_global_history(self._current_group_mode))
        filter_row.addWidget(filter_btn)
        filter_row.addStretch()
        self._history_layout.addLayout(filter_row)
        self._history_layout.addWidget(self._history_table)
        self._history_group.setMinimumHeight(320)
        group_layout.addWidget(self._history_group, 1)

        # -- Bottom row: charts (tabbed) + stats table --
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self._charts_tabs = QTabWidget()
        self._charts_tabs.setMinimumSize(420, 300)

        tab_abs = QWidget()
        tab_abs_layout = QVBoxLayout(tab_abs)
        tab_abs_layout.setContentsMargins(0, 0, 0, 0)
        self._abs_bar_view = QChartView()
        self._abs_bar_view.setRenderHint(QPainter.Antialiasing)
        self._abs_bar_view.setObjectName("panel")
        self._abs_bar = QChart()
        self._abs_bar_view.setChart(self._abs_bar)
        tab_abs_layout.addWidget(self._abs_bar_view)
        self._charts_tabs.addTab(tab_abs, "Absences")

        tab_exit = QWidget()
        tab_exit_layout = QVBoxLayout(tab_exit)
        tab_exit_layout.setContentsMargins(0, 0, 0, 0)
        self._exit_bar_view = QChartView()
        self._exit_bar_view.setRenderHint(QPainter.Antialiasing)
        self._exit_bar_view.setObjectName("panel")
        self._exit_bar = QChart()
        self._exit_bar_view.setChart(self._exit_bar)
        tab_exit_layout.addWidget(self._exit_bar_view)
        self._charts_tabs.addTab(tab_exit, "Sorties")

        tab_trend = QWidget()
        tab_trend_layout = QVBoxLayout(tab_trend)
        tab_trend_layout.setContentsMargins(0, 0, 0, 0)
        self._trend_view = QChartView()
        self._trend_view.setRenderHint(QPainter.Antialiasing)
        self._trend_view.setObjectName("panel")
        self._trend_chart = QChart()
        self._trend_chart.setAnimationOptions(QChart.SeriesAnimations)
        self._trend_view.setChart(self._trend_chart)
        tab_trend_layout.addWidget(self._trend_view)
        self._charts_tabs.addTab(tab_trend, "Tendance")

        tab_donut = QWidget()
        tab_donut_layout = QVBoxLayout(tab_donut)
        tab_donut_layout.setContentsMargins(0, 0, 0, 0)
        self._donut_view = QChartView()
        self._donut_view.setRenderHint(QPainter.Antialiasing)
        self._donut_view.setObjectName("panel")
        self._donut_chart = QChart()
        self._donut_view.setChart(self._donut_chart)
        tab_donut_layout.addWidget(self._donut_view)
        self._charts_tabs.addTab(tab_donut, "Taux présence")

        bottom_row.addWidget(self._charts_tabs, 3)

        self._stats_group = QFrame()
        self._stats_group.setObjectName("panel")
        self._stats_layout = QVBoxLayout(self._stats_group)
        stats_title = QLabel("<b>Statistiques par classe</b>")
        stats_title.setObjectName("panel_title")
        self._stats_table = QTableWidget()
        self._stats_table.setAlternatingRowColors(True)
        self._stats_table.horizontalHeader().setStretchLastSection(True)
        self._stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._stats_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._stats_layout.addWidget(stats_title)
        self._stats_layout.addWidget(self._stats_table)
        bottom_row.addWidget(self._stats_group, 2)

        group_layout.addLayout(bottom_row)

        # Page 1: Mode classe (cards empilées avec détail élève)
        self._class_page = QWidget()
        class_layout = QVBoxLayout(self._class_page)
        class_layout.setContentsMargins(0, 0, 0, 0)

        self._class_stack = QStackedWidget()

        # -- Page 0 : Cartes élèves --
        self._cards_widget = QWidget()
        self._cards_layout = QGridLayout(self._cards_widget)
        self._cards_layout.setSpacing(8)
        self._cards_scroll = QScrollArea()
        self._cards_scroll.setWidget(self._cards_widget)
        self._cards_scroll.setWidgetResizable(True)
        cards_frame = QFrame()
        cards_frame.setObjectName("panel")
        cards_frame_layout = QVBoxLayout(cards_frame)
        cards_frame_layout.setContentsMargins(0, 0, 0, 0)
        # Header row: titre à gauche, bouton EDT à droite
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        self._cards_title = QLabel("<b>Élèves</b>")
        self._cards_title.setObjectName("panel_title")
        header_row.addWidget(self._cards_title)
        header_row.addStretch()
        self._tt_edit_btn = QPushButton("🕐 Emploi du temps")
        self._tt_edit_btn.setStyleSheet(
            f"QPushButton {{ background: {theme_manager.palette.surface_variant}; "
            f"color: {theme_manager.palette.text_strong}; border: none; "
            f"border-radius: 4px; padding: 4px 8px; "
            f"font-size: {theme_manager.font_size(10)}px; }}"
            f"QPushButton:hover {{ background: {theme_manager.palette.primary}; "
            f"color: {theme_manager.palette.on_primary}; }}")
        self._tt_edit_btn.setCursor(Qt.PointingHandCursor)
        self._tt_edit_btn.clicked.connect(self._on_edit_timetable)
        header_row.addWidget(self._tt_edit_btn)
        cards_frame_layout.addLayout(header_row)
        cards_frame_layout.addWidget(self._cards_scroll)
        self._class_stack.addWidget(cards_frame)  # index 0

        # -- Page 1 : Détail élève --
        self._build_student_detail()

        class_layout.addWidget(self._class_stack)
        # Ajouter le détail élève au stack (page 1)
        self._class_stack.addWidget(self._student_detail)  # index 1

        self._content_stack.addWidget(self._group_scroll)   # 0
        self._content_stack.addWidget(self._class_page)    # 1
        self._content_stack.setCurrentIndex(0)

        main_h.addWidget(self._sidebar)
        main_h.addWidget(self._content_stack, 1)

        outer.addWidget(top)
        outer.addLayout(main_h)
        self.setLayout(outer)

    def _build_student_detail(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        self._student_detail = QFrame()
        self._student_detail.setObjectName("panel")
        sd_layout = QVBoxLayout(self._student_detail)
        sd_layout.setContentsMargins(6, 6, 6, 6)
        sd_layout.setSpacing(6)

        # Header row
        sd_header_row = QHBoxLayout()
        back_btn = QPushButton("← Retour")
        back_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {p.primary}; "
            f"border: none; font-weight: bold; "
            f"font-size: {s(11)}px; padding: 2px 6px; }}"
            f"QPushButton:hover {{ color: {p.active}; }}")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._on_back_to_cards)
        sd_header_row.addWidget(back_btn)
        sd_header_row.addStretch()
        sd_layout.addLayout(sd_header_row)

        self._sd_header = QLabel("<b>Élève</b>")
        self._sd_header.setObjectName("panel_title")
        self._sd_class = QLabel()
        self._sd_class.setStyleSheet(f"color: {p.text_soft}; font-size: {s(11)}px;")
        sd_layout.addWidget(self._sd_header)
        sd_layout.addWidget(self._sd_class)

        # Tabs
        self._sd_tabs = QTabWidget()
        self._sd_tabs.setDocumentMode(True)

        # ---- Tab 1 : Coordonnées ----
        scroll1 = QScrollArea()
        scroll1.setWidgetResizable(True)
        scroll1.setFrameShape(QFrame.NoFrame)
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        t1_layout.setContentsMargins(4, 4, 4, 4)
        t1_layout.setSpacing(6)

        # Photo + infos + add event button
        contact_row = QHBoxLayout()
        self._sd_photo = QLabel()
        self._sd_photo.setFixedSize(150, 150)
        self._sd_photo.setStyleSheet(
            f"background: {p.surface_variant}; border-radius: 8px;")
        self._sd_photo.setAlignment(Qt.AlignCenter)
        contact_row.addWidget(self._sd_photo)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self._sd_contact_labels = {}
        for key, lbl in [
            ('full_name', 'Nom'),
            ('email', 'Email'),
            ('email_perso', 'Email personnel'),
            ('tel_maison', 'Téléphone maison'),
            ('tel_portable', 'Téléphone portable'),
            ('date_entree', "Date d'entrée"),
        ]:
            w = QLabel()
            w.setStyleSheet(f"font-size: {s(12)}px; color: {p.text_soft};")
            w.setWordWrap(True)
            self._sd_contact_labels[key] = w
            info_col.addWidget(w)
        info_col.addStretch()
        contact_row.addLayout(info_col, 1)

        self._sd_add_btn = QPushButton("➕")
        self._sd_add_btn.setFixedSize(100, 100)
        self._sd_add_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 12px; font-weight: bold; "
            f"font-size: {s(28)}px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}")
        self._sd_add_btn.setCursor(Qt.PointingHandCursor)
        self._sd_add_btn.setToolTip("Ajouter un événement")
        self._sd_add_btn.clicked.connect(self._on_add_event)
        contact_row.addWidget(self._sd_add_btn)

        t1_layout.addLayout(contact_row)

        # KPIs
        kpi_r = QHBoxLayout()
        kpi_r.setSpacing(4)
        self._sd_kpis = {}
        for k, lbl in [('abs', 'Absences'), ('exit', 'Sorties'), ('total', 'Total évts')]:
            f = QFrame()
            f.setObjectName("kpi_small")
            f.setStyleSheet(
                f"QFrame#kpi_small {{ background: {p.surface_variant}; "
                f"border-radius: 6px; padding: 2px; }}")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(4, 2, 4, 2)
            v = QLabel("—")
            v.setStyleSheet(f"font-size: {s(18)}px; font-weight: bold; color: {p.primary};")
            v.setAlignment(Qt.AlignCenter)
            l = QLabel(lbl)
            l.setStyleSheet(f"font-size: {s(9)}px; color: {p.text_soft};")
            l.setAlignment(Qt.AlignCenter)
            fl.addWidget(v)
            fl.addWidget(l)
            self._sd_kpis[k] = v
            kpi_r.addWidget(f)
        t1_layout.addLayout(kpi_r)

        # Events
        evt_label = QLabel("<b>Derniers événements</b>")
        evt_label.setStyleSheet(f"font-size: {s(11)}px;")
        self._sd_events = QTableWidget()
        self._sd_events.setAlternatingRowColors(True)
        self._sd_events.horizontalHeader().setStretchLastSection(True)
        self._sd_events.setEditTriggers(QTableWidget.NoEditTriggers)
        self._sd_events.setSelectionBehavior(QTableWidget.SelectRows)
        self._sd_events.setContextMenuPolicy(Qt.CustomContextMenu)
        self._sd_events.customContextMenuRequested.connect(
            lambda pos: self._show_event_context_menu(self._sd_events, pos))
        self._sd_events.cellDoubleClicked.connect(self._on_event_table_dblclick)
        t1_layout.addWidget(evt_label)
        t1_layout.addWidget(self._sd_events, 1)

        # Bottom row: chart tabs
        self._sd_chart_tabs = QTabWidget()
        self._sd_chart_tabs.setMinimumHeight(200)

        tab_chart = QWidget()
        tab_chart_layout = QVBoxLayout(tab_chart)
        tab_chart_layout.setContentsMargins(0, 0, 0, 0)
        self._sd_chart_view = QChartView()
        self._sd_chart_view.setRenderHint(QPainter.Antialiasing)
        self._sd_chart = QChart()
        self._sd_chart_view.setChart(self._sd_chart)
        tab_chart_layout.addWidget(self._sd_chart_view)
        self._sd_chart_tabs.addTab(tab_chart, "Évolution absences")

        t1_layout.addWidget(self._sd_chart_tabs)

        scroll1.setWidget(tab1)

        # ---- Tab 2 : Parents ----
        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setFrameShape(QFrame.NoFrame)
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        t2_layout.setAlignment(Qt.AlignCenter)
        placeholder2 = QLabel("Les informations sur les parents/tuteurs\nseront bientôt disponibles.")
        placeholder2.setAlignment(Qt.AlignCenter)
        placeholder2.setStyleSheet(f"color: {p.text_disabled}; font-size: {s(13)}px;")
        t2_layout.addWidget(placeholder2)
        scroll2.setWidget(tab2)

        self._sd_tabs.addTab(scroll1, "Coordonnées")
        self._sd_tabs.addTab(scroll2, "Parents")

        sd_layout.addWidget(self._sd_tabs, 1)

        # Placeholder quand aucun élève sélectionné
        self._sd_placeholder = QLabel("Sélectionnez un élève\ndans la liste")
        self._sd_placeholder.setAlignment(Qt.AlignCenter)
        self._sd_placeholder.setStyleSheet(f"color: {p.text_disabled}; font-size: {s(14)}px;")
        sd_layout.addWidget(self._sd_placeholder)

        self._sd_tabs.hide()
        self._student_detail.hide()

    def _rebuild_student_detail_theme(self):
        if hasattr(self, '_student_detail') and self._student_detail:
            idx = self._class_stack.indexOf(self._student_detail)
            if idx >= 0:
                self._class_stack.removeWidget(self._student_detail)
                self._student_detail.deleteLater()
            self._build_student_detail()
            self._class_stack.insertWidget(1, self._student_detail)
            self._student_detail.hide()

    def _build_sidebar(self):
        layout = self._sidebar_layout
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        p = theme_manager.palette
        s = theme_manager.font_size
        prog_style = {
            'PEI':  (p.primary, p.primary_container, p.on_primary, 'PEI'),
            'MYP':  (p.secondary, p.secondary_container, p.on_secondary, 'MYP'),
            'DPFr': (p.error, p.error_container, p.on_error, 'DP'),
            'DPEn': (p.tertiary, p.tertiary_container, p.on_tertiary, 'DPEn'),
        }

        groups = {k: [] for k in ['PEI', 'MYP', 'DPEn', 'DPFr']}
        for cid, label, pid, sigle in self._classes:
            if sigle in groups:
                groups[sigle].append((cid, label))

        def _make_btn(ss, min_h=32):
            b = QPushButton()
            b.setMinimumHeight(min_h)
            b.setStyleSheet(ss)
            b.setCursor(Qt.PointingHandCursor)
            return b

        # Sections : Collège (PEI | MYP), Lycée (DP | DPEn)
        sections = [
            ('Collège', [('PEI', 'PEI'), ('MYP', 'MYP')]),
            ('Lycée',   [('DP', 'DPFr'), ('DPEn', 'DPEn')]),
        ]

        for sec_name, columns in sections:
            # Section header
            sec_hdr = _make_btn(
                f"QPushButton {{ background: transparent; color: {p.text_strong}; "
                f"border: none; border-bottom: 2px solid {p.outline_variant}; "
                f"font-weight: bold; font-size: {s(12)}px; text-align: left; padding: 4px 2px; }}"
                f"QPushButton:hover {{ color: {p.primary}; border-bottom: 2px solid {p.primary}; }}",
                min_h=28
            )
            sec_hdr.setText(sec_name)
            sec_hdr.clicked.connect(lambda checked, sn=sec_name: self._on_section_clicked(sn))
            layout.addWidget(sec_hdr)

            # Mini-grille 2 colonnes pour cette section
            grd = QGridLayout()
            grd.setSpacing(2)

            for col_idx, (hdr_text, prog_key) in enumerate(columns):
                fg, bg, on_fg, _ = prog_style[prog_key]
                items = groups.get(prog_key, [])

                col_hdr = _make_btn(
                    f"QPushButton {{ background: {fg}; color: {on_fg}; border: none; "
                    f"border-radius: 4px; font-weight: bold; font-size: {s(10)}px; padding: 3px; }}"
                    f"QPushButton:hover {{ opacity: 0.8; }}",
                    min_h=26
                )
                col_hdr.setText(hdr_text)
                col_hdr.clicked.connect(lambda checked, pk=prog_key: self._on_prog_clicked(pk))
                grd.addWidget(col_hdr, 0, col_idx)

                for i, (cid, label) in enumerate(items):
                    btn = _make_btn(
                        f"QPushButton {{ background: {bg}; color: {fg}; border: none; "
                        f"border-radius: 4px; font-size: {s(10)}px; padding: 2px; }}"
                        f"QPushButton:hover {{ background: {fg}; color: {bg}; }}",
                        min_h=32
                    )
                    btn.setText(label)
                    btn.clicked.connect(lambda checked, c=cid, l=label, b=btn: self._on_class_clicked(c, l, b))
                    grd.addWidget(btn, i + 1, col_idx)

            layout.addLayout(grd)
            layout.addSpacing(4)

        # Toutes les classes
        self._all_btn = _make_btn(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; font-weight: bold; font-size: {s(11)}px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}",
            min_h=36
        )
        self._all_btn.setText("📊 Toutes les classes")
        self._all_btn.clicked.connect(self._on_all_clicked)
        layout.addWidget(self._all_btn)
        layout.addStretch()

    def _on_section_clicked(self, section: str):
        mode_map = {'Collège': 'grp_college', 'Lycée': 'grp_lycee'}
        self._current_group_mode = mode_map[section]
        self._current_class_id = 0
        self._current_class_label = section
        self._select_btn(None)
        self._show_group_mode(mode_map[section])

    def _on_prog_clicked(self, prog: str):
        self._current_group_mode = f'grp_{prog.lower()}'
        self._current_class_id = 0
        self._current_class_label = prog
        self._select_btn(None)
        self._show_group_mode(f'grp_{prog.lower()}')

    def _on_class_clicked(self, class_id: int, label: str, btn: QPushButton | None = None):
        self._current_class_id = class_id
        self._current_class_label = label
        self._current_group_mode = 'class'
        self._select_btn(btn)
        self._show_class_mode(class_id)

    def _on_all_clicked(self):
        self._current_group_mode = 'grp_all'
        self._current_class_id = 0
        self._current_class_label = ''
        self._select_btn(None)
        self._show_group_mode('grp_all')

    def _select_btn(self, btn: QPushButton | None):
        if self._selected_btn:
            old_style = self._selected_btn.property('_normal_style') or ''
            self._selected_btn.setStyleSheet(old_style)
        self._selected_btn = btn
        if btn:
            btn.setProperty('_normal_style', btn.styleSheet())
            ss = btn.styleSheet()
            # Inverser fond/texte pour l'état sélectionné
            for line in ss.split('}'):
                if 'QPushButton' in line and 'QPushButton:hover' not in line:
                    bg = re.search(r'background:\s*([^;]+)', line)
                    fg = re.search(r'color:\s*([^;]+)', line)
                    if bg and fg:
                        btn.setStyleSheet(
                            f"QPushButton {{ background: {fg.group(1)}; color: {bg.group(1)}; "
                            f"border: 2px solid {fg.group(1)}; border-radius: 4px; "
                            f"font-size: {theme_manager.font_size(10)}px; padding: 2px; }}"
                            f"QPushButton:hover {{ background: {fg.group(1)}; color: white; }}"
                        )
                    break

    def _update_datetime(self):
        from datetime import datetime
        now = datetime.now()
        self._date_label.setText(now.strftime("%A %d %B %Y") + '  ')
        self._time_label.setText(now.strftime("%H:%M") + '  ')

    def _update_network_label(self):
        intranet_ok, internet_ok = detect_network()
        p = theme_manager.palette
        s = theme_manager.font_size
        if intranet_ok:
            self._network_label.setText("Intranet ●")
            self._network_label.setStyleSheet(f"color: {p.success}; font-weight: bold; font-size: {s(12)}px;")
        elif internet_ok:
            self._network_label.setText("Cloud ●")
            self._network_label.setStyleSheet(f"color: {p.primary}; font-weight: bold; font-size: {s(12)}px;")
        else:
            self._network_label.setText("Hors ligne")
            self._network_label.setStyleSheet(f"color: {p.text_disabled}; font-size: {s(12)}px;")

    def _set_loading(self, busy: bool, msg: str = "Chargement..."):
        self._loading_label.setText("⟳ " + msg if busy else "")
        self._loading_label.setVisible(busy)
        QCoreApplication.processEvents()

    def _load_initial_data(self):
        self._set_loading(True, "Données initiales...")
        conn = db.server_conn
        if not conn:
            QMessageBox.warning(self, "Erreur", "Non connecté au serveur.")
            self._set_loading(False)
            return

        try:
            cur = conn.cursor()

            # Terme actif (en fonction de la date courante)
            cur.execute("""
                SELECT id FROM larcauth_term
                WHERE start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE
                LIMIT 1
            """)
            r = cur.fetchone()
            self._current_term_id = int(r[0]) if r else 0

            # Programmes (PEI, DP, ...)
            cur.execute("SELECT id, sigle, label FROM larcauth_program ORDER BY sigle")
            self._programs = {r[0]: {'sigle': r[1], 'label': r[2]} for r in cur.fetchall()}

            # Classes avec leur programme via level (Collège + Lycée uniquement)
            cur.execute("""
                SELECT c.id, c.label, l.fk_program_id, p.sigle
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE c.enabled = TRUE AND p.sigle IN ('PEI', 'MYP', 'DPEn', 'DPFr')
                ORDER BY p.sigle, c.label
            """)
            self._classes = cur.fetchall()

            # Construire la sidebar
            self._build_sidebar()

            # Activer le mode groupe par défaut
            self._on_all_clicked()
            self._set_loading(False)

        except Exception as e:
            log(f"_load_initial_data: {e}")
            QMessageBox.critical(self, "Erreur", str(e))
            self._set_loading(False)

    def _on_period_changed(self, idx: int):
        if idx < 0:
            return
        self._current_period = self._period_combo.itemData(idx)
        self.refresh_all()

    def _on_theme_selected(self, action):
        key = action.data()
        if key:
            theme_manager.set_active(key)
            self.setStyleSheet(self._STYLE)
            # Reconstruire les composants qui ont des couleurs inline
            self._build_sidebar()
            self._rebuild_student_detail_theme()
            self._update_network_label()
            if self._current_group_mode:
                self.refresh_all()

    # ---- Mode groupe -------------------------------------------------------

    def _show_group_mode(self, mode: str):
        self._content_stack.setCurrentIndex(0)
        self._group_scroll.verticalScrollBar().setValue(0)
        self._load_group_stats(mode)
        self._load_global_history(mode)

    def _load_group_stats(self, mode: str):
        self._set_loading(True, "Statistiques...")
        conn = db.server_conn
        if not conn or not self._current_term_id:
            self._set_loading(False)
            return

        p = theme_manager.palette
        date_from, date_to = self._period_dates()

        try:
            cur = conn.cursor()

            if mode == 'grp_all':
                class_filter = "AND p.sigle IN ('PEI', 'MYP', 'DPEn', 'DPFr')"
            elif mode == 'grp_college':
                class_filter = "AND (p.sigle ILIKE 'PEI' OR p.sigle ILIKE 'MYP')"
            elif mode == 'grp_lycee':
                class_filter = "AND (p.sigle ILIKE 'DPEn' OR p.sigle ILIKE 'DPFr')"
            else:
                sigle = mode.split('_')[1]
                class_filter = f"AND p.sigle ILIKE '{sigle}'"

            # --- Stats par classe ---
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
                WHERE c.enabled = TRUE {class_filter}
                GROUP BY c.id, c.label
                ORDER BY c.label
            """, ('absence', 'Suivi > Absence%', 'exit', 'Sortie%', '%Fuite%', date_from, date_to))

            rows = cur.fetchall()

            # --- KPIs ---
            total_students = sum(r[5] for r in rows)
            total_abs = sum(r[3] for r in rows)
            total_exits = sum(r[4] for r in rows)
            total_events = sum(r[2] for r in rows)

            self._kpi_cards['total'].setText(str(total_students))
            present_val = max(0, total_students - total_abs) if total_abs > 0 else total_students
            self._kpi_cards['present'].setText(str(present_val))
            self._kpi_cards['absent'].setText(str(total_abs))
            self._kpi_cards['exit'].setText(str(total_exits))

            # --- Table ---
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
                for j, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignCenter)
                    self._stats_table.setItem(i, j, item)
            hh = self._stats_table.horizontalHeader()
            total_w = self._stats_table.viewport().width()
            col_w = max(80, total_w // 5)
            for c in range(5):
                hh.setSectionResizeMode(c, QHeaderView.Fixed)
                self._stats_table.setColumnWidth(c, col_w)

            # --- Barres absences par classe ---
            self._abs_bar.removeAllSeries()
            for ax in self._abs_bar.axes():
                self._abs_bar.removeAxis(ax)
            abs_set = QBarSet("Absences")
            abs_set.setColor(QColor(p.error))
            cat_names = []
            for r in rows:
                abs_set << r[3]
                cat_names.append(r[1])
            if rows:
                series = QBarSeries()
                series.append(abs_set)
                self._abs_bar.addSeries(series)
                self._abs_bar.setTitle("Absences par classe")
                self._abs_bar.setAnimationOptions(QChart.SeriesAnimations)
                self._abs_bar.legend().setVisible(False)
                axis_x = QBarCategoryAxis()
                axis_x.append(cat_names)
                axis_x.setLabelsAngle(-45)
                self._abs_bar.addAxis(axis_x, Qt.AlignBottom)
                series.attachAxis(axis_x)
                axis_y = QValueAxis()
                max_abs = max(r[3] for r in rows)
                axis_y.setRange(0, max(max_abs + 2, 10))
                self._abs_bar.addAxis(axis_y, Qt.AlignLeft)
                series.attachAxis(axis_y)
            else:
                self._abs_bar.setTitle("Absences par classe — aucune donnée")

            # --- Barres sorties par classe ---
            self._exit_bar.removeAllSeries()
            for ax in self._exit_bar.axes():
                self._exit_bar.removeAxis(ax)
            exit_set = QBarSet("Sorties")
            exit_set.setColor(QColor(p.tertiary))
            for r in rows:
                exit_set << r[4]
            if rows:
                exit_series = QBarSeries()
                exit_series.append(exit_set)
                self._exit_bar.addSeries(exit_series)
                self._exit_bar.setTitle("Sorties par classe")
                self._exit_bar.setAnimationOptions(QChart.SeriesAnimations)
                self._exit_bar.legend().setVisible(False)
                ex_axis_x = QBarCategoryAxis()
                ex_axis_x.append(cat_names)
                ex_axis_x.setLabelsAngle(-45)
                self._exit_bar.addAxis(ex_axis_x, Qt.AlignBottom)
                exit_series.attachAxis(ex_axis_x)
                ex_axis_y = QValueAxis()
                max_exit = max(r[4] for r in rows)
                ex_axis_y.setRange(0, max(max_exit + 2, 5))
                self._exit_bar.addAxis(ex_axis_y, Qt.AlignLeft)
                exit_series.attachAxis(ex_axis_y)
            else:
                self._exit_bar.setTitle("Sorties par classe — aucune donnée")

            # --- Tendance absences sur la période ---
            self._trend_chart.removeAllSeries()
            for ax in self._trend_chart.axes():
                self._trend_chart.removeAxis(ax)
            cur.execute(f"""
                SELECT DATE(se.event_at) AS d, COUNT(*) AS cnt
                FROM student_event se
                JOIN larcauth_student s ON s.aecuser_ptr_id = se.student_id
                JOIN larcauth_classroom c ON c.id = s.s_classroom_id
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE (se.event_type = %s OR se.event_type ILIKE %s)
                  AND c.enabled = TRUE {class_filter}
                  AND DATE(se.event_at) BETWEEN %s AND %s
                GROUP BY d ORDER BY d
            """, ('absence', 'Suivi > Absence%', date_from, date_to))
            trend_rows = cur.fetchall()
            if trend_rows:
                line = QLineSeries()
                line.setColor(QColor(p.error))
                line.setName("Absences")
                for d, cnt in trend_rows:
                    qd = QDate(d.year, d.month, d.day)
                    dt = QDateTime(qd, QTime(0, 0))
                    line.append(dt.toMSecsSinceEpoch(), cnt)
                self._trend_chart.addSeries(line)
                self._trend_chart.setTitle("Tendance des absences")
                self._trend_chart.setAnimationOptions(QChart.SeriesAnimations)
                self._trend_chart.legend().setVisible(False)
                axis_x_dt = QDateTimeAxis()
                axis_x_dt.setFormat("dd/MM")
                axis_x_dt.setLabelsAngle(-45)
                self._trend_chart.addAxis(axis_x_dt, Qt.AlignBottom)
                line.attachAxis(axis_x_dt)
                axis_y_t = QValueAxis()
                max_t = max(r[1] for r in trend_rows)
                axis_y_t.setRange(0, max_t + 2)
                self._trend_chart.addAxis(axis_y_t, Qt.AlignLeft)
                line.attachAxis(axis_y_t)
            else:
                self._trend_chart.setTitle("Tendance des absences — aucune donnée")

            # --- Donut taux de présence ---
            self._donut_chart.removeAllSeries()
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
                WHERE s.enabled = TRUE AND c.enabled = TRUE {class_filter}
            """, ('absence', 'Suivi > Absence%', date_from, date_to,
                   'absence', 'Suivi > Absence%', date_from, date_to))
            pres_row = cur.fetchone()
            present_count = pres_row[0] if pres_row else 0
            absent_count = pres_row[1] if pres_row else 0

            if present_count > 0 or absent_count > 0:
                donut = QPieSeries()
                donut.setHoleSize(0.45)
                if present_count > 0:
                    donut.append("Présents", present_count)
                    donut.slices()[-1].setColor(QColor(p.success))
                    donut.slices()[-1].setLabelVisible(True)
                    donut.slices()[-1].setLabel(f"Présents {present_count}")
                    donut.slices()[-1].setLabelColor(QColor(p.text_strong))
                if absent_count > 0:
                    donut.append("Absents", absent_count)
                    donut.slices()[-1].setColor(QColor(p.error))
                    donut.slices()[-1].setLabelVisible(True)
                    donut.slices()[-1].setLabel(f"Absents {absent_count}")
                    donut.slices()[-1].setLabelColor(QColor(p.text_strong))
                self._donut_chart.addSeries(donut)
                self._donut_chart.setTitle("Taux de présence")
                self._donut_chart.legend().setVisible(False)
                self._donut_chart.setAnimationOptions(QChart.SeriesAnimations)
            else:
                self._donut_chart.setTitle("Taux de présence — aucune donnée")

            self._set_loading(False)

        except Exception as e:
            log(f"_load_group_stats: {e}")
            self._set_loading(False)

    def _load_global_history(self, mode: str):
        self._set_loading(True, "Événements...")
        conn = db.server_conn
        if not conn or not self._current_term_id:
            self._set_loading(False)
            return

        try:
            cur = conn.cursor()

            # Populate filter combos
            if self._history_filter_class.count() <= 1:
                cur.execute("""
                    SELECT c.id, c.label FROM larcauth_classroom c
                    JOIN larcauth_level l ON l.id = c.fk_level_id
                    JOIN larcauth_program p ON p.id = l.fk_program_id
                    WHERE c.enabled = TRUE
                    ORDER BY c.label
                """)
                for cid, clabel in cur.fetchall():
                    self._history_filter_class.addItem(clabel, cid)
                self._history_filter_class.model().sort(0)
            if self._history_filter_type.count() == 0:
                cur.execute("SELECT DISTINCT event_type FROM student_event ORDER BY event_type")
                for (et,) in cur.fetchall():
                    self._history_filter_type.addItem(et)

            if mode == 'grp_all':
                class_filter = "AND p.sigle IN ('PEI', 'MYP', 'DPEn', 'DPFr')"
            elif mode == 'grp_college':
                class_filter = "AND (p.sigle ILIKE 'PEI' OR p.sigle ILIKE 'MYP')"
            elif mode == 'grp_lycee':
                class_filter = "AND (p.sigle ILIKE 'DPEn' OR p.sigle ILIKE 'DPFr')"
            else:
                sigle = mode.split('_')[1]
                class_filter = f"AND p.sigle ILIKE '{sigle}'"

            # -- Filtres suppl. --
            params = []
            sel_class = self._history_filter_class.currentData()
            sel_type = self._history_filter_type.currentText().strip()
            date_from = self._history_filter_date_from.date().toString('yyyy-MM-dd')
            date_to = self._history_filter_date_to.date().toString('yyyy-MM-dd')

            if sel_class:
                class_filter += " AND c.id = %s"
                params.append(sel_class)
            if sel_type:
                class_filter += " AND se.event_type ILIKE %s"
                params.append(f'%{sel_type}%')

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
                WHERE DATE(se.event_at) BETWEEN %s AND %s {class_filter}
                ORDER BY se.event_at DESC
                LIMIT 500
            """, (date_from, date_to, *params))

            rows = cur.fetchall()
            self._history_table.setRowCount(len(rows))
            self._history_table.setColumnCount(10)
            self._history_table.setHorizontalHeaderLabels(
                ["ID", "Élève", "Classe", "Type", "Lieu", "Matière", "Heure", "Note", "Créé par", "Validé"])
            self._history_table.setColumnHidden(0, True)  # event_id

            for i, row in enumerate(rows):
                eid, name, cls_name, etype, e_at, lieu, subject, note, creator, validated = row
                ei = _event_icon(etype)
                color = _event_color(etype)
                display_type = f"{ei} {etype}"

                items = [
                    QTableWidgetItem(str(eid)),
                    QTableWidgetItem(name),
                    QTableWidgetItem(cls_name),
                    QTableWidgetItem(display_type),
                    QTableWidgetItem(lieu or ''),
                    QTableWidgetItem(subject or ''),
                    QTableWidgetItem(e_at.strftime('%H:%M') if e_at else ''),
                    QTableWidgetItem(note or ''),
                    QTableWidgetItem(creator),
                    QTableWidgetItem("✓" if validated else ''),
                ]
                for j in range(len(items)):
                    if j == 3:
                        items[j].setForeground(QBrush(QColor(color)))
                    if j == 9 and validated:
                        items[j].setForeground(QBrush(QColor('#2e7d32')))
                        items[j].setFont(QFont('Segoe UI', 10, QFont.Bold))
                    if j not in (3, 7):
                        items[j].setTextAlignment(Qt.AlignCenter)
                    items[j].setFlags(items[j].flags() & ~Qt.ItemIsEditable)
                    self._history_table.setItem(i, j, items[j])
            hh = self._history_table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.Fixed);       self._history_table.setColumnWidth(0, 0)
            hh.setSectionResizeMode(1, QHeaderView.Interactive); self._history_table.setColumnWidth(1, 140)
            hh.setSectionResizeMode(2, QHeaderView.Interactive); self._history_table.setColumnWidth(2, 100)
            hh.setSectionResizeMode(3, QHeaderView.Interactive); self._history_table.setColumnWidth(3, 300)
            hh.setSectionResizeMode(4, QHeaderView.Interactive); self._history_table.setColumnWidth(4, 120)
            hh.setSectionResizeMode(5, QHeaderView.Interactive); self._history_table.setColumnWidth(5, 110)
            hh.setSectionResizeMode(6, QHeaderView.Interactive); self._history_table.setColumnWidth(6, 100)
            hh.setSectionResizeMode(7, QHeaderView.Stretch)
            hh.setSectionResizeMode(8, QHeaderView.Interactive); self._history_table.setColumnWidth(8, 200)
            hh.setSectionResizeMode(9, QHeaderView.Interactive); self._history_table.setColumnWidth(9, 130)
            self._set_loading(False)

        except Exception as e:
            log(f"_load_global_history: {e}")
            self._set_loading(False)

    # ---- Mode classe -------------------------------------------------------

    def _show_class_mode(self, class_id: int):
        self._content_stack.setCurrentIndex(1)
        self._class_stack.setCurrentIndex(0)

        self._cards_title.setText(f"<b>Élèves de {self._current_class_label}</b>")
        self._load_students(class_id)
        self._selected_student_id = 0

    def _load_students(self, class_id: int):
        self._set_loading(True, "Élèves...")
        conn = db.server_conn
        if not conn or not self._current_term_id:
            self._set_loading(False)
            return

        date_from, date_to = self._period_dates()

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.aecuser_ptr_id,
                       aec.last_name, aec.first_name
                FROM larcauth_student s
                JOIN larcauth_aecuser aec ON aec.id = s.aecuser_ptr_id
                WHERE s.s_classroom_id = %s AND s.enabled = TRUE
                ORDER BY aec.last_name
            """, (class_id,))
            rows = cur.fetchall()

            self._students = [{'id': r[0], 'last_name': r[1], 'first_name': r[2]} for r in rows]

            # Stats d'events pour chaque élève
            student_ids = [s['id'] for s in self._students]
            event_stats = {}
            if student_ids:
                ids_sql = ','.join(str(sid) for sid in student_ids)
                try:
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
                    for sid, exit_count, presence in cur.fetchall():
                        event_stats[sid] = {'exit': exit_count, 'presence': presence}
                except Exception:
                    pass

            # Vider les cartes existantes
            for i in reversed(range(self._cards_layout.count())):
                w = self._cards_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()

            # Remplir les cartes avec colonnes adaptatives
            avail_w = self._cards_scroll.viewport().width()
            card_w = 124
            spacing = 8
            cols = max(1, (avail_w + spacing) // (card_w + spacing)) if avail_w > 100 else 3
            for idx, s in enumerate(self._students):
                sid = s['id']
                card = StudentCard(sid, s['last_name'], s['first_name'])
                stats = event_stats.get(sid, {'exit': 0, 'presence': 'Présent'})
                card.set_exit_count(stats['exit'])
                is_absent = stats['presence'] == 'Absent'
                color = theme_manager.palette.error if is_absent else theme_manager.palette.success
                card.set_status(stats['presence'], color)
                card.set_absent(is_absent)
                card.clicked.connect(self._on_student_selected)
                self._cards_layout.addWidget(card, idx // cols, idx % cols, Qt.AlignCenter)

            # Étendre la grille
            remaining = len(self._students) % cols
            if remaining:
                for _ in range(cols - remaining):
                    spacer = QWidget()
                    spacer.setFixedSize(124, 200)
                    self._cards_layout.addWidget(spacer, len(self._students) // cols, cols - remaining + _, Qt.AlignCenter)
            self._set_loading(False)

        except Exception as e:
            log(f"_load_students: {e}")
            self._set_loading(False)

    def _on_student_selected(self, student_id: int):
        self._selected_student_id = student_id
        self._load_student_detail(student_id)

    def _on_edit_timetable(self):
        if not self._current_class_id:
            return
        # Trouver le label de la classe
        label = ''
        for cid, l, pid, sigle in self._classes:
            if cid == self._current_class_id:
                label = l
                break
        dlg = TimetableEditor(self._current_class_id, label, self._current_term_id, self)
        dlg.exec()

    def _on_back_to_cards(self):
        self._sd_tabs.hide()
        self._sd_placeholder.show()
        self._class_stack.setCurrentIndex(0)

    def _on_add_event(self):
        sid = self._selected_student_id
        if not sid:
            return
        dlg = EventGenerator(sid, self)
        if dlg.exec():
            data = dlg.get_data()
            conn = db.server_conn
            if not conn:
                QMessageBox.warning(self, "Erreur", "Aucune connexion base de données.")
                return
            self._set_loading(True, "Enregistrement...")
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
                self._set_loading(False)
            except Exception as e:
                log(f"_on_add_event insert: {e}")
                self._set_loading(False)
                conn.rollback()
                QMessageBox.critical(self, "Erreur", f"Échec de l'enregistrement : {e}")
                return
            self._load_student_detail(sid)

    def _load_student_detail(self, student_id: int):
        self._set_loading(True, "Détail élève...")
        conn = db.server_conn
        if not conn or not self._current_class_id:
            self._set_loading(False)
            return

        p = theme_manager.palette
        date_from, date_to = self._period_dates()

        try:
            cur = conn.cursor()

            # -- Infos élève + coordonnées --
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
                return
            last_name, first_name, email, email_perso, tel_maison, tel_portable, date_entree, cls_label = r
            name = f"{first_name} {last_name}"
            self._sd_header.setText(f"<b>{name}</b>")
            self._sd_class.setText(cls_label)

            # Coordonnées
            self._sd_contact_labels['full_name'].setText(
                f"<b>Nom :</b> {last_name.upper()} {first_name}")
            self._sd_contact_labels['email'].setText(
                f"<b>Email :</b> {email or '—'}")
            self._sd_contact_labels['email_perso'].setText(
                f"<b>Email personnel :</b> {email_perso or '—'}")
            self._sd_contact_labels['tel_maison'].setText(
                f"<b>Tél. maison :</b> {tel_maison or '—'}")
            self._sd_contact_labels['tel_portable'].setText(
                f"<b>Tél. portable :</b> {tel_portable or '—'}")
            self._sd_contact_labels['date_entree'].setText(
                f"<b>Date d'entrée :</b> {date_entree.strftime('%d/%m/%Y') if date_entree else '—'}")

            # Photo
            pix = QPixmap(get_photo_path(student_id))
            if not pix.isNull():
                self._sd_photo.setPixmap(
                    pix.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            if not self._sd_photo.pixmap() or self._sd_photo.pixmap().isNull():
                self._sd_photo.setText("📷")

            # -- KPIs --
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE event_type = %s OR event_type ILIKE %s) AS abs_count,
                    COUNT(*) FILTER (WHERE event_type = %s OR event_type ILIKE %s OR event_type ILIKE %s) AS exit_count,
                    COUNT(*) AS total
                FROM student_event
                WHERE student_id = %s AND DATE(event_at) BETWEEN %s AND %s
            """, ('absence', 'Suivi > Absence%', 'exit', 'Sortie%', '%Fuite%', student_id, date_from, date_to))
            kpi = cur.fetchone()
            abs_count, exit_count, total = kpi if kpi else (0, 0, 0)
            self._sd_kpis['abs'].setText(str(abs_count))
            self._sd_kpis['exit'].setText(str(exit_count))
            self._sd_kpis['total'].setText(str(total))

            # -- Chart évolution absences sur le trimestre --
            self._sd_chart.removeAllSeries()
            for ax in self._sd_chart.axes():
                self._sd_chart.removeAxis(ax)

            from datetime import datetime, timedelta
            term_start = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            term_end = datetime.now().strftime('%Y-%m-%d')

            cur.execute("""
                SELECT DATE(event_at) AS d, COUNT(*) AS cnt
                FROM student_event
                WHERE student_id = %s AND (event_type = %s OR event_type ILIKE %s)
                  AND DATE(event_at) BETWEEN %s AND %s
                GROUP BY d ORDER BY d
            """, (student_id, 'absence', 'Suivi > Absence%', term_start, term_end))
            trend = cur.fetchall()

            if trend:
                line = QLineSeries()
                line.setColor(QColor(p.error))
                for d, cnt in trend:
                    qd = QDate(d.year, d.month, d.day)
                    dt = QDateTime(qd, QTime(0, 0))
                    line.append(dt.toMSecsSinceEpoch(), cnt)
                self._sd_chart.addSeries(line)
                self._sd_chart.setTitle("Évolution des absences (trimestre)")
                self._sd_chart.setAnimationOptions(QChart.SeriesAnimations)
                self._sd_chart.legend().setVisible(False)
                ax_x = QDateTimeAxis()
                ax_x.setFormat("dd/MM")
                ax_x.setLabelsAngle(-45)
                self._sd_chart.addAxis(ax_x, Qt.AlignBottom)
                line.attachAxis(ax_x)
                ax_y = QValueAxis()
                max_t = max(r[1] for r in trend)
                ax_y.setRange(0, max_t + 2)
                self._sd_chart.addAxis(ax_y, Qt.AlignLeft)
                line.attachAxis(ax_y)
            else:
                self._sd_chart.setTitle("Évolution des absences — aucune donnée")

            # -- Derniers événements --
            cur.execute("""
                SELECT se.event_id, se.event_type, se.event_at, se.lieu_label, se.subject_label, se.note,
                       u.last_name || ' ' || u.first_name AS creator,
                       se.validated_by
                FROM student_event se
                LEFT JOIN larcauth_aecuser u ON u.id = se.created_by
                WHERE se.student_id = %s
                ORDER BY se.event_at DESC
                LIMIT 20
            """, (student_id,))
            evts = cur.fetchall()
            self._sd_events.setRowCount(len(evts))
            self._sd_events.setColumnCount(8)
            self._sd_events.setHorizontalHeaderLabels(["ID", "Type", "Lieu", "Matière", "Date", "Note", "Créé par", "Validé"])
            self._sd_events.setColumnHidden(0, True)
            for i, (eid, etype, e_at, lieu, subject, note, creator, validated) in enumerate(evts):
                ei = _event_icon(etype)
                color = _event_color(etype)
                items = [
                    QTableWidgetItem(str(eid)),
                    QTableWidgetItem(f"{ei} {etype}"),
                    QTableWidgetItem(lieu or ''),
                    QTableWidgetItem(subject or ''),
                    QTableWidgetItem(e_at.strftime('%d/%m %H:%M') if e_at else ''),
                    QTableWidgetItem(note or ''),
                    QTableWidgetItem(creator),
                    QTableWidgetItem("✓" if validated else ''),
                ]
                items[1].setForeground(QBrush(QColor(color)))
                for j, it in enumerate(items):
                    if j not in (1, 5):
                        it.setTextAlignment(Qt.AlignCenter)
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                    self._sd_events.setItem(i, j, it)
            hh = self._sd_events.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.Fixed);     self._sd_events.setColumnWidth(0, 0)
            hh.setSectionResizeMode(1, QHeaderView.Interactive); self._sd_events.setColumnWidth(1, 300)
            hh.setSectionResizeMode(2, QHeaderView.Interactive); self._sd_events.setColumnWidth(2, 120)
            hh.setSectionResizeMode(3, QHeaderView.Interactive); self._sd_events.setColumnWidth(3, 110)
            hh.setSectionResizeMode(4, QHeaderView.Interactive); self._sd_events.setColumnWidth(4, 100)
            hh.setSectionResizeMode(5, QHeaderView.Stretch)
            hh.setSectionResizeMode(6, QHeaderView.Interactive); self._sd_events.setColumnWidth(6, 200)
            hh.setSectionResizeMode(7, QHeaderView.Interactive); self._sd_events.setColumnWidth(7, 200)

            # Afficher les tabs, cacher le placeholder
            self._sd_tabs.show()
            self._sd_placeholder.hide()
            self._class_stack.setCurrentIndex(1)
            self._set_loading(False)

        except Exception as e:
            log(f"_load_student_detail: {e}")
            self._set_loading(False)

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

    def _get_event_id_from_table(self, table: QTableWidget) -> int | None:
        idx = table.currentRow()
        if idx < 0:
            return None
        item = table.item(idx, 0)
        return int(item.text()) if item and item.text().isdigit() else None

    def _show_event_context_menu(self, table: QTableWidget, pos):
        eid = self._get_event_id_from_table(table)
        if not eid:
            return
        conn = db.server_conn
        is_validated = False
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT validated_by FROM student_event WHERE event_id = %s", (eid,))
            row = cur.fetchone()
            is_validated = row and row[0] is not None
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Modifier")
        validate_action = menu.addAction("🔒 Dévalider" if is_validated else "✅ Valider")
        delete_action = menu.addAction("🗑️ Supprimer")
        chosen = menu.exec(table.viewport().mapToGlobal(pos))
        if chosen == edit_action:
            self._edit_event(eid)
        elif chosen == validate_action:
            self._toggle_validation(eid)
        elif chosen == delete_action:
            self._delete_event(eid)

    def _on_event_table_dblclick(self, row: int, col: int):
        sender = self.sender()
        if not isinstance(sender, QTableWidget):
            return
        item = sender.item(row, 0)
        eid = int(item.text()) if item and item.text().isdigit() else None
        if eid:
            self._edit_event(eid)

    def _edit_event(self, event_id: int):
        conn = db.server_conn
        if not conn:
            QMessageBox.warning(self, "Erreur", "Aucune connexion base de données.")
            return
        cur = conn.cursor()
        cur.execute("""
            SELECT se.event_type, se.event_at, se.lieu_label, se.subject_label, se.note,
                   aec.last_name || ' ' || aec.first_name AS student_name
            FROM student_event se
            JOIN larcauth_aecuser aec ON aec.id = se.student_id
            WHERE se.event_id = %s
        """, (event_id,))
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Erreur", "Événement introuvable.")
            return
        etype, e_at, lieu, subject, note, student_name = row

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Modifier l'événement #{event_id}")
        dlg.setMinimumSize(480, 400)
        layout = QVBoxLayout(dlg)
        p = theme_manager.palette

        # Infos
        info = QLabel(
            f"<b>{student_name}</b> — {etype}<br>"
            f"<span style='color:{p.text_disabled};font-size:{theme_manager.font_size(10)}px;'>"
            f"{e_at.strftime('%d/%m/%Y %H:%M') if e_at else ''} | {lieu or ''}"
            f"{' | ' + subject if subject else ''}</span>")
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        # Type
        layout.addWidget(QLabel("Type d'événement:"))
        type_input = QComboBox()
        cur2 = conn.cursor()
        cur2.execute("SELECT DISTINCT event_type FROM student_event ORDER BY event_type")
        type_input.addItems([et for (et,) in cur2.fetchall()])
        type_input.setCurrentText(etype)
        layout.addWidget(type_input)

        # Note
        layout.addWidget(QLabel("Note:"))
        note_input = QTextEdit()
        note_input.setText(note or '')
        note_input.setMaximumHeight(120)
        layout.addWidget(note_input)

        # Boutons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Enregistrer")
        save_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; padding: 8px 20px; font-weight: bold; }}")
        save_btn.clicked.connect(lambda: (
            cur.execute("UPDATE student_event SET event_type = %s, note = %s WHERE event_id = %s",
                        (type_input.currentText(), note_input.toPlainText().strip(), event_id)),
            conn.commit(), dlg.accept()))
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        if dlg.exec() == QDialog.Accepted:
            self.refresh_all()

    def _toggle_validation(self, event_id: int):
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("SELECT validated_by FROM student_event WHERE event_id = %s", (event_id,))
            row = cur.fetchone()
            if row and row[0] is not None:
                cur.execute("UPDATE student_event SET validated_by = NULL WHERE event_id = %s", (event_id,))
            else:
                cur.execute("UPDATE student_event SET validated_by = %s WHERE event_id = %s",
                            (session.user_id, event_id))
            conn.commit()
            self.refresh_all()
        except Exception as e:
            log(f"_toggle_validation: {e}")
            conn.rollback()

    def _delete_event(self, event_id: int):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer définitivement l'événement #{event_id} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM student_event WHERE event_id = %s", (event_id,))
            conn.commit()
            self.refresh_all()
        except Exception as e:
            log(f"_delete_event: {e}")
            conn.rollback()
            QMessageBox.critical(self, "Erreur", f"Échec de la suppression : {e}")

    def refresh_all(self):
        self._update_network_label()
        if self._current_group_mode == 'class':
            self._show_class_mode(self._current_class_id)
        elif self._current_group_mode:
            self._show_group_mode(self._current_group_mode)

    def _refresh_timer(self):
        self._update_network_label()
        QTimer.singleShot(30000, self._refresh_timer)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_current_group_mode') and self._current_group_mode == 'class':
            if self._students and self._class_stack.currentIndex() == 0:
                self._reflow_cards()

    def _reflow_cards(self):
        avail_w = self._cards_scroll.viewport().width()
        card_w = 124
        spacing = 8
        cols = max(1, (avail_w + spacing) // (card_w + spacing)) if avail_w > 100 else 3
        # Garder les StudentCard, jeter les spacers
        cards = []
        for i in reversed(range(self._cards_layout.count())):
            w = self._cards_layout.itemAt(i).widget()
            if w:
                self._cards_layout.removeWidget(w)
                if isinstance(w, StudentCard):
                    cards.insert(0, w)
                else:
                    w.deleteLater()
        for idx, card in enumerate(cards):
            self._cards_layout.addWidget(card, idx // cols, idx % cols, Qt.AlignCenter)
        remaining = len(cards) % cols
        if remaining:
            for _ in range(cols - remaining):
                sp = QWidget()
                sp.setFixedSize(124, 200)
                self._cards_layout.addWidget(sp, len(cards) // cols, cols - remaining + _, Qt.AlignCenter)


# ---------------------------------------------------------------------------
# Éditeur d'emploi du temps
# ---------------------------------------------------------------------------
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
