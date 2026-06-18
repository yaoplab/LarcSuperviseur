from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QFrame, QTabWidget, QMenu, QDialog, QMessageBox,
)
from PySide6.QtCore import Qt, QDate, QDateTime, QTime, QCoreApplication
from PySide6.QtGui import QColor, QBrush, QFont, QPainter
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis,
    QValueAxis, QPieSeries, QLineSeries, QDateTimeAxis,
)

from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.event_helpers import event_icon, event_color
from LarcSuperviseur.views.core.data_loader import DataLoader
from LarcSuperviseur.views.core.event_actions import EventActions
from LarcSuperviseur.views.core.event_dialog import EventEditDialog


class GroupPanel(QWidget):
    """Group statistics: KPIs, charts, and event history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loader = DataLoader()
        self._actions = EventActions()
        self._current_mode = ""
        self._term_id = 0
        self._init_ui()

    def _init_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(8)

        self._loading_label = QLabel()
        self._loading_label.setAlignment(Qt.AlignCenter)
        self._loading_label.setVisible(False)
        self._main_layout.addWidget(self._loading_label)

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
        self._main_layout.addLayout(kpi_row)

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
            lambda pos: self._show_context_menu(self._history_table, pos))
        self._history_table.cellDoubleClicked.connect(self._on_event_table_dblclick)
        self._history_layout.addWidget(history_title)

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
        filter_btn.clicked.connect(self._load_history)
        filter_row.addWidget(filter_btn)
        filter_row.addStretch()
        self._history_layout.addLayout(filter_row)
        self._history_layout.addWidget(self._history_table)
        self._history_group.setMinimumHeight(320)
        self._main_layout.addWidget(self._history_group, 1)

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

        self._main_layout.addLayout(bottom_row)

    def load(self, mode: str, date_from: str | None = None, date_to: str | None = None):
        self._current_mode = mode
        self._term_id = self._loader.get_active_term()
        if not self._term_id:
            return

        if date_from is None or date_to is None:
            date_from, date_to = self._period_dates()

        self._set_loading(True, "Statistiques...")
        try:
            self._update_everything(mode, date_from, date_to)
        except Exception as e:
            log(f"GroupPanel.load: {e}")
        self._set_loading(False)

    def _update_everything(self, mode, date_from, date_to):
        p = theme_manager.palette

        rows = self._loader.get_class_stats(mode, date_from, date_to)

        total_students = sum(r['student_count'] for r in rows)
        total_abs = sum(r['abs_count'] for r in rows)
        total_exits = sum(r['exit_count'] for r in rows)
        total_events = sum(r['event_count'] for r in rows)

        self._kpi_cards['total'].setText(str(total_students))
        present_val = max(0, total_students - total_abs) if total_abs > 0 else total_students
        self._kpi_cards['present'].setText(str(present_val))
        self._kpi_cards['absent'].setText(str(total_abs))
        self._kpi_cards['exit'].setText(str(total_exits))

        self._stats_table.setRowCount(len(rows))
        self._stats_table.setColumnCount(5)
        self._stats_table.setHorizontalHeaderLabels(
            ["Classe", "Événements", "Absences", "Sorties", "Élèves"])

        for i, r in enumerate(rows):
            items = [
                QTableWidgetItem(r['label']),
                QTableWidgetItem(str(r['event_count'])),
                QTableWidgetItem(str(r['abs_count'])),
                QTableWidgetItem(str(r['exit_count'])),
                QTableWidgetItem(str(r['student_count'])),
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

        self._abs_bar.removeAllSeries()
        for ax in self._abs_bar.axes():
            self._abs_bar.removeAxis(ax)
        abs_set = QBarSet("Absences")
        abs_set.setColor(QColor(p.error))
        cat_names = [r['label'] for r in rows]
        for r in rows:
            abs_set << r['abs_count']
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
            max_abs = max(r['abs_count'] for r in rows)
            axis_y.setRange(0, max(max_abs + 2, 10))
            self._abs_bar.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
        else:
            self._abs_bar.setTitle("Absences par classe — aucune donnée")

        self._exit_bar.removeAllSeries()
        for ax in self._exit_bar.axes():
            self._exit_bar.removeAxis(ax)
        exit_set = QBarSet("Sorties")
        exit_set.setColor(QColor(p.tertiary))
        for r in rows:
            exit_set << r['exit_count']
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
            max_exit = max(r['exit_count'] for r in rows)
            ex_axis_y.setRange(0, max(max_exit + 2, 5))
            self._exit_bar.addAxis(ex_axis_y, Qt.AlignLeft)
            exit_series.attachAxis(ex_axis_y)
        else:
            self._exit_bar.setTitle("Sorties par classe — aucune donnée")

        self._trend_chart.removeAllSeries()
        for ax in self._trend_chart.axes():
            self._trend_chart.removeAxis(ax)
        trend_rows = self._loader.get_attendance_trend(mode, date_from, date_to)
        if trend_rows:
            line = QLineSeries()
            line.setColor(QColor(p.error))
            line.setName("Absences")
            for tr in trend_rows:
                d = tr['date']
                qd = QDate(d.year, d.month, d.day)
                dt = QDateTime(qd, QTime(0, 0))
                line.append(dt.toMSecsSinceEpoch(), tr['count'])
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
            max_t = max(tr['count'] for tr in trend_rows)
            axis_y_t.setRange(0, max_t + 2)
            self._trend_chart.addAxis(axis_y_t, Qt.AlignLeft)
            line.attachAxis(axis_y_t)
        else:
            self._trend_chart.setTitle("Tendance des absences — aucune donnée")

        self._donut_chart.removeAllSeries()
        pr = self._loader.get_presence_rate(mode, date_from, date_to)
        present_count = pr['present']
        absent_count = pr['absent']
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

        self._load_history()

    def _load_history(self):
        if not self._term_id:
            return
        self._set_loading(True, "Événements...")
        try:
            if self._history_filter_class.count() <= 1:
                classes = self._loader.get_all_classrooms()
                for cid, clabel in classes:
                    self._history_filter_class.addItem(clabel, cid)
                self._history_filter_class.model().sort(0)
            if self._history_filter_type.count() == 0:
                types = self._loader.get_all_event_types()
                for et in types:
                    self._history_filter_type.addItem(et)

            sel_class = self._history_filter_class.currentData()
            sel_type = self._history_filter_type.currentText().strip()
            date_from = self._history_filter_date_from.date().toString('yyyy-MM-dd')
            date_to = self._history_filter_date_to.date().toString('yyyy-MM-dd')

            if sel_type == '':
                sel_type = None

            rows = self._loader.get_event_history(
                self._current_mode, date_from, date_to,
                class_id=sel_class, type_filter=sel_type)

            self._history_table.setRowCount(len(rows))
            self._history_table.setColumnCount(10)
            self._history_table.setHorizontalHeaderLabels(
                ["ID", "Élève", "Classe", "Type", "Lieu", "Matière", "Heure", "Note", "Créé par", "Validé"])
            self._history_table.setColumnHidden(0, True)

            for i, row in enumerate(rows):
                eid = row['event_id']
                name = row['student_name']
                cls_name = row['class_name']
                etype = row['event_type']
                e_at = row['event_at']
                lieu = row['lieu_label']
                subject = row['subject_label']
                note = row['note']
                creator = row['created_by']
                validated = row['validated_by']

                ei = event_icon(etype)
                color = event_color(etype)
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
        except Exception as e:
            log(f"GroupPanel._load_history: {e}")
        self._set_loading(False)

    def _period_dates(self) -> tuple[str, str]:
        today = QDate.currentDate()
        start = today.addMonths(-3)
        return start.toString('yyyy-MM-dd'), today.toString('yyyy-MM-dd')

    def _set_loading(self, busy: bool, msg: str = "Chargement..."):
        self._loading_label.setText("⟳ " + msg if busy else "")
        self._loading_label.setVisible(busy)
        QCoreApplication.processEvents()

    # -- Context menu événements --------------------------------------------

    def _get_event_id_from_table(self, table: QTableWidget):
        idx = table.currentRow()
        if idx < 0:
            return None
        item = table.item(idx, 0)
        return int(item.text()) if item and item.text().isdigit() else None

    def _show_context_menu(self, table: QTableWidget, pos):
        eid = self._get_event_id_from_table(table)
        if not eid:
            return
        event = self._actions.get_event_by_id(eid)
        is_validated = event is not None and event.get('validated_by') is not None

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
        dlg = EventEditDialog(event_id, self)
        if dlg.exec() == QDialog.Accepted:
            self._load_history()

    def _toggle_validation(self, event_id: int):
        event = self._actions.get_event_by_id(event_id)
        was_validated = event is not None and event.get('validated_by') is not None
        if self._actions.toggle_validation(event_id, not was_validated):
            self._load_history()

    def _delete_event(self, event_id: int):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer définitivement l'événement #{event_id} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        if self._actions.delete_event(event_id):
            self._load_history()
