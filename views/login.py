import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                               QPushButton, QLineEdit, QComboBox,
                               QMessageBox, QApplication)
from PySide6.QtCore import Qt
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session, UserRole, ConnMode
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.views.main_window import MainWindow
from LarcSuperviseur.common.network import detect_network
from common.auth import AuthManager


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LarcSuperviseur — Connexion")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("LarcSuperviseur")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)

        self._status = QLabel("Hors connexion")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet("color: #e67e22; font-size: 12px;")

        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Email")
        self._email_input.setFixedWidth(300)

        self._pwd_input = QLineEdit()
        self._pwd_input.setPlaceholderText("Mot de passe")
        self._pwd_input.setEchoMode(QLineEdit.Password)
        self._pwd_input.setFixedWidth(300)

        self._connect_btn = QPushButton("Connexion Intranet")
        self._connect_btn.clicked.connect(self._on_connect)
        self._connect_btn.setFixedWidth(200)

        layout.addWidget(title)
        layout.addWidget(self._status)
        layout.addSpacing(20)
        layout.addWidget(self._email_input, 0, Qt.AlignCenter)
        layout.addWidget(self._pwd_input, 0, Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self._connect_btn, 0, Qt.AlignCenter)

        self.setLayout(layout)
        self._update_network_status()

    def _update_network_status(self):
        intranet_ok, internet_ok = detect_network()
        if intranet_ok:
            self._status.setText("Connecté à l'Intranet ●")
            self._status.setStyleSheet("color: #27ae60; font-size: 12px;")
        elif internet_ok:
            self._status.setText("Connecté à Internet (lecture seule) ●")
            self._status.setStyleSheet("color: #2980b9; font-size: 12px;")
        else:
            self._status.setText("Hors connexion")
            self._status.setStyleSheet("color: #e67e22; font-size: 12px;")

    def _on_connect(self):
        email = self._email_input.text().strip()
        password = self._pwd_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Erreur", "Email et mot de passe requis.")
            return

        if not db.connect_intranet():
            QMessageBox.critical(self, "Erreur",
                "Impossible de se connecter à l'Intranet.\n"
                "Vérifiez votre connexion réseau.")
            return

        conn = db.server_conn
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, first_name, last_name, email, password, "
                "type_director, type_coordonator, type_supervisor "
                "FROM public.larcauth_aecuser WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            if row is None:
                QMessageBox.warning(self, "Erreur", "Utilisateur introuvable.")
                db.disconnect_all()
                return

            user_id, first_name, last_name, email, pwd_hash, is_dir, is_coord, is_sup = row

            # Vérifier le mot de passe
            if not AuthManager.verify_password(email, password):
                QMessageBox.warning(self, "Erreur", "Mot de passe incorrect.")
                db.disconnect_all()
                return

            # Déterminer le rôle
            if is_dir:
                role = UserRole.ADMIN
            elif is_coord:
                role = UserRole.COORD
            elif is_sup:
                role = UserRole.SUPERVISEUR
            else:
                QMessageBox.warning(self, "Accès refusé",
                    "Cette application est réservée aux superviseurs, "
                    "coordinateurs et administrateurs.")
                db.disconnect_all()
                return

            session.user_id = user_id
            session.email = email
            session.full_name = f"{first_name} {last_name}"
            session.role = role
            session.conn_mode = ConnMode.INTRANET
            session.is_authenticated = True

            log(f"Connexion réussie : {session.full_name} ({role.value})")
            self._open_main_window()

        except Exception as e:
            log(f"_on_connect: {e}")
            QMessageBox.critical(self, "Erreur", str(e))
            db.disconnect_all()

    def _open_main_window(self):
        self.main = MainWindow()
        self.main.resize(1200, 750)
        self.main.show()
        self.close()
