"""Démo : login 100% Material Design 3 sans QSS — thème=phi uniquement."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "LarcCommon"))

from larccommon.theme import theme_manager
from phibuilder.phi.scale import SpacingToken
from phibuilder.widgets import M3Button, M3Card, M3Label, M3TextField
from phibuilder.widgets.button import ButtonVariant
from phibuilder.widgets.card import CardVariant
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

app = QApplication(sys.argv)
phi = theme_manager.phi_theme
c = phi.colors
sp = phi.spacing.spacing

win = QWidget()
win.setWindowTitle("Démo M3 sans QSS")
W, H = 420, int(420 * 1.618)
win.setFixedSize(W, H)
win.setStyleSheet(f"QWidget {{ background: {c.background}; }}")

outer = QVBoxLayout(win)
outer.setContentsMargins(
    sp(SpacingToken.XXXL), sp(SpacingToken.XXL), sp(SpacingToken.XXXL), sp(SpacingToken.XXL)
)
outer.setSpacing(sp(SpacingToken.MD))
outer.setAlignment(Qt.AlignCenter)

# Logo
logo_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "LarcSuperviseur", "img", "logoAEC.png"
)
if os.path.exists(logo_path):
    lbl = M3Label(theme=phi)
    lbl.setPixmap(
        QPixmap(logo_path).scaledToHeight(theme_manager.image.logo, Qt.SmoothTransformation)
    )
    lbl.setAlignment(Qt.AlignCenter)
    outer.addWidget(lbl)

# Titre
outer.addWidget(M3Label("LarcDesign M3", theme=phi, style="headline_small"))
outer.addWidget(
    M3Label("Langues · Thèmes · Rôles · Logs · Types · Lieux", theme=phi, style="body_medium")
)

# Card login
card = M3Card(theme=phi, variant=CardVariant.ELEVATED)
cl = card.content_layout()
cl.setSpacing(sp(SpacingToken.MD))
cl.addWidget(M3Label("Connexion", theme=phi, style="title_medium"))
cl.addWidget(M3TextField(placeholder="Email", theme=phi))
pwd = M3TextField(placeholder="Mot de passe", theme=phi)
pwd.setEchoMode(M3TextField.Password)
cl.addWidget(pwd)
btn = M3Button("Connexion Intranet", theme=phi, variant=ButtonVariant.FILLED)
btn.setMinimumHeight(sp(SpacingToken.XL) * 2)
cl.addWidget(btn)
outer.addWidget(card)

win.show()
app.exec()
