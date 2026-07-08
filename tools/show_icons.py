"""Aperçu de toutes les icônes Material Design 3 disponibles."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "LarcCommon"))

from larccommon.icons import icon as md3_icon
from larccommon.theme import theme_manager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget


def main():
    app = QApplication(sys.argv)
    p = theme_manager.palette

    scroll = QScrollArea()
    scroll.setWindowTitle("Icônes Material Design 3 — LarcCommon")
    scroll.setMinimumSize(700, 500)
    scroll.setStyleSheet(f"background: {p.background};")

    container = QWidget()
    grid = QGridLayout(container)

    names = [
        ("light_mode", "Thème clair"),
        ("dark_mode", "Thème sombre"),
        ("contrast", "Contraste"),
        ("tonality", "Sobre"),
        ("refresh", "Rafraîchir"),
        ("add", "Ajouter"),
        ("arrow_back", "Retour"),
        ("close", "Fermer"),
        ("check", "Valider"),
        ("save", "Enregistrer"),
        ("delete", "Supprimer"),
        ("edit", "Éditer"),
        ("person", "Profil"),
        ("settings", "Paramètres"),
        ("menu", "Menu"),
        ("event", "Événement"),
        ("timer", "Minuteur"),
        ("calendar_today", "Calendrier"),
        ("schedule", "Horaire"),
        ("cloud", "Cloud"),
        ("wifi", "WiFi"),
        ("wifi_off", "WiFi off"),
        ("warning", "Alerte"),
        ("school", "École"),
        ("home", "Accueil"),
        ("search", "Rechercher"),
        ("logout", "Déconnexion"),
        ("filter_list", "Filtrer"),
        ("visibility", "Voir"),
        ("location_on", "Localisation"),
        ("subject", "Matière"),
        ("description", "Description"),
        ("bolt", "Éclair"),
    ]

    for idx, (name, label) in enumerate(names):
        cell = QWidget()
        cl = QVBoxLayout(cell)
        cl.setContentsMargins(6, 6, 6, 6)
        cl.setSpacing(6)
        cl.setAlignment(Qt.AlignCenter)

        ic_lbl = QLabel()
        ic = md3_icon(name, color=p.primary, size=32)
        ic_lbl.setPixmap(ic.pixmap(32, 32))
        ic_lbl.setAlignment(Qt.AlignCenter)
        ic_lbl.setFixedSize(48, 48)
        ic_lbl.setStyleSheet(f"background: {p.surface_variant}; border-radius: 8px;")

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {p.text_strong}; font-size: 11px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)

        cl.addWidget(ic_lbl)
        cl.addWidget(lbl)

        row = idx // 4
        col = idx % 4
        grid.addWidget(cell, row, col)

    scroll.setWidget(container)
    scroll.setWidgetResizable(True)
    scroll.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
