import os
import sys
import hashlib
from typing import Optional
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QMessageBox, QApplication, QTabWidget, QFormLayout,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session, UserRole, ConnMode
from LarcSuperviseur.common.logger import log
from LarcSuperviseur.common.network import detect_network
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.common.auth import OAuth2Manager
from LarcSuperviseur.common.app_config import app_config


class _Worker(QThread):
    done = Signal(object)

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self.finished.connect(self.deleteLater)

    def run(self):
        try:
            self.done.emit(self._fn(*self._args))
        except Exception as exc:
            self.done.emit((False, None, str(exc)))


class LoginWindow(QWidget):

    _login_attempts: dict[str, dict] = {}

    @classmethod
    def _check_rate_limit(cls, key: str) -> bool:
        now = time.time()
        entry = cls._login_attempts.get(key)
        if entry and entry['until'] > now:
            remaining = int(entry['until'] - now)
            raise RuntimeError(f"Trop de tentatives. Réessayez dans {remaining}s.")
        if entry and entry['until'] <= now:
            cls._login_attempts.pop(key, None)
        return True

    @classmethod
    def _record_failure(cls, key: str):
        entry = cls._login_attempts.setdefault(key, {'count': 0, 'until': 0})
        entry['count'] += 1
        if entry['count'] >= 5:
            entry['until'] = time.time() + 30

    def __init__(self):
        super().__init__()
        self._worker: Optional[_Worker] = None
        self.setWindowTitle("LarcSuperviseur — Connexion")

        db.connect_intranet()
        if not db.server_conn:
            db.connect_cloud()
        app_config.load()

        self._init_ui()

    def _style(self) -> str:
        p = theme_manager.palette
        d = theme_manager.design if hasattr(theme_manager, 'design') else None
        rd = 6
        return f"""
            QWidget#root {{ background: {p.background}; }}
            QTabWidget::pane {{
                border: 1px solid {p.outline_variant}; background: {p.surface};
                border-radius: {rd}px;
            }}
            QTabBar::tab          {{ padding: 6px 16px; font-size: 11px; }}
            QTabBar::tab:selected {{
                background: {p.surface}; border-bottom: 2px solid {p.primary};
                color: {p.text_strong}; font-weight: bold;
            }}
            QTabBar::tab:!selected {{ background: {p.surface_variant}; color: {p.text_soft}; }}
            QLineEdit {{
                padding: 7px 10px; border: 1px solid {p.outline_variant};
                border-radius: {rd}px; font-size: 12px; background: {p.surface};
                color: {p.text_strong};
            }}
            QLineEdit:focus {{ border-color: {p.primary}; }}
            QPushButton {{
                padding: 9px 20px; border: none; border-radius: {rd}px;
                font-size: 12px; font-weight: bold; color: white;
            }}
            QPushButton#btnIntra  {{ background: {p.primary}; }}
            QPushButton#btnIntra:hover  {{ background: {p.active}; }}
            QPushButton#btnIntra:disabled  {{ background: {p.inactive}; }}
            QPushButton#btnGoogle {{ background: #DB4437; }}
            QPushButton#btnGoogle:hover {{ background: #C53929; }}
            QPushButton#btnGoogle:disabled {{ background: {p.inactive}; }}
            QPushButton#btnCloud {{ background: {p.primary}; }}
            QPushButton#btnCloud:hover {{ background: {p.active}; }}
            QLabel#errLabel {{ color: {p.error}; font-size: 11px; }}
            QLabel#hdrTitle {{ color: {p.text_strong}; font-size: 22px; font-weight: bold; }}
            QLabel#hdrSub   {{ color: {p.text_soft}; font-size: 11px; }}
            QLabel#infoLbl  {{ color: {p.text_disabled}; font-size: 11px; }}
        """

    def _init_ui(self):
        self.setStyleSheet(self._style())
        self.setMinimumSize(480, 420)
        self.setMaximumSize(560, 560)

        outer = QVBoxLayout()
        outer.setContentsMargins(40, 30, 40, 20)

        title = QLabel("LarcSuperviseur")
        title.setObjectName("hdrTitle")
        title.setAlignment(Qt.AlignCenter)
        outer.addWidget(title)

        sub = QLabel("Supervision de la vie scolaire")
        sub.setObjectName("hdrSub")
        sub.setAlignment(Qt.AlignCenter)
        outer.addWidget(sub)
        outer.addSpacing(10)

        self._net_label = QLabel()
        self._net_label.setAlignment(Qt.AlignCenter)
        self._net_label.setObjectName("infoLbl")
        outer.addWidget(self._net_label)
        outer.addSpacing(10)

        tabs = QTabWidget()
        tabs.addTab(self._tab_intranet(), "Intranet")
        tabs.addTab(self._tab_cloud(), "Cloud")
        outer.addWidget(tabs, 1)

        self._err_label = QLabel()
        self._err_label.setObjectName("errLabel")
        self._err_label.setAlignment(Qt.AlignCenter)
        self._err_label.setWordWrap(True)
        outer.addWidget(self._err_label)

        self._status_label = QLabel()
        self._status_label.setObjectName("infoLbl")
        outer.addWidget(self._status_label)

        self.setLayout(outer)
        self._update_network_status()

        self._net_timer = QTimer(self)
        self._net_timer.setInterval(30000)
        self._net_timer.timeout.connect(self._update_network_status)
        self._net_timer.start()

    def _tab_intranet(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        form = QFormLayout()
        form.setSpacing(8)

        email = QLineEdit()
        email.setPlaceholderText("prenom.nom@votreedu.com")
        self._edt_i_email = email
        pwd = QLineEdit()
        pwd.setEchoMode(QLineEdit.Password)
        pwd.setPlaceholderText("Mot de passe")
        pwd.returnPressed.connect(self._on_intranet)
        self._edt_i_pwd = pwd

        form.addRow("Email :", email)
        form.addRow("Mot de passe :", pwd)
        layout.addLayout(form)

        btn = QPushButton("Connexion Intranet")
        btn.setObjectName("btnIntra")
        btn.setMinimumHeight(44)
        btn.clicked.connect(self._on_intranet)
        layout.addWidget(btn)

        layout.addSpacing(8)
        info = QLabel("Authentification via le serveur interne.")
        info.setObjectName("infoLbl")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        return w

    def _tab_cloud(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        info = QLabel("Connectez-vous avec votre compte\nGoogle @arc-en-ciel.org")
        info.setObjectName("infoLbl")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        layout.addSpacing(10)

        btn = QPushButton("Connexion Google")
        btn.setObjectName("btnGoogle")
        btn.setMinimumHeight(44)
        btn.clicked.connect(self._on_cloud)
        layout.addWidget(btn)

        layout.addSpacing(8)
        info2 = QLabel("Authentification OAuth2 via Supabase.")
        info2.setObjectName("infoLbl")
        info2.setAlignment(Qt.AlignCenter)
        layout.addWidget(info2)
        return w

    def _on_intranet(self):
        email = self._edt_i_email.text().strip()
        password = self._edt_i_pwd.text()
        if not email or not password:
            self._show_error("Email et mot de passe requis.")
            return
        try:
            self._check_rate_limit(email.lower())
        except RuntimeError as e:
            self._show_error(str(e))
            return
        self._hide_error()
        self._set_busy(True)

        if not db.connect_intranet():
            self._set_busy(False)
            self._show_error("Impossible de se connecter à l'Intranet.")
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
                self._show_error("Utilisateur introuvable.")
                db.disconnect_all()
                return

            user_id, first_name, last_name, email, pwd_hash, is_dir, is_coord, is_sup = row

            pass_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if pwd_hash and pwd_hash != pass_hash:
                self._show_error("Mot de passe incorrect.")
                db.disconnect_all()
                return

            if not (is_dir or is_coord or is_sup):
                self._show_error(
                    "Cette application est réservée aux superviseurs, "
                    "coordinateurs et administrateurs.")
                db.disconnect_all()
                return

            if is_dir: role = UserRole.ADMIN
            elif is_coord: role = UserRole.COORD
            else: role = UserRole.SUPERVISEUR

            session.user_id = user_id
            session.email = email
            session.full_name = f"{first_name} {last_name}"
            session.role = role
            session.conn_mode = ConnMode.INTRANET
            session.is_authenticated = True

            log(f"Connexion Intranet : {session.full_name} ({role.value})")
            self._open_main_window()

        except Exception as e:
            log(f"_on_intranet: {e}")
            self._show_error(str(e))
            db.disconnect_all()

    def _on_cloud(self):
        try:
            self._check_rate_limit('cloud')
        except RuntimeError as e:
            self._show_error(str(e))
            return
        self._hide_error()
        self._set_busy(True)
        self._worker = _Worker(OAuth2Manager.authenticate, parent=self)
        self._worker.done.connect(self._on_cloud_done)
        self._worker.start()

    def _on_cloud_done(self, result):
        self._set_busy(False)
        ok, res, err = result
        if not ok:
            self._record_failure('cloud')
            self._show_error(err or "Authentification échouée.")
            return

        # Vérifier le rôle
        if res.role not in (UserRole.SUPERVISEUR, UserRole.COORD, UserRole.ADMIN):
            self._show_error("Accès non autorisé pour ce compte.")
            return

        session.user_id = res.user_id
        session.email = res.email
        session.full_name = res.full_name
        session.role = res.role
        session.conn_mode = ConnMode.CLOUD
        session.is_authenticated = True

        log(f"Connexion Cloud : {session.full_name} ({res.role.value})")
        self._open_main_window()

    def _open_main_window(self):
        from LarcSuperviseur.views.main_window import MainWindow
        self.main = MainWindow()
        self.main.resize(1200, 750)
        self.main.showMaximized()
        self.close()

    def _update_network_status(self):
        intranet_ok, internet_ok = detect_network()
        if intranet_ok:
            self._net_label.setText("Intranet ●")
            self._net_label.setStyleSheet(f"color: {theme_manager.palette.success}; font-weight: bold; font-size: 11px;")
        elif internet_ok:
            self._net_label.setText("Cloud ●")
            self._net_label.setStyleSheet(f"color: {theme_manager.palette.primary}; font-weight: bold; font-size: 11px;")
        else:
            self._net_label.setText("Hors ligne")
            self._net_label.setStyleSheet(f"color: {theme_manager.palette.text_disabled}; font-weight: bold; font-size: 11px;")

    def _show_error(self, msg: str):
        self._err_label.setText(msg)

    def _hide_error(self):
        self._err_label.setText("")

    def _set_busy(self, busy: bool):
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(not busy)
        if busy:
            self._status_label.setText("Connexion en cours...")
        else:
            self._status_label.setText("")
