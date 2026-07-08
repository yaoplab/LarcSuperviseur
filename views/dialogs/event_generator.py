from larccommon.l10n import _
from phibuilder.phi.scale import SpacingToken
from phibuilder.widgets import M3Button, M3Card, M3Label, M3TextField
from phibuilder.widgets.button import ButtonVariant
from phibuilder.widgets.card import CardVariant
from PySide6.QtCore import QDate, Qt, QTime
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from LarcSuperviseur.common.database import db
from LarcSuperviseur.common.network import detect_network
from LarcSuperviseur.common.session import session
from LarcSuperviseur.common.theme import theme_manager
from LarcSuperviseur.views.core.data_loader import DataLoader


class EventGenerator(QDialog):
    _CAT_COLORS = {
        "Bureau BI": ("#d32f2f", "#ffffff"),
        "Médical": ("#1976d2", "#ffffff"),
        "Sortie": ("#e65100", "#ffffff"),
        "Suivi": ("#f9a825", "#222222"),
    }

    def __init__(self, student_id: int, parent=None):
        super().__init__(parent)
        self._student_id = student_id
        self._locations = []
        self._classroom_lieu_ids = set()
        self._selected_lieu_id = 0
        self._selected_lieu_label = ""
        self._selected_subject = ""
        self._type_hierarchy = {}
        self._student_classroom_id = None
        self._student_classroom_label = ""
        self._loader = DataLoader()
        self._path = []
        self._mode = None
        self._modes = []
        self._absence_types = []
        self._retard_durations = []
        self._phi = theme_manager.phi_theme
        self.setWindowTitle(_("event.window_title").format(id=student_id))
        self.setMinimumWidth(680)
        self._load_student_classroom()
        self._load_types_from_db()
        self._load_locations()
        self._init_ui()

    # ── Data loading ──

    def _load_student_classroom(self):
        data = self._loader.get_student_classroom(self._student_id)
        if data:
            self._student_classroom_id = data["classroom_id"]
            self._student_classroom_label = data["label"]

    def _load_locations(self):
        self._locations = self._loader.get_locations()

    def _load_types_from_db(self):
        conn = db.server_conn
        lang = getattr(session, "fk_language", 2)
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT DISTINCT type_event FROM larcauth_type_status '
                'WHERE fk_language = %s AND "Enabled" = TRUE ORDER BY idtypeevent',
                (lang,),
            )
            mode_map = {"Absence": "absence", "Retard": "retard"}
            self._modes = []
            for (type_evt,) in cur.fetchall():
                cat = type_evt.strip()
                key = next((v for k, v in mode_map.items() if k in cat), None)
                if not key:
                    key = "autres"
                self._modes.append((cat, key))

            cur.execute(
                'SELECT type_event, Ststus_Niveau2 FROM larcauth_type_status '
                'WHERE fk_language = %s AND "Enabled" = TRUE AND Ststus_Niveau2 IS NOT NULL '
                'ORDER BY idtypeevent',
                (lang,),
            )
            self._absence_types = []
            self._retard_durations = []
            for type_evt, niveau2 in cur.fetchall():
                if "Absence" in type_evt or "absence" in type_evt.lower():
                    self._absence_types.append(niveau2.strip())
                elif "Retard" in type_evt or "Tardiness" in type_evt:
                    self._retard_durations.append(niveau2.strip())
        except Exception:
            pass

        # Keep existing type hierarchy for "Autres" mode
        self._type_hierarchy = self._loader.get_event_types_tree()

    # ── UI ──

    def _init_ui(self):
        phi = self._phi
        c = phi.colors
        sp = phi.spacing.spacing

        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            sp(SpacingToken.LG), sp(SpacingToken.LG), sp(SpacingToken.LG), sp(SpacingToken.LG)
        )
        outer.setSpacing(sp(SpacingToken.MD))

        # ── Breadcrumb bar ──
        self._crumb_widget = QWidget()
        self._crumb_layout = QHBoxLayout(self._crumb_widget)
        self._crumb_layout.setContentsMargins(0, 0, 0, 0)
        self._crumb_layout.setSpacing(sp(SpacingToken.XS))
        self._crumb_widget.hide()
        outer.addWidget(self._crumb_widget)

        # ── Step container (espace unique réinitialisé à chaque étape) ──
        self._step_card = M3Card(theme=phi, variant=CardVariant.ELEVATED, parent=self)
        sl = self._step_card.content_layout()
        sl.setContentsMargins(
            sp(SpacingToken.LG), sp(SpacingToken.LG), sp(SpacingToken.LG), sp(SpacingToken.LG)
        )
        self._step_grid = QGridLayout()
        self._step_grid.setSpacing(sp(SpacingToken.SM))
        sl.addLayout(self._step_grid)
        outer.addWidget(self._step_card)

        # ── Badge (résumé de l'événement) ──
        self._bd = M3Card(theme=phi, variant=CardVariant.FILLED, parent=self)
        bdl = self._bd.content_layout()
        bdl.setContentsMargins(
            sp(SpacingToken.XL), sp(SpacingToken.SM), sp(SpacingToken.XL), sp(SpacingToken.SM)
        )
        self._btxt = M3Label("", theme=phi, style="title_medium")
        self._btxt.setAlignment(Qt.AlignCenter)
        bdl.addWidget(self._btxt)
        self._bd.hide()
        outer.addWidget(self._bd)

        # ── Final section (date / note / actions) ──
        self._final = QWidget()
        fl = QVBoxLayout(self._final)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(sp(SpacingToken.MD))

        dr = QHBoxLayout()
        dr.setSpacing(sp(SpacingToken.MD))
        dr.addWidget(M3Label(_("event.date"), theme=phi, style="body_medium"))
        self._date_edit = QDateEdit(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dddd dd MMMM yyyy")
        self._date_edit.setStyleSheet(
            f"QDateEdit {{ padding: {sp(SpacingToken.MD)}px; border: 1px solid {c.outline_variant}; "
            f"border-radius: {sp(SpacingToken.XS)}px; font-size: 13px; "
            f"background: {c.surface}; color: {c.on_surface}; font-weight: bold; }}"
        )
        dr.addWidget(self._date_edit, 2)
        dr.addWidget(M3Label(_("event.time"), theme=phi, style="body_medium"))
        self._time_edit = QTimeEdit(QTime.currentTime())
        self._time_edit.setDisplayFormat("HH:mm")
        self._time_edit.setStyleSheet(
            f"QTimeEdit {{ padding: {sp(SpacingToken.MD)}px; border: 1px solid {c.outline_variant}; "
            f"border-radius: {sp(SpacingToken.XS)}px; font-size: 13px; "
            f"background: {c.surface}; color: {c.on_surface}; font-weight: bold; }}"
        )
        dr.addWidget(self._time_edit, 1)
        self._src = M3Label("", theme=phi, style="body_small")
        self._update_source_label()
        dr.addWidget(self._src)
        fl.addLayout(dr)

        fl.addWidget(M3Label(_("event.note"), theme=phi, style="body_medium"))
        self._ni = M3TextField(placeholder=_("event.note_placeholder"), theme=phi)
        fl.addWidget(self._ni)

        ar = QHBoxLayout()
        ar.addStretch()
        cb = M3Button(_("common.button.cancel"), theme=phi, variant=ButtonVariant.OUTLINED)
        cb.clicked.connect(self.reject)
        ar.addWidget(cb)
        self._vb = M3Button(_("event.validate_button"), theme=phi, variant=ButtonVariant.FILLED)
        self._vb.clicked.connect(self._validate)
        ar.addWidget(self._vb)
        fl.addLayout(ar)

        self._final.hide()
        outer.addWidget(self._final)

        self._show_step()

    # ── Step rendering ──

    def _show_step(self):
        self._step_card.hide()
        self._clear_grid(self._step_grid)
        self._update_breadcrumb()

        if not self._path:
            self._show_mode_buttons()
            self._step_card.show()
            self._bd.hide()
            self._final.hide()
            return

        if self._is_final_step():
            self._step_card.hide()
            self._bd_update()
            self._bd.show()
            self._final.show()
            return

        if self._mode == "absence" and len(self._path) == 1:
            self._show_absence_natures()
        elif self._mode == "retard" and len(self._path) == 1:
            self._show_retard_durations()
        elif self._mode == "autres" and len(self._path) == 1:
            self._show_locations()
        elif self._mode == "autres" and len(self._path) == 2 and self._is_classroom():
            self._show_subjects()
        elif self._mode == "autres" and len(self._path) >= 2:
            self._show_type_options()

        self._step_card.show()
        self._bd.hide()
        self._final.hide()

        self.adjustSize()

    def _show_mode_buttons(self):
        phi = self._phi
        h = phi.spacing.spacing(SpacingToken.XL) * 2
        modes = self._modes
        h = phi.spacing.spacing(SpacingToken.XL) * 2
        for idx, (label, mode) in enumerate(modes):
            b = M3Button(label, theme=phi, variant=ButtonVariant.TONAL)
            b.setMinimumHeight(h)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked, l=label, m=mode: self._on_step_click(l, mode=m))
            self._step_grid.addWidget(b, 0, idx)

    def _show_absence_natures(self):
        phi = self._phi
        for idx, n in enumerate(self._absence_types):
            b = M3Button(n, theme=phi, variant=ButtonVariant.TONAL)
            b.setMinimumHeight(48)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked, l=n: self._on_step_click(l))
            self._step_grid.addWidget(b, idx // 3, idx % 3)

    def _show_retard_durations(self):
        phi = self._phi
        for idx, d in enumerate(self._retard_durations):
            b = M3Button(d, theme=phi, variant=ButtonVariant.TONAL)
            b.setMinimumHeight(48)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked, l=d: self._on_step_click(l))
            self._step_grid.addWidget(b, idx // 3, idx % 3)

    def _show_locations(self):
        phi = self._phi
        for idx, (lid, sid, lieu_name) in enumerate(self._locations):
            b = M3Button(lieu_name, theme=phi, variant=ButtonVariant.OUTLINED)
            b.setMinimumHeight(44)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(
                lambda checked, l=lieu_name, lid=lid: self._on_step_click(
                    l, lieu_id=lid, lieu_label=l
                )
            )
            self._step_grid.addWidget(b, idx // 3, idx % 3)
            if sid:
                self._classroom_lieu_ids.add(lid)

    def _is_classroom(self):
        return self._selected_lieu_id in self._classroom_lieu_ids

    def _show_subjects(self):
        phi = self._phi
        if not self._student_classroom_id:
            self._show_type_options()
            return
        term_id = self._loader.get_term_id()
        subjects = self._loader.get_classroom_subjects(self._student_classroom_id, term_id)
        if not subjects:
            self._show_type_options()
            return
        for idx, (sid, label, tid, tname) in enumerate(subjects):
            b = M3Button(label, theme=phi, variant=ButtonVariant.OUTLINED)
            b.setMinimumHeight(40)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tname or "")
            b.clicked.connect(lambda checked, l=label: self._on_step_click(l, subject_label=l))
            self._step_grid.addWidget(b, idx // 4, idx % 4)

    def _show_type_options(self):
        phi = self._phi
        node = self._get_type_node()
        if node is None:
            return
        if isinstance(node, dict):
            for idx, (k, v) in enumerate(node.items()):
                bg, fg = self._CAT_COLORS.get(k, (None, None))
                b = M3Button(k, theme=phi, variant=ButtonVariant.FILLED)
                b.setMinimumHeight(52)
                b.setCursor(Qt.PointingHandCursor)
                if bg:
                    b.setStyleSheet(f"M3Button {{ background-color: {bg}; color: {fg}; }}")
                b.clicked.connect(lambda checked, l=k: self._on_step_click(l))
                self._step_grid.addWidget(b, idx // 2, idx % 2)
        elif isinstance(node, list):
            for idx, leaf in enumerate(node):
                b = M3Button(leaf, theme=phi, variant=ButtonVariant.TONAL)
                b.setMinimumHeight(48)
                b.setCursor(Qt.PointingHandCursor)
                b.clicked.connect(lambda checked, l=leaf: self._on_step_click(l))
                self._step_grid.addWidget(b, idx // 3, idx % 3)

    # ── Step click ──

    def _on_step_click(self, label, **data):
        self._path.append(label)
        if "mode" in data:
            self._mode = data["mode"]
        if "lieu_id" in data:
            self._selected_lieu_id = data["lieu_id"]
            self._selected_lieu_label = data.get("lieu_label", label)
        if "subject_label" in data:
            self._selected_subject = data["subject_label"]
        self._show_step()

    # ── Breadcrumb ──

    def _update_breadcrumb(self):
        while self._crumb_layout.count():
            item = self._crumb_layout.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.deleteLater()

        if not self._path:
            self._crumb_widget.hide()
            return

        phi = self._phi
        c = phi.colors

        for i, label in enumerate(self._path):
            if i > 0:
                sep = M3Label(">", theme=phi, style="body_medium")
                sep.setStyleSheet(f"color: {c.outline};")
                self._crumb_layout.addWidget(sep)

            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            is_last = i == len(self._path) - 1
            if is_last:
                btn.setStyleSheet(
                    f"QPushButton {{ color: {c.on_surface}; font-size: 14px; font-weight: bold; "
                    f"border: none; background: transparent; text-align: left; padding: 4px 0; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ color: {c.primary}; font-size: 14px; font-weight: bold; "
                    f"border: none; background: transparent; text-align: left; padding: 4px 0; }}"
                    f"QPushButton:hover {{ color: {c.primary_container}; }}"
                )
                btn.clicked.connect(lambda checked, idx=i: self._on_crumb_click(idx))
            self._crumb_layout.addWidget(btn)

        self._crumb_layout.addStretch()
        self._crumb_widget.show()

    def _on_crumb_click(self, index):
        self._path = self._path[: index + 1]
        if self._mode == "autres" and len(self._path) < 2:
            self._selected_lieu_id = 0
        self._selected_lieu_label = ""
        self._selected_subject = ""
        self._show_step()

    # ── Helpers ──

    def _clear_grid(self, g):
        while g.count():
            w = g.takeAt(0).widget()
            if w:
                w.deleteLater()

    def _type_start(self):
        """Index dans _path où commence les types (après Autres, Lieu, [Matière])."""
        if self._mode != "autres" or len(self._path) < 2:
            return None
        if self._is_classroom():
            return 3
        return 2

    def _get_type_node(self):
        start = self._type_start()
        if start is None:
            return None
        if len(self._path) == start:
            return self._type_hierarchy
        node = self._type_hierarchy
        for label in self._path[start:]:
            if isinstance(node, dict):
                node = node.get(label)
            elif isinstance(node, list):
                return None
            else:
                return None
        return node

    def _is_final_step(self):
        if not self._path:
            return False
        if self._mode == "absence" and len(self._path) >= 2:
            return True
        if self._mode == "retard" and len(self._path) >= 2:
            return True
        if self._mode == "autres":
            start = self._type_start()
            if start is not None and len(self._path) > start:
                node = self._get_type_node()
                if node is None or not isinstance(node, (dict, list)) or len(node) == 0:
                    return True
        return False

    def _compute_type_path(self):
        if self._mode == "absence" and len(self._path) >= 2:
            return f"Absence > {self._path[1]}"
        if self._mode == "retard" and len(self._path) >= 2:
            return f"Retard > {self._path[1]}"
        if self._mode == "autres":
            start = self._type_start()
            if start is not None and len(self._path) > start:
                return " > ".join(self._path[start:])
        return None

    # ── Badge & source ──

    def _bd_update(self):
        c = self._phi.colors
        type_path = self._compute_type_path()
        if not type_path:
            self._bd.hide()
            return
        if self._mode == "absence":
            self._btxt.setText(_("event.badge_absence").format(path=type_path))
            self._btxt.setStyleSheet(f"color: {c.on_error}; font-weight: bold;")
            self._bd.setStyleSheet(f"M3Card {{ background: {c.error}; border-radius: 12px; }}")
        elif self._mode == "retard":
            self._btxt.setText(_("event.badge_retard").format(path=type_path))
            self._btxt.setStyleSheet(f"color: {c.on_tertiary}; font-weight: bold;")
            self._bd.setStyleSheet(f"M3Card {{ background: {c.tertiary}; border-radius: 12px; }}")
        else:
            txt = _("event.badge_other").format(path=type_path)
            if self._selected_lieu_label:
                txt += f"  —  {self._selected_lieu_label}"
            self._btxt.setText(txt)
            self._btxt.setStyleSheet(f"color: {c.on_primary}; font-weight: bold;")
            self._bd.setStyleSheet(f"M3Card {{ background: {c.primary}; border-radius: 12px; }}")
        self._bd.show()

    def _update_source_label(self):
        ok, _ign = detect_network()
        c = self._phi.colors
        if ok and db.is_server_connected:
            self._src.setText(_("event.source_intranet"))
            self._src.setStyleSheet(f"color: {c.primary}; font-weight: bold;")
        else:
            self._src.setText(_("event.source_cloud"))
            self._src.setStyleSheet(f"color: {c.tertiary}; font-weight: bold;")

    # ── Validate ──

    def _validate(self):
        type_path = self._compute_type_path()
        if not type_path:
            QMessageBox.warning(
                self, _("common.dialog.error_title"), _("event.select_type_required")
            )
            return
        evt = self._date_edit.date().toString("yyyy-MM-dd")
        try:
            cur = db.server_conn.cursor()
            cur.execute("SELECT MAX(date_all) FROM agenda")
            r = cur.fetchone()
            if r and r[0]:
                last = str(r[0])[:10]
                if evt > last:
                    QMessageBox.warning(
                        self,
                        _("common.dialog.error_title"),
                        _("event.date_error").format(last=last),
                    )
                    return
        except Exception:
            pass
        self.accept()

    def get_data(self) -> dict:
        dt = self._date_edit.dateTime()
        dt.setTime(self._time_edit.time())
        type_path = self._compute_type_path()
        is_abs_or_ret = self._mode in ("absence", "retard")
        return {
            "student_id": self._student_id,
            "event_type": type_path,
            "event_at": dt.toString("yyyy-MM-dd HH:mm:ss"),
            "classroom_id": self._student_classroom_id,
            "classroom_label": self._student_classroom_label,
            "lieu_id": self._selected_lieu_id if not is_abs_or_ret else 0,
            "lieu_label": self._selected_lieu_label if not is_abs_or_ret else "",
            "subject_id": None,
            "subject_label": self._selected_subject,
            "note": self._ni.text().strip(),
            "source": "cloud" if not detect_network()[0] else "intranet",
        }
