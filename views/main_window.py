from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QComboBox, QPushButton,
                               QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox,
                               QDateEdit, QGroupBox, QSplitter,
                               QTextEdit, QFrame, QScrollArea,
                               QCheckBox)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QColor, QBrush
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session, UserRole
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.network import detect_network


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"LarcSuperviseur — {session.full_name} ({session.role.value})")
        self._current_class_id = None
        self._current_date = QDate.currentDate()
        self._init_ui()
        self._load_classes()
        QTimer.singleShot(30000, self._refresh_timer)

    def _init_ui(self):
        layout = QVBoxLayout()

        # Top bar
        top = QHBoxLayout()
        title = QLabel(f"Supervision — {session.full_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")

        self._class_combo = QComboBox()
        self._class_combo.setMinimumWidth(250)
        self._class_combo.currentIndexChanged.connect(self._on_class_changed)

        self._date_picker = QDateEdit()
        self._date_picker.setDate(self._current_date)
        self._date_picker.setCalendarPopup(True)
        self._date_picker.dateChanged.connect(self._on_date_changed)

        self._today_btn = QPushButton("Aujourd'hui")
        self._today_btn.clicked.connect(self._go_today)

        self._refresh_btn = QPushButton("Rafraîchir")
        self._refresh_btn.clicked.connect(self._refresh)

        self._network_label = QLabel()
        self._update_network_label()

        top.addWidget(title)
        top.addWidget(QLabel("Classe :"))
        top.addWidget(self._class_combo)
        top.addWidget(QLabel("Date :"))
        top.addWidget(self._date_picker)
        top.addWidget(self._today_btn)
        top.addWidget(self._refresh_btn)
        top.addStretch()
        top.addWidget(self._network_label)

        # Event type filter
        filter_layout = QHBoxLayout()
        self._filter_all = QCheckBox("Tous")
        self._filter_arrival = QCheckBox("Arrivées")
        self._filter_departure = QCheckBox("Départs")
        self._filter_exit = QCheckBox("Sorties")
        self._filter_absence = QCheckBox("Absences")
        self._filter_late = QCheckBox("Retards")
        for cb in (self._filter_all, self._filter_arrival, self._filter_departure,
                   self._filter_exit, self._filter_absence, self._filter_late):
            cb.stateChanged.connect(self._refresh)
        self._filter_all.setChecked(True)

        # Stats summary
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet("font-size: 12px; padding: 5px;")

        # Main table
        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)

        # Validation section (admin/coord only)
        self._validate_group = QGroupBox("Validation en attente")
        vlayout = QVBoxLayout()
        self._pending_table = QTableWidget()
        self._pending_table.setAlternatingRowColors(True)
        self._pending_table.horizontalHeader().setStretchLastSection(True)
        self._validate_btn = QPushButton("Valider la sélection")
        self._validate_btn.clicked.connect(self._validate_selected)
        self._validate_btn.setEnabled(session.role in (UserRole.ADMIN, UserRole.COORD))
        vlayout.addWidget(self._pending_table)
        vlayout.addWidget(self._validate_btn)
        self._validate_group.setLayout(vlayout)

        # Build layout
        layout.addLayout(top)
        layout.addLayout(filter_layout)
        layout.addWidget(self._stats_label)
        layout.addWidget(self._table, stretch=3)
        layout.addWidget(self._validate_group, stretch=1)

        container = QWidget()
        container.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        outer = QVBoxLayout()
        outer.addWidget(scroll)
        self.setLayout(outer)

    def _update_network_label(self):
        intranet_ok, internet_ok = detect_network()
        if intranet_ok:
            self._network_label.setText("Intranet ●")
            self._network_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        elif internet_ok:
            self._network_label.setText("Cloud ▲")
            self._network_label.setStyleSheet("color: #2980b9; font-weight: bold;")
        else:
            self._network_label.setText("Hors ligne ●")
            self._network_label.setStyleSheet("color: #e67e22; font-weight: bold;")

    def _go_today(self):
        self._current_date = QDate.currentDate()
        self._date_picker.setDate(self._current_date)

    def _on_date_changed(self, date: QDate):
        self._current_date = date
        self._refresh()

    def _load_classes(self):
        conn = db.server_conn
        if not conn:
            QMessageBox.warning(self, "Erreur", "Non connecté au serveur.")
            return
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT c.id, c.label
                FROM larcauth_classroom c
                ORDER BY c.label
            """)
            rows = cur.fetchall()
            self._class_combo.clear()
            for cid, label in rows:
                self._class_combo.addItem(label, cid)
        except Exception as e:
            log(f"_load_classes: {e}")
            QMessageBox.critical(self, "Erreur", str(e))

    def _on_class_changed(self, idx: int):
        if idx < 0:
            return
        self._current_class_id = self._class_combo.itemData(idx)
        self._refresh()

    def _refresh(self):
        self._refresh_table()
        self._refresh_pending()

    def _refresh_timer(self):
        self._refresh()
        QTimer.singleShot(30000, self._refresh_timer)

    def _refresh_table(self):
        conn = db.server_conn
        if not conn or not self._current_class_id:
            return

        active_filters = []
        if self._filter_all.isChecked():
            pass
        else:
            if self._filter_arrival.isChecked():    active_filters.append("'arrival'")
            if self._filter_departure.isChecked():  active_filters.append("'departure'")
            if self._filter_exit.isChecked():       active_filters.append("'exit'")
            if self._filter_absence.isChecked():    active_filters.append("'absence'")
            if self._filter_late.isChecked():       active_filters.append("'late'")

        date_str = self._current_date.toString("yyyy-MM-dd")

        try:
            cur = conn.cursor()
            where_filter = ""
            if active_filters:
                where_filter = f"AND se.event_type IN ({','.join(active_filters)})"

            cur.execute(f"""
                SELECT
                    se.event_id,
                    s.lastname || ' ' || s.firstname AS student_name,
                    se.event_type,
                    se.event_at,
                    se.note,
                    u.lastname || ' ' || u.firstname AS created_by_name,
                    CASE WHEN se.validated_by IS NOT NULL THEN 'Oui' ELSE 'Non' END AS valide
                FROM student_event se
                JOIN larcauth_student s ON s.id = se.student_id
                JOIN larcauth_aecuser u ON u.id = se.created_by
                LEFT JOIN larcauth_learner_has_term lht
                    ON lht.fk_student_id = se.student_id
                LEFT JOIN larcauth_classroom c ON c.id = lht.fk_classroom_id
                WHERE DATE(se.event_at) = %s
                  AND lht.fk_classroom_id = %s
                  {where_filter}
                ORDER BY se.event_at DESC
            """, (date_str, self._current_class_id))

            rows = cur.fetchall()
            self._table.setRowCount(len(rows))
            self._table.setColumnCount(7)
            headers = ["Élève", "Type", "Heure", "Note", "Créé par", "Validé", "ID"]
            self._table.setHorizontalHeaderLabels(headers)

            stats = {'arrival': 0, 'departure': 0, 'exit': 0, 'return': 0,
                     'absence': 0, 'justified': 0, 'late': 0}

            icons = {'arrival': '▲', 'departure': '▼', 'exit': '→', 'return': '←',
                     'absence': '✕', 'justified': '✓', 'late': '⏰'}

            colors = {'arrival': '#27ae60', 'departure': '#2980b9', 'exit': '#e67e22',
                      'return': '#2ecc71', 'absence': '#e74c3c', 'justified': '#95a5a6',
                      'late': '#f1c40f'}

            for i, row in enumerate(rows):
                eid, name, etype, e_at, note, creator, valide = row
                ei = icons.get(etype, etype)
                color = colors.get(etype, '#000')
                display_type = f"{ei} {etype}"
                stats[etype] = stats.get(etype, 0) + 1

                items = [
                    QTableWidgetItem(name),
                    QTableWidgetItem(display_type),
                    QTableWidgetItem(e_at.strftime('%H:%M') if e_at else ''),
                    QTableWidgetItem(note or ''),
                    QTableWidgetItem(creator),
                    QTableWidgetItem(valide),
                    QTableWidgetItem(str(eid)),
                ]
                for j, item in enumerate(items):
                    if j == 1:
                        item.setForeground(QBrush(QColor(color)))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self._table.setItem(i, j, item)

            self._table.setColumnHidden(6, True)
            self._table.resizeColumnsToContents()

            total = sum(stats.values())
            parts = []
            for key in ('arrival', 'departure', 'exit', 'absence', 'late', 'justified'):
                if stats.get(key, 0):
                    parts.append(f"{icons.get(key, key)} {key}={stats[key]}")
            self._stats_label.setText(
                f"📊 {total} événements | {' | '.join(parts)}"
            )

        except Exception as e:
            log(f"_refresh_table: {e}")

    def _refresh_pending(self):
        conn = db.server_conn
        if not conn or not self._current_class_id:
            return

        if session.role not in (UserRole.ADMIN, UserRole.COORD):
            self._validate_group.hide()
            return
        self._validate_group.show()

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    se.event_id,
                    s.lastname || ' ' || s.firstname AS student_name,
                    se.event_type,
                    se.event_at,
                    se.note,
                    u.lastname || ' ' || u.firstname AS created_by_name
                FROM student_event se
                JOIN larcauth_student s ON s.id = se.student_id
                JOIN larcauth_aecuser u ON u.id = se.created_by
                LEFT JOIN larcauth_learner_has_term lht
                    ON lht.fk_student_id = se.student_id
                WHERE se.validated_by IS NULL
                  AND DATE(se.event_at) = %s
                  AND lht.fk_classroom_id = %s
                ORDER BY se.event_at DESC
            """, (self._current_date.toString("yyyy-MM-dd"), self._current_class_id))

            rows = cur.fetchall()
            self._pending_table.setRowCount(len(rows))
            self._pending_table.setColumnCount(5)
            self._pending_table.setHorizontalHeaderLabels(
                ["Élève", "Type", "Heure", "Note", "Créé par"])
            self._pending_table.horizontalHeader().setStretchLastSection(True)

            self._pending_ids = []
            for i, row in enumerate(rows):
                eid, name, etype, e_at, note, creator = row
                self._pending_ids.append(eid)
                items = [
                    QTableWidgetItem(name),
                    QTableWidgetItem(etype),
                    QTableWidgetItem(e_at.strftime('%H:%M') if e_at else ''),
                    QTableWidgetItem(note or ''),
                    QTableWidgetItem(creator),
                ]
                for item in items:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._pending_table.setItem(i, 0, items[0])
                self._pending_table.setItem(i, 1, items[1])
                self._pending_table.setItem(i, 2, items[2])
                self._pending_table.setItem(i, 3, items[3])
                self._pending_table.setItem(i, 4, items[4])

            self._pending_table.resizeColumnsToContents()

        except Exception as e:
            log(f"_refresh_pending: {e}")

    def _validate_selected(self):
        selected = self._pending_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Info", "Sélectionnez des événements à valider.")
            return

        rows = set()
        for item in selected:
            rows.add(item.row())

        conn = db.server_conn
        if not conn:
            QMessageBox.warning(self, "Erreur", "Non connecté au serveur.")
            return

        try:
            cur = conn.cursor()
            for row in rows:
                eid = self._pending_ids[row]
                cur.execute("""
                    UPDATE student_event
                    SET validated_by = %s
                    WHERE event_id = %s
                """, (session.user_id, eid))
            QMessageBox.information(self, "Succès",
                f"{len(rows)} événement(s) validé(s).")
            self._refresh()

        except Exception as e:
            log(f"_validate_selected: {e}")
            QMessageBox.critical(self, "Erreur", str(e))
