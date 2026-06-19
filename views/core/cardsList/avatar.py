from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtCore import Qt


_COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']


def make_avatar(last_name: str, first_name: str, size: int = 89, font_px: int = 34) -> QPixmap:
    initials = (last_name[:1] + first_name[:1]).upper() or '?'
    color = _COLORS[hash(last_name + first_name) % len(_COLORS)]
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(0, 0, size, size)
    p.setPen(QColor('#fff'))
    font = p.font()
    font.setPixelSize(font_px)
    font.setBold(True)
    p.setFont(font)
    p.drawText(px.rect(), Qt.AlignCenter, initials)
    p.end()
    return px
