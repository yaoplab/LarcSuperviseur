from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QDialog, QMenu, QTabWidget, QMessageBox,
)
from PySide6.QtCore import Qt, QDate, QDateTime, QTime, Signal
from PySide6.QtGui import QPixmap, QColor, QBrush, QPainter
from PySide6.QtCharts import (
    QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis,
)

from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.photos import get_photo_path
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.event_helpers import event_icon, event_color
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
        self._init_ui()

    def _period_dates(self) -> tuple[str, str]:
        today = QDate.currentDate()
        start = today.addMonths(-3)
        return start.toString('yyyy-MM-dd'), today.toString('yyyy-MM-dd')

    def _init_ui(self):
        p = theme_manager.palette
        s = theme_manager.font_size
        self.setObjectName("panel")
        sd_layout = QVBoxLayout(self)
        sd_layout.setContentsMargins(6, 6, 6, 6)
        sd_layout.setSpacing(6)

        # Header row
        sd_header_row = QHBoxLayout()
        self._back_btn = QPushButton("\u2190 Retour")
        self._back_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {p.primary}; "
            f"border: none; font-weight: bold; "
            f"font-size: {s(11)}px; padding: 2px 6px; }}"
            f"QPushButton:hover {{ color: {p.active}; }}")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.clicked.connect(self._on_back)
        sd_header_row.addWidget(self._back_btn)
        sd_header_row.addStretch()
        sd_layout.addLayout(sd_header_row)

        self._sd_header = QLabel("<b>\u00c9l\u00e8ve</b>")
        self._sd_header.setObjectName("panel_title")
        self._sd_class = QLabel()
        self._sd_class.setStyleSheet(f"color: {p.text_soft}; font-size: {s(11)}px;")
        sd_layout.addWidget(self._sd_header)
        sd_layout.addWidget(self._sd_class)

        # Tabs
        self._sd_tabs = QTabWidget()
        self._sd_tabs.setDocumentMode(True)

        # ---- Tab 1 : Coordonn\u00e9es ----
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
            ('tel_maison', 'T\u00e9l\u00e9phone maison'),
            ('tel_portable', 'T\u00e9l\u00e9phone portable'),
            ('date_entree', "Date d'entr\u00e9e"),
        ]:
            w = QLabel()
            w.setStyleSheet(f"font-size: {s(12)}px; color: {p.text_soft};")
            w.setWordWrap(True)
            self._sd_contact_labels[key] = w
            info_col.addWidget(w)
        info_col.addStretch()
        contact_row.addLayout(info_col, 1)

        self._sd_add_btn = QPushButton("\U0001f349")
        self._sd_add_btn.setFixedSize(100, 100)
        self._sd_add_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 12px; font-weight: bold; "
            f"font-size: {s(28)}px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}")
        self._sd_add_btn.setCursor(Qt.PointingHandCursor)
        self._sd_add_btn.setToolTip("Ajouter un \u00e9v\u00e9nement")
        self._sd_add_btn.clicked.connect(self._on_add_event)
        contact_row.addWidget(self._sd_add_btn)

        t1_layout.addLayout(contact_row)

        # KPIs
        kpi_r = QHBoxLayout()
        kpi_r.setSpacing(4)
        self._sd_kpis = {}
        for k, lbl in [('abs', 'Absences'), ('exit', 'Sorties'), ('total', 'Total \u00e9vts')]:
            f = QFrame()
            f.setObjectName("kpi_small")
            f.setStyleSheet(
                f"QFrame#kpi_small {{ background: {p.surface_variant}; "
                f"border-radius: 6px; padding: 2px; }}")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(4, 2, 4, 2)
            v = QLabel("\u2014")
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
        evt_label = QLabel("<b>Derniers \u00e9v\u00e9nements</b>")
        evt_label.setStyleSheet(f"font-size: {s(11)}px;")
        self._sd_events = QTableWidget()
        self._sd_events.setAlternatingRowColors(True)
        self._sd_events.horizontalHeader().setStretchLastSection(True)
        self._sd_events.setEditTriggers(QTableWidget.NoEditTriggers)
        self._sd_events.setSelectionBehavior(QTableWidget.SelectRows)
        self._sd_events.setContextMenuPolicy(Qt.CustomContextMenu)
        self._sd_events.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(self._sd_events, pos))
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
        self._sd_chart_tabs.addTab(tab_chart, "\u00c9volution absences")

        t1_layout.addWidget(self._sd_chart_tabs)

        scroll1.setWidget(tab1)

        # ---- Tab 2 : Parents ----
        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setFrameShape(QFrame.NoFrame)
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        t2_layout.setAlignment(Qt.AlignCenter)
        placeholder2 = QLabel("Les informations sur les parents/tuteurs\nseront bient\u00f4t disponibles.")
        placeholder2.setAlignment(Qt.AlignCenter)
        placeholder2.setStyleSheet(f"color: {p.text_disabled}; font-size: {s(13)}px;")
        t2_layout.addWidget(placeholder2)
        scroll2.setWidget(tab2)

        self._sd_tabs.addTab(scroll1, "Coordonn\u00e9es")
        self._sd_tabs.addTab(scroll2, "Parents")

        sd_layout.addWidget(self._sd_tabs, 1)

        # Placeholder quand aucun \u00e9l\u00e8ve s\u00e9lectionn\u00e9
        self._sd_placeholder = QLabel("S\u00e9lectionnez un \u00e9l\u00e8ve\ndans la liste")
        self._sd_placeholder.setAlignment(Qt.AlignCenter)
        self._sd_placeholder.setStyleSheet(f"color: {p.text_disabled}; font-size: {s(14)}px;")
        sd_layout.addWidget(self._sd_placeholder)

        self._sd_tabs.hide()

    def load(self, student_id: int):
        self._student_id = student_id
        conn = db.server_conn
        if not conn:
            return

        p = theme_manager.palette
        date_from, date_to = self._period_dates()

        try:
            cur = conn.cursor()

            # -- Infos \u00e9l\u00e8ve + coordonn\u00e9es --
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

            # Coordonn\u00e9es
            self._sd_contact_labels['full_name'].setText(
                f"<b>Nom :</b> {last_name.upper()} {first_name}")
            self._sd_contact_labels['email'].setText(
                f"<b>Email :</b> {email or '\u2014'}")
            self._sd_contact_labels['email_perso'].setText(
                f"<b>Email personnel :</b> {email_perso or '\u2014'}")
            self._sd_contact_labels['tel_maison'].setText(
                f"<b>T\u00e9l. maison :</b> {tel_maison or '\u2014'}")
            self._sd_contact_labels['tel_portable'].setText(
                f"<b>T\u00e9l. portable :</b> {tel_portable or '\u2014'}")
            self._sd_contact_labels['date_entree'].setText(
                f"<b>Date d'entr\u00e9e :</b> {date_entree.strftime('%d/%m/%Y') if date_entree else '\u2014'}")

            # Photo
            pix = QPixmap(get_photo_path(student_id))
            if not pix.isNull():
                self._sd_photo.setPixmap(
                    pix.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            if not self._sd_photo.pixmap() or self._sd_photo.pixmap().isNull():
                self._sd_photo.setText("\U0001f4f7")

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

            # -- Chart \u00e9volution absences sur le trimestre --
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
                self._sd_chart.setTitle("\u00c9volution des absences (trimestre)")
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
                self._sd_chart.setTitle("\u00c9volution des absences \u2014 aucune donn\u00e9e")

            # -- Derniers \u00e9v\u00e9nements --
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
            self._sd_events.setHorizontalHeaderLabels(["ID", "Type", "Lieu", "Mati\u00e8re", "Date", "Note", "Cr\u00e9\u00e9 par", "Valid\u00e9"])
            self._sd_events.setColumnHidden(0, True)
            for i, (eid, etype, e_at, lieu, subject, note, creator, validated) in enumerate(evts):
                ei = event_icon(etype)
                color = event_color(etype)
                items = [
                    QTableWidgetItem(str(eid)),
                    QTableWidgetItem(f"{ei} {etype}"),
                    QTableWidgetItem(lieu or ''),
                    QTableWidgetItem(subject or ''),
                    QTableWidgetItem(e_at.strftime('%d/%m %H:%M') if e_at else ''),
                    QTableWidgetItem(note or ''),
                    QTableWidgetItem(creator),
                    QTableWidgetItem("\u2713" if validated else ''),
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

        except Exception as e:
            log(f"StudentDetail.load: {e}")

    def _on_add_event(self):
        sid = self._student_id
        if not sid:
            return
        dlg = EventGenerator(sid, self)
        if dlg.exec():
            data = dlg.get_data()
            conn = db.server_conn
            if not conn:
                QMessageBox.warning(self, "Erreur", "Aucune connexion base de donn\u00e9es.")
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
                log(f"_on_add_event insert: {e}")
                conn.rollback()
                QMessageBox.critical(self, "Erreur", f"\u00c9chec de l'enregistrement : {e}")
                return
            self.load(sid)

    def _on_back(self):
        self._sd_tabs.hide()
        self._sd_placeholder.show()
        self.back_requested.emit()

    def _get_event_id_from_table(self, table: QTableWidget) -> int | None:
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
        edit_action = menu.addAction("\u270f\ufe0f Modifier")
        validate_action = menu.addAction("\U0001f512 D\u00e9valider" if is_validated else "\u2705 Valider")
        delete_action = menu.addAction("\U0001f5d1\ufe0f Supprimer")
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
        if dlg.exec() == QDialog.Accepted:
            self.load(self._student_id)

    def _toggle_validation(self, event_id: int):
        event = self._actions.get_event_by_id(event_id)
        was_validated = event is not None and event.get('validated_by') is not None
        if self._actions.toggle_validation(event_id, not was_validated):
            self.load(self._student_id)

    def _delete_event(self, event_id: int):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer d\u00e9finitivement l'\u00e9v\u00e9nement #{event_id} ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
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
