from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDateEdit, QFrame, QScrollArea, QGridLayout,
    QDialog, QDialogButtonBox, QTextEdit,
    QButtonGroup,
    QMenu, QStackedWidget, QTabWidget, QTimeEdit,
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal, QDateTime, QTime
from PySide6.QtGui import QColor, QBrush, QPixmap, QFont, QPainter
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis,
    QValueAxis, QPieSeries, QLineSeries, QDateTimeAxis,
)
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.network import detect_network
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.photos import get_photo_path
from LarcSuperviseur.views.core.time_manager import TimeManager
from LarcSuperviseur.views.top_bar import TopBar
from LarcSuperviseur.views.core.cardsList.config import CARD_THEMES
from LarcSuperviseur.common.trace import trace


from LarcSuperviseur.common.event_helpers import event_icon, event_color
from LarcSuperviseur.views.core.cardsList.card import StudentCard
from LarcSuperviseur.views.dialogs.event_generator import EventGenerator
from LarcSuperviseur.views.dialogs.timetable_editor import TimetableEditor


# ---------------------------------------------------------------------------
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
            QPushButton#period_btn {{
                min-width: 89px; max-width: 89px; height: 34px;
                font-size: {s(13)}px; font-weight: normal;
                border: 2px solid transparent; border-radius: 4px;
                padding: 0;
                background: {p.surface_variant}; color: {p.text_strong};
            }}
            QPushButton#period_btn:hover {{
                background: {p.primary_container}; border-color: {p.primary};
            }}
            QPushButton#period_btn:checked {{
                background: {p.primary}; color: {p.on_primary};
                border: 2px solid {p.primary}; font-weight: bold;
            }}
        """

    def __init__(self):
        super().__init__()
        trace(f" MainWindow.__init__: démarre")
        self.setWindowTitle(f"LarcSuperviseur — {session.full_name} ({session.role.value})")
        self._current_class_id: int = 0
        self._current_class_label: str = ''
        self._selected_btn: QPushButton | None = None
        self._current_group_mode: str = ''  # 'pei', 'dp', 'etab', 'class'
        self._current_weekday: int = 0
        self._selected_student_id: int = 0
        self._students: list[dict] = []
        self._classes: list = []
        self._programs: dict = {}
        self._time_manager = TimeManager()
        self._init_ui()
        trace(f" MainWindow.__init__: _init_ui OK, appel _load_initial_data")
        self._load_initial_data()
        trace(f" MainWindow.__init__: _load_initial_data terminé")
        QTimer.singleShot(30000, self._refresh_timer)

    def _init_ui(self):
        self.setStyleSheet(self._STYLE)
        outer = QVBoxLayout()
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(6)

        # -- Top bar ------------------------------------------------------------
        self._top_bar = TopBar(
            on_period_click=self._on_period_clicked,
            on_theme_change=self._on_theme_selected,
            on_refresh=self.refresh_all,
        )
        outer.addWidget(self._top_bar)

        # -- Main area (sidebar + content) ------------------------------------
        main_h = QHBoxLayout()
        main_h.setSpacing(6)

        # Sidebar gauche
        self._sidebar = QFrame()
        self._sidebar.setObjectName("panel")
        self._sidebar.setFixedWidth(233)
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
        # Boutons thèmes Phi
        self._phi_group = QButtonGroup(self)
        self._phi_group.setExclusive(True)
        self._card_theme: str = 'medium'
        for key, label in [('compact', '▱'), ('medium', '▰'), ('large', '▣')]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedSize(34, 34)
            btn.setToolTip(f"Phi {key.capitalize()}")
            btn.setStyleSheet(
                f"QPushButton {{ font-size: 16px; border: 1px solid {theme_manager.palette.outline_variant}; "
                f"border-radius: 4px; background: {theme_manager.palette.surface_variant}; "
                f"color: {theme_manager.palette.text_strong}; }}"
                f"QPushButton:checked {{ background: {theme_manager.palette.primary}; "
                f"color: {theme_manager.palette.on_primary}; border: 2px solid {theme_manager.palette.primary}; }}"
            )
            self._phi_group.addButton(btn)
            btn.clicked.connect(lambda checked, k=key: self._on_card_theme(k))
            if key == 'medium':
                btn.setChecked(True)
            header_row.addWidget(btn)
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

        info_col = QGridLayout()
        info_col.setSpacing(8)
        info_col.setColumnStretch(0, 0)
        info_col.setColumnStretch(1, 1)
        self._sd_contact_labels = {}
        for i, (key, lbl) in enumerate([
            ('full_name', 'Nom'),
            ('email', 'Email'),
            ('email_perso', 'Email personnel'),
            ('tel_maison', 'Téléphone maison'),
            ('tel_portable', 'Téléphone portable'),
            ('date_entree', "Date d'entrée"),
        ]):
            label = QLabel(f"<b>{lbl} :</b>")
            label.setStyleSheet(f"font-size: {s(13)}px; color: {p.text_strong};")
            w = QLabel()
            w.setStyleSheet(f"font-size: {s(13)}px; color: {p.text_soft}; padding-left: 8px;")
            w.setWordWrap(True)
            self._sd_contact_labels[key] = w
            info_col.addWidget(label, i, 0, Qt.AlignLeft)
            info_col.addWidget(w, i, 1, Qt.AlignLeft)
        info_col.setRowStretch(len([1,2,3,4,5,6]), 1)
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
        trace(f" _build_sidebar: classes={len(self._classes)}, groups={ {k:len(v) for k,v in groups.items()} }")

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
                f"font-weight: bold; font-size: {s(13)}px; text-align: left; padding: 4px 2px; }}"
                f"QPushButton:hover {{ color: {p.primary}; border-bottom: 2px solid {p.primary}; }}",
                min_h=34
            )
            sec_hdr.setText(sec_name)
            sec_hdr.clicked.connect(lambda checked, sn=sec_name: self._on_section_clicked(sn))
            layout.addWidget(sec_hdr)

            # Mini-grille 2 colonnes pour cette section
            grd = QGridLayout()
            grd.setSpacing(8)

            for col_idx, (hdr_text, prog_key) in enumerate(columns):
                fg, bg, on_fg, _ = prog_style[prog_key]
                items = groups.get(prog_key, [])

                col_hdr = _make_btn(
                    f"QPushButton {{ background: {fg}; color: {on_fg}; border: none; "
                    f"border-radius: 4px; font-weight: bold; font-size: {s(13)}px; padding: 3px; }}"
                    f"QPushButton:hover {{ opacity: 0.8; }}",
                    min_h=21
                )
                col_hdr.setText(hdr_text)
                col_hdr.clicked.connect(lambda checked, pk=prog_key: self._on_prog_clicked(pk))
                grd.addWidget(col_hdr, 0, col_idx)

                for i, (cid, label) in enumerate(items):
                    btn = _make_btn(
                        f"QPushButton {{ background: {bg}; color: {fg}; border: none; "
                        f"border-radius: 4px; font-size: {s(13)}px; padding: 2px; }}"
                        f"QPushButton:hover {{ background: {fg}; color: {bg}; }}",
                        min_h=34
                    )
                    btn.setText(label)
                    btn.clicked.connect(lambda checked, c=cid, l=label, b=btn: self._on_class_clicked(c, l, b))
                    grd.addWidget(btn, i + 1, col_idx)

            layout.addLayout(grd)
            layout.addSpacing(8)

        # Toutes les classes
        self._all_btn = _make_btn(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; font-weight: bold; font-size: {s(21)}px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}",
            min_h=55
        )
        self._all_btn.setText("Toutes les classes")
        self._all_btn.clicked.connect(self._on_all_clicked)
        layout.addWidget(self._all_btn)
        layout.addStretch()
        trace(f" _build_sidebar: terminé")

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
        trace(f" _on_all_clicked: lance _show_group_mode(grp_all)")
        self._show_group_mode('grp_all')
        trace(f" _on_all_clicked: terminé")

    def _select_btn(self, btn: QPushButton | None):
        if self._selected_btn:
            self._selected_btn.setChecked(False)
        self._selected_btn = btn
        if btn:
            btn.setChecked(True)

    def _load_initial_data(self):
        self._top_bar.set_loading(True, "Données initiales...")
        trace(f" _load_initial_data: démarre")
        conn = db.server_conn
        trace(f" _load_initial_data: server_conn={conn is not None}")
        if not conn:
            QMessageBox.warning(self, "Erreur", "Non connecté au serveur.")
            self._top_bar.set_loading(False)
            return

        try:
            cur = conn.cursor()

            # Terme actif (via academicyear, pas les dates)
            cur.execute("""
                SELECT t.id, t.label FROM larcauth_term t, larcauth_academicyear ay
                WHERE ay.s_id = 1 AND t.trim = ay.current_term_number
                LIMIT 1
            """)
            r = cur.fetchone()
            if r:
                self._time_manager.term_id = int(r[0])
                self._time_manager.term_label = r[1]
            else:
                self._time_manager.term_id = 0
                self._time_manager.term_label = ''

            # Programmes (PEI, DP, ...)
            cur.execute("SELECT id, sigle, label FROM larcauth_program ORDER BY sigle")
            self._programs = {r[0]: {'sigle': r[1], 'label': r[2]} for r in cur.fetchall()}
            trace(f" _load_initial_data: {len(self._programs)} programmes chargés")

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
            trace(f" _load_initial_data: {len(self._classes)} classes chargées")

            # Unités de période
            from LarcSuperviseur.views.core.data_loader import DataLoader
            self._time_manager.unit_periods = DataLoader().get_unit_periods()
            self._top_bar.set_unit_periods(self._time_manager.unit_periods)

            # Construire la sidebar
            trace(f" _load_initial_data: construction sidebar")
            self._build_sidebar()
            trace(f" _load_initial_data: sidebar construite")

            # Activer le mode groupe par défaut
            self._on_all_clicked()
            self._top_bar.set_loading(False)

        except Exception as e:
            log(f"_load_initial_data: {e}")
            QMessageBox.critical(self, "Erreur", str(e))
            self._top_bar.set_loading(False)

    def _on_period_clicked(self, key: str):
        self._time_manager.select_period(key)
        self.refresh_all()

    def _on_theme_selected(self, key: str):
        theme_manager.set_active(key)
        self.setStyleSheet(self._STYLE)
        self._top_bar.restyle()
        self._build_sidebar()
        self._rebuild_student_detail_theme()
        self._top_bar.update_network()
        if self._current_group_mode:
            self.refresh_all()

    # ---- Mode groupe -------------------------------------------------------

    def _show_group_mode(self, mode: str):
        self._content_stack.setCurrentIndex(0)
        self._group_scroll.verticalScrollBar().setValue(0)
        self._top_bar.show_period_row(True)
        trace(f" _show_group_mode({mode}): chargement stats + historique")
        self._load_group_stats(mode)
        self._load_global_history(mode)
        trace(f" _show_group_mode({mode}): terminé")

    def _load_group_stats(self, mode: str):
        self._top_bar.set_loading(True, "Statistiques...")
        conn = db.server_conn
        trace(f" _load_group_stats: mode={mode}, server_conn={conn is not None}, term_id={self._time_manager.term_id}")
        if not conn or not self._time_manager.term_id:
            self._top_bar.set_loading(False)
            return

        p = theme_manager.palette
        date_from, date_to = self._time_manager.period_dates()

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

            self._top_bar.set_loading(False)

        except Exception as e:
            log(f"_load_group_stats: {e}")
            self._top_bar.set_loading(False)

    def _load_global_history(self, mode: str):
        self._top_bar.set_loading(True, "Événements...")
        conn = db.server_conn
        if not conn or not self._time_manager.term_id:
            self._top_bar.set_loading(False)
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
                    if et.lower() not in ('absence', 'exit', 'arrival', 'departure', 'return', 'late', 'justified'):
                        self._history_filter_type.addItem(et)
                self._history_filter_type.setCurrentIndex(-1)
                self._history_filter_type.lineEdit().setText("")

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
            date_from, date_to = self._time_manager.period_dates()

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
            self._top_bar.set_loading(False)

        except Exception as e:
            log(f"_load_global_history: {e}")
            self._top_bar.set_loading(False)

    # ---- Mode classe -------------------------------------------------------

    def _show_class_mode(self, class_id: int):
        self._content_stack.setCurrentIndex(1)
        self._class_stack.setCurrentIndex(0)
        self._top_bar.show_period_row(False)

        self._cards_title.setText(f"<b>Élèves de {self._current_class_label}</b>")
        self._load_students(class_id)
        self._selected_student_id = 0

    def _load_students(self, class_id: int):
        self._top_bar.set_loading(True, "Élèves...")
        conn = db.server_conn
        if not conn or not self._time_manager.term_id:
            self._top_bar.set_loading(False)
            return

        today = QDate.currentDate().toString('yyyy-MM-dd')

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
                    """, ('exit', 'Sortie%', '%Fuite%', 'absence', 'Suivi > Absence%', today, today))
                    for sid, exit_count, presence in cur.fetchall():
                        event_stats[sid] = {'exit': exit_count, 'presence': presence}
                except Exception:
                    pass

            # Vider les cartes existantes
            for i in reversed(range(self._cards_layout.count())):
                w = self._cards_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()

            # Grille multi-colonnes avec scroll vertical
            cfg = CARD_THEMES.get(self._card_theme)
            card_w = cfg.card_w + cfg.margin * 2
            avail_w = self._cards_scroll.viewport().width()
            spacing = self._cards_layout.spacing()
            cols = max(1, (avail_w + spacing) // (card_w + spacing)) if avail_w > 100 else 2
            for idx, s in enumerate(self._students):
                sid = s['id']
                card = StudentCard(sid, s['last_name'], s['first_name'], cfg=cfg)
                stats = event_stats.get(sid, {'exit': 0, 'presence': 'Présent'})
                card.set_exit_count(stats['exit'])
                is_absent = stats['presence'] == 'Absent'
                color = theme_manager.palette.error if is_absent else theme_manager.palette.success
                card.set_status(stats['presence'], color)
                card.set_absent(is_absent)
                card.clicked.connect(self._on_student_selected)
                self._cards_layout.addWidget(card, idx // cols, idx % cols, Qt.AlignCenter)
            self._top_bar.set_loading(False)

        except Exception as e:
            log(f"_load_students: {e}")
            self._top_bar.set_loading(False)

    def _on_student_selected(self, student_id: int):
        self._selected_student_id = student_id
        self._top_bar.show_period_row(True)
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
        dlg = TimetableEditor(self._current_class_id, label, self._time_manager.term_id, self)
        dlg.exec()

    def _on_back_to_cards(self):
        self._sd_tabs.hide()
        self._sd_placeholder.show()
        self._class_stack.setCurrentIndex(0)
        self._selected_student_id = 0
        self._top_bar.show_period_row(False)

    def _on_card_theme(self, key: str):
        self._card_theme = key
        if self._current_class_id:
            self._load_students(self._current_class_id)

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
            self._top_bar.set_loading(True, "Enregistrement...")
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
                self._top_bar.set_loading(False)
            except Exception as e:
                log(f"_on_add_event insert: {e}")
                self._top_bar.set_loading(False)
                conn.rollback()
                QMessageBox.critical(self, "Erreur", f"Échec de l'enregistrement : {e}")
                return
            self._load_student_detail(sid)

    def _load_student_detail(self, student_id: int):
        self._top_bar.set_loading(True, "Détail élève...")
        conn = db.server_conn
        if not conn or not self._current_class_id:
            self._top_bar.set_loading(False)
            return

        p = theme_manager.palette
        date_from, date_to = self._time_manager.period_dates()

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
                f"{last_name.upper()} {first_name}")
            self._sd_contact_labels['email'].setText(
                email or '—')
            self._sd_contact_labels['email_perso'].setText(
                email_perso or '—')
            self._sd_contact_labels['tel_maison'].setText(
                tel_maison or '—')
            self._sd_contact_labels['tel_portable'].setText(
                tel_portable or '—')
            self._sd_contact_labels['date_entree'].setText(
                date_entree.strftime('%d/%m/%Y') if date_entree else '—')

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
            self._top_bar.set_loading(False)

        except Exception as e:
            log(f"_load_student_detail: {e}")
            self._top_bar.set_loading(False)

    # ---- Utilitaires -------------------------------------------------------

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
        self._top_bar.update_network()
        if self._current_group_mode == 'class':
            if self._selected_student_id:
                trace(f"refresh_all: reload student detail {self._selected_student_id}")
                self._load_student_detail(self._selected_student_id)
            else:
                trace(f"refresh_all: show class mode {self._current_class_id}")
                self._show_class_mode(self._current_class_id)
        elif self._current_group_mode:
            trace(f"refresh_all: show group mode {self._current_group_mode}")
            self._show_group_mode(self._current_group_mode)

    def _refresh_timer(self):
        self._top_bar.update_network()
        QTimer.singleShot(30000, self._refresh_timer)

    def resizeEvent(self, event):
        super().resizeEvent(event)
