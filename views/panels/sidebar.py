from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QGridLayout, QFrame
from PySide6.QtCore import Signal, Qt
import re

from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.logger import log


class Sidebar(QScrollArea):
    """Left sidebar with programs and classes navigation."""

    class_selected = Signal(int, str)
    all_selected = Signal()
    group_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_btn: QPushButton | None = None
        self._classes: list = []

        container = QWidget()
        self.setWidget(container)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        container.setObjectName("panel")
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._layout.setSpacing(2)

    def load_data(self):
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT c.id, c.label, l.fk_program_id, p.sigle
                FROM larcauth_classroom c
                JOIN larcauth_level l ON l.id = c.fk_level_id
                JOIN larcauth_program p ON p.id = l.fk_program_id
                WHERE c.enabled = TRUE AND p.sigle IN ('PEI', 'MYP', 'DPEn', 'DPFr')
                ORDER BY p.sigle, c.label
            """)
            self._classes = cur.fetchall()
            self._build_sections()
        except Exception as e:
            log(f"Sidebar.load_data: {e}")

    def _build_sections(self):
        layout = self._layout
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

        sections = [
            ('Collège', [('PEI', 'PEI'), ('MYP', 'MYP')]),
            ('Lycée',   [('DP', 'DPFr'), ('DPEn', 'DPEn')]),
        ]

        for sec_name, columns in sections:
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

        self._all_btn = _make_btn(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; font-weight: bold; font-size: {s(11)}px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}",
            min_h=36
        )
        self._all_btn.setText("\U0001f4ca Toutes les classes")
        self._all_btn.clicked.connect(self._on_all_clicked)
        layout.addWidget(self._all_btn)
        layout.addStretch()

    def _on_section_clicked(self, section: str):
        mode_map = {'Collège': 'grp_college', 'Lycée': 'grp_lycee'}
        self._select_btn(None)
        self.group_selected.emit(mode_map[section])

    def _on_prog_clicked(self, prog: str):
        self._select_btn(None)
        self.group_selected.emit(f'grp_{prog.lower()}')

    def _on_class_clicked(self, class_id: int, label: str, btn: QPushButton | None = None):
        self._select_btn(btn)
        self.class_selected.emit(class_id, label)

    def _on_all_clicked(self):
        self._select_btn(None)
        self.all_selected.emit()

    def _select_btn(self, btn: QPushButton | None):
        if self._selected_btn:
            old_style = self._selected_btn.property('_normal_style') or ''
            self._selected_btn.setStyleSheet(old_style)
        self._selected_btn = btn
        if btn:
            btn.setProperty('_normal_style', btn.styleSheet())
            ss = btn.styleSheet()
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
