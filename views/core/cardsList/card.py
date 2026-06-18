from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.photos import get_photo_path
from .avatar import make_avatar
from .config import DEFAULT_CONFIG


class StudentCard(QFrame):
    clicked = Signal(int)

    def __init__(self, student_id: int, last_name: str, first_name: str, cfg=None):
        super().__init__()
        cfg = cfg or DEFAULT_CONFIG
        self._sid = student_id
        self._last_name = last_name
        self._first_name = first_name
        self.setFrameShape(QFrame.StyledPanel)
        self._build(cfg)
        self.setStyleSheet(self._default_style)
        self.setFixedSize(cfg.card_w, cfg.card_h)
        self.setCursor(Qt.PointingHandCursor)

    def _build(self, cfg):
        self._default_style = (
            f"StudentCard {{"
            f"  background: {theme_manager.palette.surface};"
            f"  border: 1px solid {theme_manager.palette.outline_variant};"
            f"  border-radius: {cfg.border_radius}px; padding: {cfg.padding}px;"
            f"}}"
            f"StudentCard:hover {{"
            f"  background: {theme_manager.palette.surface_variant};"
            f"  border-color: {theme_manager.palette.outline};"
            f"}}"
        )
        layout = QVBoxLayout()
        layout.setSpacing(cfg.spacing)
        layout.setContentsMargins(cfg.margin, cfg.margin, cfg.margin, cfg.margin)

        self._name_label = QLabel()
        self._name_label.setTextFormat(Qt.RichText)
        self._name_label.setAlignment(Qt.AlignCenter)
        fs = cfg.font_name
        self._name_label.setText(
            f"<b style='font-size:{theme_manager.font_size(fs)}px'>{self._last_name}</b><br>"
            f"<span style='font-size:{theme_manager.font_size(fs)}px; color:{theme_manager.palette.text_soft}'>{self._first_name}</span>"
        )

        self._photo_badge = QFrame()
        self._photo_badge.setFixedSize(cfg.badge_size, cfg.badge_size)
        self._photo_badge.setStyleSheet(
            f"background: {theme_manager.palette.primary_container}; border-radius: {cfg.border_radius}px;"
        )
        badge_layout = QVBoxLayout(self._photo_badge)
        badge_layout.setAlignment(Qt.AlignCenter)
        badge_layout.setContentsMargins(0, 0, 0, 0)

        self._photo = QLabel()
        self._photo.setFixedSize(cfg.photo_size, cfg.photo_size)
        self._photo.setAlignment(Qt.AlignCenter)

        pix = QPixmap(get_photo_path(self._sid))
        if pix.isNull() or pix.size().isNull():
            pix = make_avatar(self._last_name, self._first_name, cfg.photo_size, cfg.avatar_font)
        else:
            pix = pix.scaled(cfg.photo_size, cfg.photo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._photo.setPixmap(pix)

        badge_layout.addWidget(self._photo)

        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(f"font-size: {theme_manager.font_size(cfg.font_status)}px; font-weight: bold;")

        self._exit_label = QLabel()
        self._exit_label.setAlignment(Qt.AlignCenter)
        self._exit_label.setStyleSheet(f"font-size: {theme_manager.font_size(cfg.font_exit)}px; color: {theme_manager.palette.text_disabled};")

        layout.addWidget(self._name_label)
        layout.addStretch()
        layout.addWidget(self._photo_badge, 0, Qt.AlignCenter)
        layout.addSpacing(cfg.spacing)
        layout.addWidget(self._status_label)
        layout.addWidget(self._exit_label)
        self.setLayout(layout)

    def mousePressEvent(self, event):
        self.clicked.emit(self._sid)
        super().mousePressEvent(event)

    def set_status(self, text: str, color: str):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(
            f"font-size: {theme_manager.font_size(13)}px; font-weight: bold; color: {color};")

    def set_exit_count(self, count: int):
        self._exit_label.setText(f"{count} sortie(s)" if count else '')

    def set_absent(self, absent: bool):
        p = theme_manager.palette
        if absent:
            self.setStyleSheet(
                f"StudentCard {{"
                f"  background: {p.error_container};"
                f"  border: 2px solid {p.error};"
                f"  border-radius: 8px; padding: 8px;"
                f"}}"
                f"StudentCard:hover {{"
                f"  background: #FFC9C0; border-color: {p.error};"
                f"}}")
        else:
            self.setStyleSheet(self._default_style)
