from larccommon.l10n import _
from phibuilder.widgets import M3Label, M3ScrollArea
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from LarcSuperviseur.views.core.cardsList import DEFAULT_CONFIG, StudentCard
from LarcSuperviseur.views.core.cardsList.grid import fill_cards_grid
from LarcSuperviseur.views.core.data_loader import DataLoader


class ClassPanel(QWidget):
    """Student cards grid for a selected class."""

    student_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loader = DataLoader()
        self._students = []
        self._class_id = 0
        self._init_ui()

    def _init_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

        self._loading = M3Label(_("class_panel.loading"))
        self._loading.setAlignment(Qt.AlignCenter)
        self._loading.setVisible(False)
        self._main_layout.addWidget(self._loading)

        self._scroll = M3ScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(13, 13, 13, 13)

        self._scroll.setWidget(self._grid_widget)
        self._main_layout.addWidget(self._scroll)

    def load(self, class_id: int, date_from: str = "", date_to: str = ""):
        self._class_id = class_id
        self._loading.setVisible(True)

        if not date_from or not date_to:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            date_from = date_from or today
            date_to = date_to or today

        students = self._loader.get_students(class_id)
        self._students = students

        student_ids = [s["id"] for s in students]
        event_stats = self._loader.get_student_event_stats(student_ids, date_from, date_to)

        fill_cards_grid(self._grid_layout, self._scroll, students, event_stats, self._on_card_click)

        self._loading.setVisible(False)

    def _on_card_click(self, student_id: int):
        self.student_selected.emit(student_id)

    def reflow(self):
        avail_w = self._scroll.viewport().width()
        cfg = DEFAULT_CONFIG
        card_w = cfg.card_w
        spacing = cfg.spacing
        cols = max(1, (avail_w + spacing) // (card_w + spacing)) if avail_w > 100 else 3
        cards = []
        for i in reversed(range(self._grid_layout.count())):
            w = self._grid_layout.itemAt(i).widget()
            if w:
                self._grid_layout.removeWidget(w)
                if isinstance(w, StudentCard):
                    cards.insert(0, w)
                else:
                    w.deleteLater()
        for idx, card in enumerate(cards):
            self._grid_layout.addWidget(card, idx // cols, idx % cols, Qt.AlignCenter)
        remaining = len(cards) % cols
        if remaining:
            for _ in range(cols - remaining):
                sp = QWidget()
                sp.setFixedSize(cfg.card_w, cfg.card_h)
                self._grid_layout.addWidget(
                    sp, len(cards) // cols, cols - remaining + _, Qt.AlignCenter
                )

    def show_student_highlight(self, student_id: int):
        pass
