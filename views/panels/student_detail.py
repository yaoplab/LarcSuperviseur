from larccommon.l10n import _
from phibuilder.widgets import (
    M3Button,
    M3Dialog,
    M3Frame,
    M3HeaderView,
    M3Label,
    M3Menu,
    M3ScrollArea,
    M3TableWidget,
    M3TabWidget,
)
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QDateTimeAxis,
    QLineSeries,
    QValueAxis,
)
from PySide6.QtCore import QDate, QDateTime, Qt, QTime, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from LarcSuperviseur.common.event_helpers import event_color, event_icon
from LarcSuperviseur.common.photos import get_photo_path
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.views.core.data_loader import DataLoader
from LarcSuperviseur.views.core.event_actions import EventActions
from LarcSuperviseur.views.core.event_dialog import EventEditDialog
from LarcSuperviseur.views.dialogs.event_generator import EventGenerator


class StudentDetail(QWidget):
    """Student detail with tabs, photo, and event management."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._student_id = 0
        self._actions = EventActions()
        self._loader = DataLoader()
        self._init_ui()

    def _period_dates(self) -> tuple[str, str]:
        today = QDate.currentDate()
        start = today.addMonths(-3)
        return start.toString("yyyy-MM-dd"), today.toString("yyyy-MM-dd")

    def _init_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        self.setObjectName("panel")
        sd_layout = QVBoxLayout(self)
        sd_layout.setContentsMargins(6, 6, 6, 6)
        sd_layout.setSpacing(6)

        # Header row
        sd_header_row = QHBoxLayout()
        self._back_btn = M3Button(_("common.button.back"))
        self._back_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {p.primary}; "
            f"border: none; font-weight: bold; "
            f"font-size: {s(11)}px; padding: 2px 6px; }}"
            f"QPushButton:hover {{ color: {p.active}; }}"
        )
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.clicked.connect(self._on_back)
        sd_header_row.addWidget(self._back_btn)
        sd_header_row.addStretch()
        sd_layout.addLayout(sd_header_row)

        self._sd_header = M3Label(f"<b>{_('student.title')}</b>")
        self._sd_header.setObjectName("panel_title")
        self._sd_class = M3Label()
        self._sd_class.setStyleSheet(f"color: {p.text_soft}; font-size: {s(11)}px;")
        sd_layout.addWidget(self._sd_header)
        sd_layout.addWidget(self._sd_class)

        # Tabs
        self._sd_tabs = M3TabWidget()
        self._sd_tabs.setDocumentMode(True)

        # ---- Tab 1 : Coordonn\u00e9es ----
        scroll1 = M3ScrollArea()
        scroll1.setWidgetResizable(True)
        scroll1.setFrameShape(M3Frame.NoFrame)
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        t1_layout.setContentsMargins(4, 4, 4, 4)
        t1_layout.setSpacing(6)

        # Photo + infos + add event button
        contact_row = QHBoxLayout()
        self._sd_photo = M3Label()
        self._sd_photo.setFixedSize(150, 150)
        self._sd_photo.setStyleSheet(f"background: {p.surface_variant}; border-radius: 8px;")
        self._sd_photo.setAlignment(Qt.AlignCenter)
        contact_row.addWidget(self._sd_photo)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self._sd_contact_labels = {}
        for key, lbl in [
            ("full_name", "Nom"),
            ("email", "Email"),
            ("email_perso", "Email personnel"),
            ("tel_maison", "T\u00e9l\u00e9phone maison"),
            ("tel_portable", "T\u00e9l\u00e9phone portable"),
            ("date_entree", "Date d'entr\u00e9e"),
        ]:
            w = M3Label()
            w.setStyleSheet(f"font-size: {s(12)}px; color: {p.text_soft};")
            w.setWordWrap(True)
            self._sd_contact_labels[key] = w
            info_col.addWidget(w)
        info_col.addStretch()
        contact_row.addLayout(info_col, 1)

        self._sd_add_btn = M3Button("\U0001f349")
        self._sd_add_btn.setFixedSize(100, 100)
        self._sd_add_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 12px; font-weight: bold; "
            f"font-size: {s(28)}px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}"
        )
        self._sd_add_btn.setCursor(Qt.PointingHandCursor)
        self._sd_add_btn.setToolTip(_("student.add_event"))
        self._sd_add_btn.clicked.connect(self._on_add_event)
        contact_row.addWidget(self._sd_add_btn)

        t1_layout.addLayout(contact_row)

        # KPIs
        kpi_r = QHBoxLayout()
        kpi_r.setSpacing(4)
        self._sd_kpis = {}
        for k, lbl in [
            ("abs", _("chart.absences")),
            ("exit", _("kpi.exit")),
            ("total", _("kpi.total_events")),
        ]:
            f = M3Frame()
            f.setObjectName("kpi_small")
            f.setStyleSheet(
                f"QFrame#kpi_small {{ background: {p.surface_variant}; "
                f"border-radius: 6px; padding: 2px; }}"
            )
            fl = QVBoxLayout(f)
            fl.setContentsMargins(4, 2, 4, 2)
            v = M3Label("\u2014")
            v.setStyleSheet(f"font-size: {s(18)}px; font-weight: bold; color: {p.primary};")
            v.setAlignment(Qt.AlignCenter)
            l = M3Label(lbl)
            l.setStyleSheet(f"font-size: {s(9)}px; color: {p.text_soft};")
            l.setAlignment(Qt.AlignCenter)
            fl.addWidget(v)
            fl.addWidget(l)
            self._sd_kpis[k] = v
            kpi_r.addWidget(f)
        t1_layout.addLayout(kpi_r)

        # Events
        evt_label = M3Label(f"<b>{_('student.tab.events')}</b>")
        evt_label.setStyleSheet(f"font-size: {s(11)}px;")
        self._sd_events = M3TableWidget()
        self._sd_events.setAlternatingRowColors(True)
        self._sd_events.horizontalHeader().setStretchLastSection(True)
        self._sd_events.setEditTriggers(M3TableWidget.NoEditTriggers)
        self._sd_events.setSelectionBehavior(M3TableWidget.SelectRows)
        self._sd_events.setContextMenuPolicy(Qt.CustomContextMenu)
        self._sd_events.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(self._sd_events, pos)
        )
        self._sd_events.cellDoubleClicked.connect(self._on_event_table_dblclick)
        t1_layout.addWidget(evt_label)
        t1_layout.addWidget(self._sd_events, 1)

        # Bottom row: chart tabs
        self._sd_chart_tabs = M3TabWidget()
        self._sd_chart_tabs.setMinimumHeight(200)

        tab_chart = QWidget()
        tab_chart_layout = QVBoxLayout(tab_chart)
        tab_chart_layout.setContentsMargins(0, 0, 0, 0)
        self._sd_chart_view = QChartView()
        self._sd_chart_view.setRenderHint(QPainter.Antialiasing)
        self._sd_chart = QChart()
        self._sd_chart_view.setChart(self._sd_chart)
        tab_chart_layout.addWidget(self._sd_chart_view)
        self._sd_chart_tabs.addTab(tab_chart, _("chart.evolution_absences"))

        t1_layout.addWidget(self._sd_chart_tabs)

        scroll1.setWidget(tab1)

        # ---- Tab 2 : Parents ----
        scroll2 = M3ScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setFrameShape(M3Frame.NoFrame)
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        t2_layout.setAlignment(Qt.AlignCenter)
        placeholder2 = M3Label(_("student.parents_placeholder"))
        placeholder2.setAlignment(Qt.AlignCenter)
        placeholder2.setStyleSheet(f"color: {p.text_disabled}; font-size: {s(13)}px;")
        t2_layout.addWidget(placeholder2)
        scroll2.setWidget(tab2)

        self._sd_tabs.addTab(scroll1, _("student.tab.coords"))
        self._sd_tabs.addTab(scroll2, _("student.tab.parents"))

        sd_layout.addWidget(self._sd_tabs, 1)

        # Placeholder quand aucun \u00e9l\u00e8ve s\u00e9lectionn\u00e9
        self._sd_placeholder = M3Label(_("student.no_selection"))
        self._sd_placeholder.setAlignment(Qt.AlignCenter)
        self._sd_placeholder.setStyleSheet(f"color: {p.text_disabled}; font-size: {s(14)}px;")
        sd_layout.addWidget(self._sd_placeholder)

        self._sd_tabs.hide()

    def load(self, student_id: int):
        self._student_id = student_id
        p = theme_manager.palette
        date_from, date_to = self._period_dates()

        info = self._loader.get_student_info(student_id)
        if not info:
            return

        name = f"{info['first_name']} {info['last_name']}"
        self._sd_header.setText(f"<b>{name}</b>")
        self._sd_class.setText(info["class_label"])

        self._sd_contact_labels["full_name"].setText(
            f"<b>{_('student.contact.name')} :</b> {info['last_name'].upper()} {info['first_name']}"
        )
        self._sd_contact_labels["email"].setText(
            f"<b>{_('student.contact.email')} :</b> {info.get('email') or '\u2014'}"
        )
        self._sd_contact_labels["email_perso"].setText(
            f"<b>{_('student.contact.email_perso')} :</b> {info.get('email_perso') or '\u2014'}"
        )
        self._sd_contact_labels["tel_maison"].setText(
            f"<b>{_('student.contact.tel_maison')} :</b> {info.get('tel_maison') or '\u2014'}"
        )
        self._sd_contact_labels["tel_portable"].setText(
            f"<b>{_('student.contact.tel_portable')} :</b> {info.get('tel_portable') or '\u2014'}"
        )
        self._sd_contact_labels["date_entree"].setText(
            f"<b>{_('student.contact.date_entree')} :</b> {info.get('date_entree').strftime('%d/%m/%Y') if info.get('date_entree') else '\u2014'}"
        )

        pix = QPixmap(get_photo_path(student_id))
        if not pix.isNull():
            self._sd_photo.setPixmap(
                pix.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        if not self._sd_photo.pixmap() or self._sd_photo.pixmap().isNull():
            self._sd_photo.setText("\U0001f4f7")

        kpi = self._loader.get_student_kpis(student_id, date_from, date_to)
        self._sd_kpis["abs"].setText(str(kpi.get("abs_count", 0)))
        self._sd_kpis["exit"].setText(str(kpi.get("exit_count", 0)))
        self._sd_kpis["total"].setText(str(kpi.get("total", 0)))

        self._sd_chart.removeAllSeries()
        for ax in self._sd_chart.axes():
            self._sd_chart.removeAxis(ax)

        from datetime import datetime, timedelta

        term_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        term_end = datetime.now().strftime("%Y-%m-%d")

        trend = self._loader.get_student_absence_trend(student_id, term_start, term_end)
        if trend:
            line = QLineSeries()
            line.setColor(QColor(p.error))
            for row in trend:
                d = row["date"]
                cnt = row["count"]
                qd = QDate(d.year, d.month, d.day)
                dt = QDateTime(qd, QTime(0, 0))
                line.append(dt.toMSecsSinceEpoch(), cnt)
            self._sd_chart.addSeries(line)
            self._sd_chart.setTitle(_("chart.abs_trend_term"))
            self._sd_chart.setAnimationOptions(QChart.SeriesAnimations)
            self._sd_chart.legend().setVisible(False)
            ax_x = QDateTimeAxis()
            ax_x.setFormat("dd/MM")
            ax_x.setLabelsAngle(-45)
            self._sd_chart.addAxis(ax_x, Qt.AlignBottom)
            line.attachAxis(ax_x)
            ax_y = QValueAxis()
            max_t = max(row["count"] for row in trend)
            ax_y.setRange(0, max_t + 2)
            self._sd_chart.addAxis(ax_y, Qt.AlignLeft)
            line.attachAxis(ax_y)
        else:
            self._sd_chart.setTitle(_("chart.abs_trend_nodata"))

        evts = self._loader.get_student_events(student_id)
        self._sd_events.setRowCount(len(evts))
        self._sd_events.setColumnCount(8)
        self._sd_events.setHorizontalHeaderLabels(
            [
                _("table.id"),
                _("table.type"),
                _("table.location"),
                _("table.subject"),
                _("table.date"),
                _("table.note"),
                _("table.created_by"),
                _("table.validated"),
            ]
        )
        self._sd_events.setColumnHidden(0, True)
        for i, evt in enumerate(evts):
            ei = event_icon(evt["event_type"])
            color = event_color(evt["event_type"])
            items = [
                QTableWidgetItem(str(evt["event_id"])),
                QTableWidgetItem(f"{ei} {evt['event_type']}"),
                QTableWidgetItem(evt.get("lieu_label") or ""),
                QTableWidgetItem(evt.get("subject_label") or ""),
                QTableWidgetItem(
                    evt["event_at"].strftime("%d/%m %H:%M") if evt.get("event_at") else ""
                ),
                QTableWidgetItem(evt.get("note") or ""),
                QTableWidgetItem(evt.get("creator")),
                QTableWidgetItem("\u2713" if evt.get("validated_by") else ""),
            ]
            items[1].setForeground(QBrush(QColor(color)))
            for j, it in enumerate(items):
                if j not in (1, 5):
                    it.setTextAlignment(Qt.AlignCenter)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self._sd_events.setItem(i, j, it)
        hh = self._sd_events.horizontalHeader()
        hh.setSectionResizeMode(0, M3HeaderView.Fixed)
        self._sd_events.setColumnWidth(0, 0)
        hh.setSectionResizeMode(1, M3HeaderView.Interactive)
        self._sd_events.setColumnWidth(1, 300)
        hh.setSectionResizeMode(2, M3HeaderView.Interactive)
        self._sd_events.setColumnWidth(2, 120)
        hh.setSectionResizeMode(3, M3HeaderView.Interactive)
        self._sd_events.setColumnWidth(3, 110)
        hh.setSectionResizeMode(4, M3HeaderView.Interactive)
        self._sd_events.setColumnWidth(4, 100)
        hh.setSectionResizeMode(5, M3HeaderView.Stretch)
        hh.setSectionResizeMode(6, M3HeaderView.Interactive)
        self._sd_events.setColumnWidth(6, 200)
        hh.setSectionResizeMode(7, M3HeaderView.Interactive)
        self._sd_events.setColumnWidth(7, 200)

        self._sd_tabs.show()
        self._sd_placeholder.hide()

    def _on_add_event(self):
        sid = self._student_id
        if not sid:
            return
        dlg = EventGenerator(sid, self)
        if dlg.exec():
            data = dlg.get_data()
            data["created_by"] = session.user_id
            if not self._loader.insert_event(data):
                QMessageBox.critical(self, _("common.dialog.error_title"), _("student.save_error"))
                return
            self.load(sid)

    def _on_back(self):
        self._sd_tabs.hide()
        self._sd_placeholder.show()
        self.back_requested.emit()

    def _get_event_id_from_table(self, table: M3TableWidget) -> int | None:
        idx = table.currentRow()
        if idx < 0:
            return None
        item = table.item(idx, 0)
        return int(item.text()) if item and item.text().isdigit() else None

    def _show_context_menu(self, table: M3TableWidget, pos):
        eid = self._get_event_id_from_table(table)
        if not eid:
            return
        event = self._actions.get_event_by_id(eid)
        is_validated = event is not None and event.get("validated_by") is not None
        menu = M3Menu(self)
        edit_action = menu.addAction(_("context_menu.edit"))
        validate_action = menu.addAction(
            _("context_menu.invalidate") if is_validated else _("context_menu.validate")
        )
        delete_action = menu.addAction(_("context_menu.delete"))
        chosen = menu.exec(table.viewport().mapToGlobal(pos))
        if chosen == edit_action:
            self._edit_event(eid)
        elif chosen == validate_action:
            self._toggle_validation(eid)
        elif chosen == delete_action:
            self._delete_event(eid)

    def _on_event_table_dblclick(self, row: int, col: int):
        item = self._sd_events.item(row, 0)
        eid = int(item.text()) if item and item.text().isdigit() else None
        if eid:
            self._edit_event(eid)

    def _edit_event(self, event_id: int):
        dlg = EventEditDialog(event_id, self)
        if dlg.exec() == M3Dialog.Accepted:
            self.load(self._student_id)

    def _toggle_validation(self, event_id: int):
        event = self._actions.get_event_by_id(event_id)
        was_validated = event is not None and event.get("validated_by") is not None
        if self._actions.toggle_validation(event_id, not was_validated):
            self.load(self._student_id)

    def _delete_event(self, event_id: int):
        reply = QMessageBox.question(
            self,
            _("student.confirm_delete_event"),
            _("common.dialog.delete_event").format(id=event_id),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if self._actions.delete_event(event_id):
            self.load(self._student_id)

    def refresh_theme(self):
        sid = self._student_id
        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
        self._init_ui()
        if sid:
            self.load(sid)
