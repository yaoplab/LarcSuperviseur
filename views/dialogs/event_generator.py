from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QFrame, QGridLayout, QButtonGroup, QStackedWidget,
    QTextEdit, QDialogButtonBox, QMessageBox, QWidget, QTimeEdit,
)
from PySide6.QtCore import Qt, QDate, QTime
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.network import detect_network
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.views.core.data_loader import DataLoader


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
        self._loader = DataLoader()
        self.setWindowTitle(f"Événement — élève #{student_id}")
        self.setMinimumWidth(600)
        self._load_student_classroom()
        self._load_types_from_db()
        self._init_ui()

    def _load_student_classroom(self):
        data = self._loader.get_student_classroom(self._student_id)
        if data:
            self._student_classroom_id = data['classroom_id']
            self._student_classroom_label = data['label']

    def _get_term_id(self) -> int:
        return self._loader.get_term_id()

    def _init_ui(self):
        layout = QVBoxLayout()
        p = theme_manager.palette
        s = theme_manager.font_size
        fs = 10
        sp = 8
        rd = 4
        # --- 1. Infos élève ---
        student_name = self._loader.get_student_name(self._student_id) or f"Élève #{self._student_id}"
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
        term_id = self._get_term_id()
        self._subjects = self._loader.get_classroom_subjects(self._student_classroom_id, term_id)
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

    def _load_locations(self):
        self._locations = self._loader.get_locations()

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
        self._type_hierarchy = self._loader.get_event_types_tree()

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
