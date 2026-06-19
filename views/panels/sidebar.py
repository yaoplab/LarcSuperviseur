from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QGridLayout, QFrame
from PySide6.QtCore import Signal, Qt

from LarcSuperviseur.common.theme import theme_manager

# Fibonacci : {8, 13, 21, 34, 55, 89, 144, 233}
FIB = {
    'w_sidebar': 233,
    'h_section': 34,
    'h_prog': 21,
    'h_class': 34,
    'h_all': 55,
    'col_w': 89,
    's': 8,
    'p': 13,
    'r': 8,
    'f_section': 13,
    'f_prog': 8,
    'f_class': 13,
    'f_all': 21,
}


class Sidebar(QScrollArea):
    class_selected = Signal(int, str)
    all_selected = Signal()
    group_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._classes: list = []

        container = QWidget()
        self.setWidget(container)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setFixedWidth(FIB['w_sidebar'])

        container.setObjectName("panel")
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(FIB['p'], FIB['p'], FIB['p'], FIB['p'])
        self._layout.setSpacing(FIB['s'])

    def load_data(self):
        from LarcSuperviseur.views.core.data_loader import DataLoader
        self._classes = DataLoader().get_classes()
        self._build_sections()

    def _build_sections(self):
        layout = self._layout
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        p = theme_manager.palette
        s = theme_manager.font_size
        prog_style = {
            'PEI':  (p.primary, p.primary_container),
            'MYP':  (p.secondary, p.secondary_container),
            'DPFr': (p.error, p.error_container),
            'DPEn': (p.tertiary, p.tertiary_container),
        }

        groups = {k: [] for k in ['PEI', 'MYP', 'DPEn', 'DPFr']}
        for cid, label, pid, sigle in self._classes:
            if sigle in groups:
                groups[sigle].append((cid, label))

        sections = [
            ('Collège', [('PEI', 'PEI'), ('MYP', 'MYP')]),
            ('Lycée',   [('DP', 'DPFr'), ('DPEn', 'DPEn')]),
        ]

        for sec_name, columns in sections:
            sec_hdr = QPushButton(sec_name)
            sec_hdr.setFixedHeight(FIB['h_section'])
            sec_hdr.setCursor(Qt.PointingHandCursor)
            sec_hdr.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {p.text_strong}; "
                f"border: none; border-bottom: 2px solid {p.outline_variant}; "
                f"font-weight: bold; font-size: {s(FIB['f_section'])}px; text-align: left; "
                f"padding: 0; }}"
                f"QPushButton:hover {{ color: {p.primary}; border-bottom: 2px solid {p.primary}; }}"
            )
            sec_hdr.clicked.connect(lambda checked, sn=sec_name: self._on_section_clicked(sn))
            layout.addWidget(sec_hdr)

            grd = QGridLayout()
            grd.setSpacing(FIB['s'])

            for col_idx, (hdr_text, prog_key) in enumerate(columns):
                fg, bg = prog_style[prog_key]
                items = groups.get(prog_key, [])

                col_hdr = QPushButton(hdr_text)
                col_hdr.setFixedSize(FIB['col_w'], FIB['h_prog'])
                col_hdr.setCursor(Qt.PointingHandCursor)
                col_hdr.setStyleSheet(
                    f"QPushButton {{ background: {fg}; color: {bg}; border: none; "
                    f"border-radius: {FIB['r']}px; font-weight: bold; "
                    f"font-size: {s(FIB['f_prog'])}px; padding: 0; }}"
                    f"QPushButton:hover {{ background: {bg}; color: {fg}; }}"
                )
                col_hdr.clicked.connect(lambda checked, pk=prog_key: self._on_prog_clicked(pk))
                grd.addWidget(col_hdr, 0, col_idx)

                for i, (cid, label) in enumerate(items):
                    btn = QPushButton(label)
                    btn.setFixedSize(FIB['col_w'], FIB['h_class'])
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.setCheckable(True)
                    btn.setStyleSheet(
                        f"QPushButton {{ background: {bg}; color: {fg}; border: none; "
                        f"border-radius: {FIB['r']}px; font-size: {s(FIB['f_class'])}px; }}"
                        f"QPushButton:hover {{ background: {fg}; color: {bg}; }}"
                        f"QPushButton:checked {{ background: {fg}; color: {bg}; "
                        f"border: 2px solid {fg}; }}"
                    )
                    btn.clicked.connect(lambda checked, c=cid, l=label, b=btn: self._on_class_clicked(c, l, b))
                    grd.addWidget(btn, i + 1, col_idx)

            layout.addLayout(grd)
            layout.addSpacing(FIB['s'])

        self._all_btn = QPushButton("Toutes les classes")
        self._all_btn.setFixedHeight(FIB['h_all'])
        self._all_btn.setCursor(Qt.PointingHandCursor)
        self._all_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: {FIB['r']}px; font-weight: bold; "
            f"font-size: {s(FIB['f_all'])}px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}"
        )
        self._all_btn.clicked.connect(self._on_all_clicked)
        layout.addWidget(self._all_btn)
        layout.addStretch()

    def _on_section_clicked(self, section: str):
        mode_map = {'Collège': 'grp_college', 'Lycée': 'grp_lycee'}
        self._clear_selection()
        self.group_selected.emit(mode_map[section])

    def _on_prog_clicked(self, prog: str):
        self._clear_selection()
        self.group_selected.emit(f'grp_{prog.lower()}')

    def _on_class_clicked(self, class_id: int, label: str, btn: QPushButton):
        self._clear_selection()
        btn.setChecked(True)
        self.class_selected.emit(class_id, label)

    def _on_all_clicked(self):
        self._clear_selection()
        self.all_selected.emit()

    def _clear_selection(self):
        for w in self.findChildren(QPushButton):
            if w.isCheckable():
                w.setChecked(False)
