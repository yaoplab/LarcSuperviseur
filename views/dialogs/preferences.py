from larccommon.l10n import Translator, _
from phibuilder.widgets import M3Button, M3Dialog, M3Frame, M3Label
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QVBoxLayout,
)

from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.views.core.cardsList.config import CARD_THEMES


def _btn_style(selected: bool):
    p = theme_manager.palette
    if selected:
        return (
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 4px; font-weight: bold; "
            f"font-size: {theme_manager.font_size(11)}px; }}"
        )
    return (
        f"QPushButton {{ background: {p.surface}; color: {p.text_strong}; "
        f"border: 1px solid {p.outline_variant}; border-radius: 4px; "
        f"font-size: {theme_manager.font_size(11)}px; }}"
        f"QPushButton:hover {{ border-color: {p.primary}; }}"
    )


class PreferencesDialog(M3Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("prefs.title"))
        self.setFixedSize(420, 380)
        self._orig_lang = session.fk_language
        self._orig_theme = session.theme_pref
        self._orig_card = session.card_theme
        self._init_ui()

    def _make_group(
        self, label: str, options: list[tuple[str, str]], get_current, set_current
    ) -> QButtonGroup:
        frame = M3Frame()
        frame.setStyleSheet(
            f"background: {theme_manager.palette.surface_variant}; "
            f"border-radius: 6px; padding: 6px;"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 4, 8, 4)
        fl.setSpacing(4)
        lbl = M3Label(f"<b>{label}</b>")
        lbl.setStyleSheet(
            f"font-size: {theme_manager.font_size(11)}px; "
            f"color: {theme_manager.palette.text_strong};"
        )
        fl.addWidget(lbl)
        row = QHBoxLayout()
        row.setSpacing(6)
        group = QButtonGroup(self)
        group.setExclusive(True)
        current = get_current()
        for val, display in options:
            btn = M3Button(display)
            btn.setCheckable(True)
            btn.setFixedSize(89, 34)
            btn.setChecked(val == current)
            btn.setStyleSheet(_btn_style(val == current))
            btn.clicked.connect(
                lambda checked, v=val: (set_current(v), self._refresh_group_styles(group))
            )
            group.addButton(btn)
            row.addWidget(btn)
        row.addStretch()
        fl.addLayout(row)
        self.layout().addWidget(frame)
        return group

    def _refresh_group_styles(self, group: QButtonGroup):
        for btn in group.buttons():
            btn.setStyleSheet(_btn_style(btn.isChecked()))

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 13, 13, 13)
        layout.setSpacing(8)

        self._make_group(
            _("prefs.language"),
            [("fr", _("common.language.fr")), ("en", _("common.language.en"))],
            lambda: "fr" if session.fk_language == 2 else "en",
            lambda v: setattr(session, "fk_language", 2 if v == "fr" else 1),
        )

        self._make_group(
            _("prefs.theme"),
            [(k, v.label) for k, v in theme_manager._themes.items()],
            lambda: session.theme_pref,
            lambda v: setattr(session, "theme_pref", v),
        )

        self._make_group(
            _("prefs.card_size"),
            [(k, k.capitalize()) for k in CARD_THEMES],
            lambda: session.card_theme,
            lambda v: setattr(session, "card_theme", v),
        )

        layout.addStretch()

        p = theme_manager.palette
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = M3Button(_("common.button.ok"))
        ok_btn.setStyleSheet(
            f"QPushButton {{ background: {p.primary}; color: {p.on_primary}; "
            f"border: none; border-radius: 6px; padding: 6px 20px; font-weight: bold; }}"
        )
        ok_btn.clicked.connect(self._on_ok)
        btn_row.addWidget(ok_btn)
        cancel_btn = M3Button(_("common.button.cancel"))
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _apply(self):
        lang_id = session.fk_language
        lang = "en" if lang_id == 1 else "fr"
        trans = Translator.instance(lang)
        trans.reload(Translator.l10n_dir())
        theme_manager.set_active(session.theme_pref)
        # Persister dans larcauth_config
        if session.user_id:
            try:
                cur = db.server_conn.cursor()
                for k, v in [
                    ("theme_pref", session.theme_pref),
                    ("card_theme", session.card_theme),
                    ("fk_language", str(session.fk_language)),
                ]:
                    cur.execute(
                        "INSERT INTO larcauth_config (key, value) VALUES (%s, %s) "
                        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                        (f"user_{session.user_id}_{k}", v),
                    )
                db.server_conn.commit()
            except Exception:
                pass
        conn = db.server_conn
        if conn and session.user_id:
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE larcauth_aecuser SET fk_language = %s WHERE id = %s",
                    (lang_id, session.user_id),
                )
                conn.commit()
            except Exception:
                pass

    def _on_ok(self):
        self._apply()
        self.accept()

    def _on_cancel(self):
        session.fk_language = self._orig_lang
        session.theme_pref = self._orig_theme
        session.card_theme = self._orig_card
        self.reject()
