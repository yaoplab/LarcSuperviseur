from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QMenu, QButtonGroup,
)
from PySide6.QtCore import Qt, QTimer, QCoreApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon

from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.network import detect_network
from larccommon.l10n import _


class TopBar(QFrame):
    """UI bandeau 2 lignes : date/heure/terme, réseau, thème, boutons période."""

    def __init__(self, on_period_click, on_theme_change, on_refresh):
        super().__init__()
        self.setObjectName("top_bar")
        self._on_period_click = on_period_click
        self._on_theme_change = on_theme_change
        self._on_refresh = on_refresh

        self._unit_periods: list[dict] = []
        self._unit_keys: list[str] = []
        self._unit_buttons: list[QPushButton] = []

        self._build_ui()
        self._start_clock()

    # ── Construction UI ────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 6, 10, 6)
        outer.setSpacing(4)
        p = theme_manager.palette

        # Ligne 1 -------------------------------------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self._date_label = QLabel()
        self._date_label.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {p.text_strong};")
        self._time_label = QLabel()
        self._time_label.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {p.primary};")
        self._term_label = QLabel()
        self._term_label.setStyleSheet(f"font-size: 13px; color: {p.text_soft}; padding-left: 13px;")
        self._update_datetime()
        row1.addWidget(self._date_label)
        row1.addWidget(self._time_label)
        row1.addWidget(self._term_label)
        row1.addStretch()

        self._network_label = QLabel()
        self._update_network_label()
        row1.addWidget(self._network_label)

        self._theme_btn = QPushButton("🎨")
        self._theme_btn.setObjectName("theme_btn")
        self._theme_btn.setFixedSize(34, 34)
        self._theme_menu = QMenu()
        for key, label in theme_manager.names():
            a = self._theme_menu.addAction(label)
            a.setData(key)
            pal = theme_manager.get_palette(key)
            if pal:
                pm = QPixmap(16, 16)
                pm.fill(QColor(pal.primary))
                a.setIcon(QIcon(pm))
        self._theme_menu.triggered.connect(self._on_theme_triggered)
        self._theme_btn.setMenu(self._theme_menu)
        row1.addWidget(self._theme_btn)

        # Bouton profil (initiales)
        from LarcSuperviseur.common.session import session
        initials = ''.join(w[0].upper() for w in session.full_name.split() if w)[:2] or '?'
        self._profile_btn = QPushButton(initials)
        self._profile_btn.setFixedSize(34, 34)
        self._profile_btn.setCursor(Qt.PointingHandCursor)
        p = theme_manager.palette
        self._profile_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"font-weight: bold; font-size: 13px; border: none; border-radius: 17px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}"
        )
        self._profile_menu = QMenu(self)
        self._profile_menu.addAction("Pr\u00e9f\u00e9rences")
        self._profile_menu.addSeparator()
        logout_action = self._profile_menu.addAction("D\u00e9connexion")
        logout_action.triggered.connect(self._on_logout)
        self._profile_btn.setMenu(self._profile_menu)
        row1.addWidget(self._profile_btn)

        self._loading_label = QLabel()
        self._loading_label.setStyleSheet(f"font-size: 13px; color: {p.primary}; font-weight: bold;")
        self._loading_label.setVisible(False)
        row1.addWidget(self._loading_label)

        # Ligne 2 : 5 fixes + slot unités + espacement + refresh ---------
        self._period_row = QHBoxLayout()
        self._period_row.setSpacing(6)
        self._period_group = QButtonGroup(self)
        self._period_group.setExclusive(True)
        self._period_keys: list[str] = []

        fixed = [(_('topbar.period.day'), 'day'), (_('topbar.period.week'), 'week'), (_('topbar.period.month'), 'month'),
                 (_('topbar.period.term'), 'term'), ("Année", 'year')]
        for label, key in fixed:
            btn = self._make_period_btn(label)
            btn.clicked.connect(lambda checked, k=key: self._on_period_click(k))
            self._period_group.addButton(btn)
            self._period_keys.append(key)
            self._period_row.addWidget(btn)
        if self._period_keys:
            self._period_group.buttons()[0].setChecked(True)

        # Slot pour les unités (inséré entre les fixes et le spacer)
        self._unit_slot = QHBoxLayout()
        self._unit_slot.setSpacing(6)
        self._period_row.addLayout(self._unit_slot)

        self._period_row.addSpacing(13)
        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setFixedSize(34, 34)
        self._refresh_btn.clicked.connect(self._on_refresh)
        self._period_row.addWidget(self._refresh_btn)
        self._period_row.addStretch()

        outer.addLayout(row1)
        self._period_container = QFrame()
        self._period_container.setLayout(self._period_row)
        outer.addWidget(self._period_container)

    def _start_clock(self):
        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_datetime)
        self._clock_timer.start(10000)

    # ── Boutons période ────────────────────────────────────────────────

    def _make_period_btn(self, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("period_btn")
        btn.setCheckable(True)
        btn.setFixedSize(89, 34)
        return btn

    def set_unit_periods(self, periods: list[dict]):
        self._unit_periods = periods
        # Vider le slot unités
        for btn in self._unit_buttons:
            self._period_group.removeButton(btn)
            self._unit_slot.removeWidget(btn)
            btn.deleteLater()
        self._unit_buttons.clear()
        self._unit_keys.clear()
        # Re-remplir
        for up in self._unit_periods:
            key = f"unit_{up['id']}"
            btn = self._make_period_btn(up['label'])
            btn.clicked.connect(lambda checked, k=key: self._on_period_click(k))
            self._period_group.addButton(btn)
            self._unit_buttons.append(btn)
            self._unit_keys.append(key)
            self._unit_slot.addWidget(btn)

    def show_period_row(self, visible: bool):
        self._period_container.setVisible(visible)

    # ── Mise à jour des labels ─────────────────────────────────────────

    def _update_datetime(self):
        from datetime import datetime
        now = datetime.now()
        self._date_label.setText(now.strftime("%A %d %B %Y") + '  ')
        self._time_label.setText(now.strftime("%H:%M") + '  ')
        t = session.term_label
        self._term_label.setText(f"— {t}" if t else '')

    def update_network(self):
        self._update_network_label()

    def _update_network_label(self):
        intranet_ok, internet_ok = detect_network()
        p = theme_manager.palette
        s = theme_manager.font_size
        if intranet_ok:
            self._network_label.setText("Intranet ●")
            self._network_label.setStyleSheet(
                f"color: {p.success}; font-weight: bold; font-size: {s(12)}px;")
        elif internet_ok:
            self._network_label.setText("Cloud ●")
            self._network_label.setStyleSheet(
                f"color: {p.primary}; font-weight: bold; font-size: {s(12)}px;")
        else:
            self._network_label.setText(_('topbar.network.offline'))
            self._network_label.setStyleSheet(
                f"color: {p.text_disabled}; font-size: {s(12)}px;")

    def set_loading(self, busy: bool, msg: str = "Chargement..."):
        self._loading_label.setText("⟳ " + msg if busy else "")
        self._loading_label.setVisible(busy)
        QCoreApplication.processEvents()

    # ── Thème ──────────────────────────────────────────────────────────

    def _on_theme_triggered(self, action):
        key = action.data()
        if key:
            self._on_theme_change(key)

    def _on_logout(self):
        QCoreApplication.quit()

    # ── Réapplication du style après changement de thème ────────────────

    def restyle(self):
        p = theme_manager.palette
        self._profile_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"font-weight: bold; font-size: 13px; border: none; border-radius: 17px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}"
        )
        self._date_label.setStyleSheet(
            f"font-size: 21px; font-weight: bold; color: {p.text_strong};")
        self._time_label.setStyleSheet(
            f"font-size: 21px; font-weight: bold; color: {p.primary};")
        self._term_label.setStyleSheet(
            f"font-size: 13px; color: {p.text_soft}; padding-left: 13px;")
        self._loading_label.setStyleSheet(
            f"font-size: 13px; color: {p.primary}; font-weight: bold;")
        self._update_network_label()
