from larccommon.l10n import _
from phibuilder.widgets import M3Button, M3Frame, M3ScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from LarcSuperviseur.common.theme import theme_manager

SIDEBAR_W = 233
H_SECTION = 34
H_PROG = 21
H_CLASS = 34
H_ALL = 55
COL_W = 89
F_SECTION = 12
F_PROG = 10
F_CLASS = 10
F_ALL = 11


class Sidebar(M3ScrollArea):
    class_selected = Signal(int, str)
    all_selected = Signal()
    group_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._classes: list = []

        container = QWidget()
        self.setWidget(container)
        self.setWidgetResizable(True)
        self.setFrameShape(M3Frame.NoFrame)
        self.setFixedWidth(SIDEBAR_W)

        container.setObjectName("panel")
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(theme_manager.design.spacing)

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
        d = theme_manager.design

        prog_style = {
            "PEI": (p.primary, p.primary_container, p.on_primary),
            "MYP": (p.secondary, p.secondary_container, p.on_secondary),
            "DPFr": (p.error, p.error_container, p.on_error),
            "DPEn": (p.tertiary, p.tertiary_container, p.on_tertiary),
        }

        groups = {k: [] for k in ["PEI", "MYP", "DPEn", "DPFr"]}
        for cid, label, pid, sigle in self._classes:
            if sigle in groups:
                groups[sigle].append((cid, label))

        sections = [
            ("Collège", [("PEI", "PEI"), ("MYP", "MYP")]),
            ("Lycée", [("DP", "DPFr"), ("DPEn", "DPEn")]),
        ]

        for sec_name, columns in sections:
            sec_hdr = M3Button(sec_name)
            sec_hdr.setFixedHeight(H_SECTION)
            sec_hdr.setCursor(Qt.PointingHandCursor)
            sec_hdr.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {p.text_strong}; "
                f"border: none; border-bottom: 2px solid {p.outline_variant}; "
                f"font-weight: bold; font-size: {s(F_SECTION)}px; text-align: left; "
                f"padding: 3px 2px; }}"
                f"QPushButton:hover {{ color: {p.primary}; border-bottom: 2px solid {p.primary}; }}"
            )
            sec_hdr.clicked.connect(lambda checked, sn=sec_name: self._on_section_clicked(sn))
            layout.addWidget(sec_hdr)

            grd = QGridLayout()
            grd.setSpacing(d.spacing)

            for col_idx, (hdr_text, prog_key) in enumerate(columns):
                fg, bg, on_fg = prog_style[prog_key]
                items = groups.get(prog_key, [])

                col_hdr = M3Button(hdr_text)
                col_hdr.setFixedSize(COL_W, H_PROG)
                col_hdr.setCursor(Qt.PointingHandCursor)
                col_hdr.setStyleSheet(
                    f"QPushButton {{ background: {fg}; color: {on_fg}; border: none; "
                    f"border-radius: {d.radius}px; font-weight: bold; "
                    f"font-size: {s(F_PROG)}px; padding: 3px; }}"
                    f"QPushButton:hover {{ background: {bg}; color: {fg}; }}"
                )
                col_hdr.clicked.connect(lambda checked, pk=prog_key: self._on_prog_clicked(pk))
                grd.addWidget(col_hdr, 0, col_idx)

                for i, (cid, label) in enumerate(items):
                    btn = M3Button(label)
                    btn.setFixedSize(COL_W, H_CLASS)
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.setCheckable(True)
                    btn.setStyleSheet(
                        f"QPushButton {{ background: {bg}; color: {fg}; border: none; "
                        f"border-radius: {d.radius}px; font-size: {s(F_CLASS)}px; padding: 2px 4px; }}"
                        f"QPushButton:hover {{ background: {fg}; color: {bg}; }}"
                        f"QPushButton:checked {{ background: {fg}; color: {bg}; "
                        f"border: 2px solid {fg}; }}"
                    )
                    btn.clicked.connect(
                        lambda checked, c=cid, l=label, b=btn: self._on_class_clicked(c, l, b)
                    )
                    grd.addWidget(btn, i + 1, col_idx)

            layout.addLayout(grd)
            layout.addSpacing(d.spacing)

        self._all_btn = M3Button(_("sidebar.all_classes"))
        self._all_btn.setFixedHeight(H_ALL)
        self._all_btn.setCursor(Qt.PointingHandCursor)
        self._all_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: {d.radius}px; font-weight: bold; "
            f"font-size: {s(F_ALL)}px; padding: 8px; }}"
            f"QPushButton:hover {{ background: {p.active}; }}"
        )
        self._all_btn.clicked.connect(self._on_all_clicked)
        layout.addWidget(self._all_btn)
        layout.addStretch()

    def _on_section_clicked(self, section: str):
        mode_map = {"Collège": "grp_college", "Lycée": "grp_lycee"}
        self._clear_selection()
        self.group_selected.emit(mode_map[section])

    def _on_prog_clicked(self, prog: str):
        self._clear_selection()
        self.group_selected.emit(f"grp_{prog.lower()}")

    def _on_class_clicked(self, class_id: int, label: str, btn: M3Button):
        self._clear_selection()
        btn.setChecked(True)
        self.class_selected.emit(class_id, label)

    def _on_all_clicked(self):
        self._clear_selection()
        self.all_selected.emit()

    def _clear_selection(self):
        for w in self.findChildren(M3Button):
            if w.isCheckable():
                w.setChecked(False)
