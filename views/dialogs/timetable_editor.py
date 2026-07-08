from larccommon.l10n import _
from phibuilder.widgets import M3Button, M3ComboBox, M3Dialog, M3Label, M3TableWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.views.core.data_loader import DataLoader

# EventGenerator imported lazily in _open_event_dialog to avoid circular import


class TimeSlotGrid(QWidget):
    slotClicked = Signal(int, str, str)  # student_id, timeperiod_id, timetable_id

    def __init__(self):
        super().__init__()
        self._loader = DataLoader()
        self._grid = QGridLayout()
        self._grid.setSpacing(1)
        self.setLayout(self._grid)
        self._slots: dict[str, M3Button] = {}
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

        self._timeperiods = self._loader.get_classroom_timeperiods(classroom_id, weekday, term_id)
        if not self._timeperiods:
            return

        for col, tp in enumerate(self._timeperiods):
            label = M3Label(f"{tp['debut']}-{tp['fin']}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                f"font-weight: bold; font-size: {theme_manager.font_size(10)}px; padding: 2px; "
                f"color: {theme_manager.palette.text_strong};"
            )
            self._grid.addWidget(label, 0, col)

        btn = M3Button(_("timetable.add_event"))
        p = theme_manager.palette
        s = theme_manager.font_size
        btn.setStyleSheet(
            f"font-size: {s(9)}px; padding: 4px; "
            f"background: {p.surface_variant}; border: 1px solid {p.outline_variant}; "
            f"color: {p.text_strong};"
        )
        btn.clicked.connect(lambda: self._open_event_dialog(0, "", ""))
        self._grid.addWidget(btn, 1, 0, 1, len(self._timeperiods))

    def set_student(self, student_id: int):
        self._current_student_id = student_id
        self._update_student_labels()

    def _update_student_labels(self):
        for key, btn in self._slots.items():
            sid, tp_id = map(int, key.split(":"))
            if self._current_student_id and sid != self._current_student_id:
                btn.setVisible(False)
            else:
                btn.setVisible(True)

    def _open_event_dialog(self, timetable_id=None, timeperiod_id=None, slot_label=None):
        if not self._current_student_id:
            QMessageBox.information(
                self, _("common.dialog.info_title"), _("timetable.select_student_first")
            )
            return
        from LarcSuperviseur.common.session import session
        from LarcSuperviseur.views.dialogs.event_generator import EventGenerator

        dlg = EventGenerator(self._current_student_id, self)
        if dlg.exec():
            data = dlg.get_data()
            data["created_by"] = session.user_id
            if not self._loader.insert_event(data):
                QMessageBox.critical(self, _("common.dialog.error"), _("timetable.save_failed"))
                return
            self.window().refresh_all()


class TimetableEditor(M3Dialog):
    DAYS = [
        _("timetable.monday"),
        _("timetable.tuesday"),
        _("timetable.wednesday"),
        _("timetable.thursday"),
        _("timetable.friday"),
    ]

    def __init__(self, class_id: int, class_label: str, term_id: int, parent=None):
        super().__init__(parent)
        self._loader = DataLoader()
        self._class_id = class_id
        self._term_id = term_id
        self.setWindowTitle(_("timetable.title").format(label=class_label))
        self.setMinimumSize(800, 500)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        layout = QVBoxLayout(self)

        # Grille
        self._tt_grid = M3TableWidget()
        self._tt_grid.setAlternatingRowColors(True)
        self._tt_grid.horizontalHeader().setStretchLastSection(True)
        self._tt_grid.setEditTriggers(M3TableWidget.NoEditTriggers)
        layout.addWidget(self._tt_grid, 1)

        # Boutons
        btn_row = QHBoxLayout()
        save_btn = M3Button(_("timetable.save_button"))
        save_btn.setMinimumHeight(36)
        save_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; font-weight: bold; "
            f"font-size: {s(12)}px; padding: 6px 20px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}"
        )
        save_btn.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _load_data(self):
        try:
            from collections import defaultdict

            all_tps = self._loader.get_timeperiods()
            self._tp_by_day: dict[int, list[tuple]] = defaultdict(list)
            for tp_id, debut, fin, wd in all_tps:
                self._tp_by_day[wd].append((tp_id, debut, fin))

            tt = self._loader.get_classroom_timetable(self._class_id, self._term_id)
            self._cht_map = tt["cht_map"]
            self._cht_id_map = tt["cht_id_map"]

            self._subjects = self._loader.get_available_subjects(self._class_id)

            self._build_grid()

        except Exception as e:
            log(f"TimetableEditor._load_data: {e}")
            QMessageBox.critical(self, _("common.dialog.error"), str(e))

    def _build_grid(self):
        p = theme_manager.palette

        # Déterminer le nombre max de créneaux par jour
        max_slots = max(len(v) for v in self._tp_by_day.values()) if self._tp_by_day else 0

        self._tt_grid.setColumnCount(6)  # Heure + 5 jours
        self._tt_grid.setHorizontalHeaderLabels([_("timetable.hour")] + self.DAYS)
        self._tt_grid.setRowCount(max_slots)

        # Stocker les combos pour la sauvegarde
        self._cell_combos: dict[tuple[int, int], M3ComboBox] = {}

        for row in range(max_slots):
            for day_idx in range(1, 6):  # 1=Lundi ... 5=Vendredi
                tp_list = self._tp_by_day.get(day_idx, [])
                if row < len(tp_list):
                    tp_id, debut, fin = tp_list[row]
                    debut_str = debut.strftime("%H:%M") if debut else ""
                    fin_str = fin.strftime("%H:%M") if fin else ""
                    time_label = f"{debut_str}-{fin_str}"

                    # Colonne Heure (col 0)
                    if day_idx == 1:
                        time_item = QTableWidgetItem(time_label)
                        time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
                        self._tt_grid.setItem(row, 0, time_item)

                    # Combo matière
                    combo = M3ComboBox()
                    combo.addItems(self._subjects)
                    current_subj = self._cht_map.get((day_idx, tp_id), "")
                    idx = combo.findText(current_subj)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                    # Stocker tp_id et cht_id dans le combo
                    combo.setProperty("tp_id", tp_id)
                    combo.setProperty("cht_id", self._cht_id_map.get((day_idx, tp_id), ""))
                    combo.setProperty("day", day_idx)
                    self._cell_combos[(row, day_idx)] = combo
                    self._tt_grid.setCellWidget(row, day_idx, combo)

        self._tt_grid.resizeColumnsToContents()
        self._tt_grid.setColumnWidth(0, 80)
        for c in range(1, 6):
            self._tt_grid.setColumnWidth(c, 140)

    def _save(self):
        updated = 0

        for (row, day), combo in self._cell_combos.items():
            tp_id = combo.property("tp_id")
            cht_id = combo.property("cht_id")
            subj = combo.currentText().strip()

            if not cht_id:
                continue

            subj_id = self._loader.get_subject_id_by_label(subj)
            if self._loader.update_timetable_slot(cht_id, subj_id):
                updated += 1

        QMessageBox.information(
            self, _("common.label.success"), _("timetable.save_success").format(count=updated)
        )
        self.accept()
