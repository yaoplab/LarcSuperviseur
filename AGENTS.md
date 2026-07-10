# AGENTS.md — Projets Larc (Mise à jour 10/07/2026)

## What this is

PySide6 (Qt6) desktop apps for student attendance/event supervision + administration.
Direct psycopg2 PostgreSQL — no ORM, no REST API.
Windows-only. Bilingual UI (FR/EN via `LARC_LANG` env var).
Requires `LarcCommon` installed (`pip install -e C:\Projets\LarcCommon`).
Dépend aussi de `materialyoucolor` (moteur de couleurs M3).

## How to run

```bash
cd C:\Projets
set LARC_LANG=fr    # Français (défaut)
set LARC_LANG=en    # English
python -m LarcSuperviseur          # Supervision
python -m LarcSecretaire           # Secrétariat
python -m LarcHub                  # Hub
python -m LarcDesign               # Designer (i18n, thèmes, rôles, logs, types, lieux)
```

## Architecture des dépôts

| Dépôt | Rôle | Entrée |
|---|---|---|
| `LarcCommon/` | Librairie partagée : `larccommon`, `phibuilder` | `pip install -e C:\Projets\LarcCommon` |
| `LarcSuperviseur/` | Supervision présence/événements | `python -m LarcSuperviseur` |
| `LarcSecretaire/` | Secrétariat (notes, dossiers, parents) | `python -m LarcSecretaire` |
| `LarcHub/` | Hub LarcAdmin (fusion Supervision + Secrétariat) | `python -m LarcHub` |
| `LarcDesign/` | Designer (i18n, thèmes, rôles, logs, types, lieux) | `python -m LarcDesign` |
| `eLarcProfPy/` | Professeurs (SQLite locale, séparé) | — |

## LarcCommon (C:\Projets\LarcCommon/)

**larccommon** :
- `larccommon/theme.py` — `ThemeManager` + 4 thèmes (blue/dark/sobre/contrast) + `phi_theme` (unifié phibuilder) + `ImageScale` (tailles standard)
- `larccommon/l10n/` — `Translator` + `fr.json`/`en.json` (~650 clés)
- `larccommon/database.py` — `db` (connexion PostgreSQL directe)
- `larccommon/network.py` — `detect_network()` → (intranet_ok, internet_ok)
- `larccommon/config_loader.py` — `find_cfg()` cherche config.ini (priorité LarcCommon/)
- `larccommon/icons.py` — Icônes Material Design 3 en SVG vers QIcon (40 icônes)
- `larccommon/photos.py` — gestion photos élèves
- `larccommon/logger.py` — log
- `config.ini` — DB Intranet (5432), Supabase Cloud (6543), OAuth2, SMTP

**phibuilder** widgets M3 (25 widgets) :
- `widgets/button.py` — `M3Button` (filled/tonal/outlined/text)
- `widgets/label.py` — `M3Label`, `widgets/card.py` — `M3Card`
- `widgets/textfield.py` — `M3TextField`, `widgets/combo.py` — `M3ComboBox`
- `widgets/table.py` — `M3TableWidget`, `widgets/listwidget.py` — `M3ListWidget`
- `widgets/dialog.py` — `M3Dialog`, `widgets/menu.py` — `M3Menu`
- `widgets/tab.py` — `M3TabWidget`, `widgets/dateedit.py` — `M3DateEdit`
- `widgets/timeedit.py` — `M3TimeEdit`, `widgets/frame.py` — `M3Frame`
- `widgets/scrollarea.py` — `M3ScrollArea`, `widgets/stackedwidget.py` — `M3StackedWidget`
- `widgets/headerview.py` — `M3HeaderView`, `widgets/dialogbuttonbox.py` — `M3DialogButtonBox`
- `widgets/textedit.py` — `M3TextEdit`, `widgets/progressbar.py` — `M3ProgressBar`
- `widgets/groupbox.py` — `M3GroupBox`, `widgets/splitter.py` — `M3Splitter`
- `widgets/profilebutton.py` — `M3ProfileButton` (QPushButton pur sans contrainte M3)
- `widgets/bottomsheet.py` — `M3BottomSheet`, `widgets/snackbar.py` — `M3Snackbar`
- `widgets/navigation.py` — `M3NavigationBar`, `M3Sidebar`
- `phi/scale.py` — `PhiScale(base_spacing=4)`, `SpacingToken` (Fibonacci 1,2,3,5,8,13,21,34,55,89...)
- `theme/` — `Theme`, `ThemeConfig`, `M3ColorScheme`, `M3Typography`

## Règles de code

- **Imports UI** : TOUJOURS depuis `phibuilder.widgets`, JAMAIS de `PySide6.QtWidgets` direct
- **Exceptions** : `QMessageBox`, `QApplication`, `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QButtonGroup`, `QTableWidgetItem` (pas de wrapper M3)
- **Couleurs** : `theme_manager.phi_theme` pour widgets M3, `theme_manager.palette` pour QSS
- **Icônes** : `from larccommon.icons import icon as md3_icon` → `md3_icon('name', color, size=18)`
  - **INTERDIT** : images (PNG/JPG) comme icônes — toujours utiliser les SVG Material Design 3
  - Tailles carrées uniquement, via `ds.icon_sm` (20), `ds.icon_md` (32), `ds.icon_lg` (52)
  - Liste des 40 icônes disponibles : `light_mode`, `dark_mode`, `contrast`, `tonality`, `refresh`, `add`, `arrow_back`, `close`, `check`, `save`, `delete`, `edit`, `person`, `settings`, `menu`, `event`, `timer`, `calendar_today`, `schedule`, `cloud`, `wifi`, `wifi_off`, `warning`, `school`, `home`, `search`, `logout`, `filter_list`, `visibility`, `location_on`, `subject`, `description`, `bolt`, `lock`, `check_circle`, `cancel`, `sync`, `info`, `error`
- **Tailles images** : `theme_manager.image.*` à la place de hardcoded
  - `image.logo=89`, `image.icon_btn=18`, `image.icon_menu=18`, `image.icon_large=32`
  - `image.theme_btn=34`, `image.profile_btn=34`, `image.refresh_btn=34`
  - `image.add_btn=100`, `image.avatar=150`, `image.photo=150`, `image.field_height=56`
- **Espacement** : `phi.spacing.spacing(SpacingToken.XXL)` via Fibonacci
- **Login** : utilise le QSS de `_style()` (copie LarcSuperviseur). NE PAS appeler `theme_manager.bind(app)` dans les apps qui ont leur propre QSS de login — conflit de couches QSS qui rend la fenêtre illisible.
- **theme=phi** : inutile pour les widgets du login (QLabel, QPushButton, QLineEdit) car le QSS les style déjà.
- **Structure existante** : pour une nouvelle app, copier la structure d'une app existante (LarcSuperviseur login), ne pas réinventer
- **Heritage fenêtre** : toujours `QWidget` pour une fenêtre autonome, jamais `M3Card`
- **Pas de test framework, pas de linting** — lancer l'app pour vérifier

## Design System — `larccommon/design_system.py`

**RÈGLE ABSOLUE POUR TOUTE NOUVELLE CRÉATION UI : ZÉRO HARDCODING.**

Toutes les tailles, espacements, couleurs, bordures doivent passer par le Design System :

```python
from larccommon.design_system import ds

# Espacement — jamais setSpacing(12) ou setContentsMargins(6,6,6,6)
layout.setSpacing(ds.space_sm)
layout.setContentsMargins(ds.space_md, ds.space_md, ds.space_md, ds.space_md)

# Hauteurs des champs — jamais setFixedHeight(52)
field.setFixedHeight(ds.field_height)

# Bordures — jamais border-radius: 8px; ou border: 1px solid #xxx
field.setStyleSheet(ds.flat_input_qss())

# Tableaux — harmonisés avec le formulaire
table.setStyleSheet(ds.table_qss())

# Couleurs — jamais #1565C0 ou #c0392b
ds.p.primary, ds.p.surface, ds.p.error, ds.p.outline

# Couleurs M3 — pour widgets phibuilder
ds.c.primary, ds.c.on_surface, ds.c.outline_variant

# Boutons — variants M3 standard
M3Button("OK", theme=ds.phi, variant=ds.BTN_FILLED)

# Fibonacci direct
ds.sp(SpacingToken.XXL)   # 84 px
```

### Tokens rapides

| Catégorie | Token | Valeur |
|---|---|---|
| Espacement | `ds.space_xs` / `ds.space_sm` / `ds.space_md` / `ds.space_xl` | 8 / 12 / 20 / 52 px |
| Champs | `ds.field_height` | 32 px |
| Boutons | `ds.button_height` / `ds.icon_lg` | 52 px |
| Bordures | `ds.radius_xs` / `ds.radius_sm` / `ds.border_width` | 4 / 8 / 1 px |
| Polices | `ds.font_title` / `ds.font_body` / `ds.font_small` | 14 / 13 / 11 px |
| Tableaux | `ds.table_row_min` / `ds.table_qss()` | 32 px |

### Contrainte stricte padding champs
- Tout champ de saisie DOIT avoir un `padding` gauche ≥ `ds.space_md` (20px) — le premier caractère ne touche jamais la bordure
- Le `_flat_field` standard complet :
  ```python
  f"background: transparent; border: 1px solid {p.outline}; "
  f"border-radius: {ds.radius_xs}px; padding: {ds.space_md}px; "
  f"color: {p.text_strong}; font-size: {ds.font_body}px;"
  ```
- **INTERDIT** d'oublier `padding` ou `color` dans un override QSS de champ

### Pattern standard pour un formulaire

```python
phi = theme_manager.phi_theme
sp = phi.spacing.spacing
p = theme_manager.palette
_fh = ds.field_height   # 52 px

# Card identité
card = M3Card(theme=phi, variant=ds.CARD_ELEVATED)
cl = card.content_layout()
cl.setSpacing(ds.space_sm)

field = M3TextField(theme=phi)
field.setFixedHeight(_fh)
field.setStyleSheet(ds.flat_input_qss())

# Tableau
table = M3TableWidget(theme=phi)
table.setStyleSheet(ds.table_qss())
table.horizontalHeader().setFixedHeight(ds.space_lg)
```

## Audit padding/margin (10/07/2026)

### Règle absolue
- **TOUTE** valeur de padding/margin/spacing dans QSS doit utiliser les tokens `ds.*` (`ds.space_xxs`=4, `ds.space_xs`=8, `ds.space_sm`=12, `ds.space_md`=20, `ds.space_lg`=32, etc.)
- **TOUT** `setContentsMargins(a, b, c, d)`, `setSpacing(n)`, `setFixedWidth(n)` avec des nombres littéraux est interdit — utiliser `ds.space_*`, `SpacingToken`, ou `ds.sp()`
- Exceptions : valeurs 0 (zéro) pour collapse et valeurs calculées dynamiquement

### Tokens disponibles (`larccommon/design_system._DesignSystem` → singleton `ds`)
```
space_xxs=4  space_xs=8   space_sm=12  space_md=20
space_lg=32  space_xl=52  space_xxl=84 space_xxxl=136
field_height=52  button_height=52  header_height=52  table_row_min=32
radius_xs=4  radius_sm=8  radius_md=12  radius_lg=20  border_width=1
```
QSS helpers intégrés dans `ds` : `ds.flat_input_qss()`, `ds.table_qss()`, `ds.panel_qss()`, `ds.label_qss()`

### Résultat par projet

| Projet | padding: QSS | setContentsMargins | setSpacing | setFixedWidth |
|--------|:----------:|:-----------------:|:----------:|:------------:|
| LarcSecretaire (focus) | 51 (dont 11 hard) | 28 (dont 10 hard) | 78 (dont 18 hard) | 0 hard |
| LarcProf | 60 (dont 57 hard) | 38 (dont 30 hard) | 47 (dont 43 hard) | 4 hard |
| LarcSuperviseur | 5 (tous hard) | 24 (dont 18 hard) | 40 (dont 25 hard) | 1 hard (sidebar 233px) |
| LarcHub | 5 (tous hard) | 4 (tous hard) | 7 (tous hard) | 0 hard |
| LarcDesign | 0 hard | 9 (dont 1 hard) | 12 (dont 3 hard) | 1 hard (sidebar 233px) |

**Total hardcodé estimé : ~170 occurrences** à migrer vers ds.* tokens priorité basse (UI fonctionnelle).

### Priorité
1. **Haute** : LarcProf top bar (padding grid QSS vient d'être fixé en `ds.space_sm px ds.space_md px`)
2. **Moyenne** : LarcSecretaire login (16 hard) + LarcHub login (14 hard) + LarcSuperviseur login (16 hard)
3. **Basse** : le reste — audit complet fait, correction au fil des modifications UI

### Fichier de référence
`C:\Projets\LarcSecretaire\views\parent_manager.py` — **100% conforme** Design System (0 hardcoded).

## LarcSuperviseur — Architecture

| Fichier | Rôle | Lignes |
|---|---|---|
| `main.py` | Point d'entrée | 38 |
| `views/main_window.py` | Orchestrateur principal | ~1725 |
| `views/top_bar.py` | Barre du haut (date, réseau, thème, périodes) | ~280 |
| `views/panels/sidebar.py` | Navigation gauche (programmes, classes) | ~160 |
| `views/panels/group_panel.py` | Stats groupe : KPIs, charts, historique | ~500 |
| `views/panels/class_panel.py` | Grille cartes élèves | 90 |
| `views/panels/student_detail.py` | Détail élève : photo, infos, événements | ~400 |
| `views/core/data_loader.py` | Toutes les requêtes DB (33 méthodes) | 759 |
| `views/core/event_actions.py` | CRUD événements + menu contextuel | 130 |
| `views/core/event_dialog.py` | Dialogue édition événement | 87 |
| `views/dialogs/event_generator.py` | Wizard génération événement | ~480 |
| `views/dialogs/timetable_editor.py` | Éditeur emploi du temps | 209 |

## EventGenerator (réécrit 07/07)

**Wizard séquentiel — 3 modes :**

```
Étape 1 : [Absence journée] [Retard] [Événements]  ← 3 boutons, rien d'autre
```

- **Absence** → nature (Maladie, Accident, Vacances, etc.) → badge rouge `✕ Absence > Maladie`
- **Retard** → durée (5mn / 10min / 15min / 30min / 45min / 01h00) → badge tertiaire `⏱ Retard > 15 min`
- **Événements** → Lieu → [si salle de cours] Matières → Types hiérarchiques (Bureau BI > Violence > Auteur, etc.) → badge primary

**Breadcrumb** cumulatif cliquable : `Événements > Classe > Bureau BI > Violence > Auteur`  
Chaque segment est cliquable pour revenir à cette étape.

**Espace unique** : le même card est réinitialisé à chaque étape (pas de cartes empilées).  
`adjustSize()` appelé pour éviter les déformations.

## LarcCommon/theme.py — Unification palettes

`_LarcM3Colors` mappe `theme_manager.palette` → propriétés M3 :
- `primary` / `on_primary` / `primary_container`
- `secondary` / `on_secondary`
- `secondary_container` → `primary_container` (évite le vert pastel)
- `on_secondary_container` → `text_strong` (texte lisible)
- `error` / `on_error` / `surface` / `on_surface` / `outline` etc.

`theme_manager.phi_colors` = accès direct aux couleurs unifiées.

## Icônes MD3 (larccommon/icons.py)

40 icônes : `light_mode`, `dark_mode`, `contrast`, `tonality`, `refresh`, `add`, `arrow_back`, `close`, `check`, `save`, `delete`, `edit`, `person`, `settings`, `menu`, `event`, `timer`, `calendar_today`, `schedule`, `cloud`, `wifi`, `wifi_off`, `warning`, `school`, `home`, `search`, `logout`, `filter_list`, `visibility`, `location_on`, `subject`, `description`, `bolt`, `lock`, `check_circle`, `cancel`, `sync`, `info`, `error`.

Usage : `md3_icon('refresh', color=p.primary, size=18)` → retourne `QIcon`
Taille recommandée : `theme_manager.image.icon_btn` (18px) pour boutons/menus, `icon_large` (32px) pour grands boutons.

## DB

- PostgreSQL: `127.0.0.1:5432` (Intranet) dbname=NewLarcDB user=postgres password=postgres
- Supabase: `aws-1-eu-north-1.pooler.supabase.com:6543` user=postgres.crvyxfsuvwqxzlhsfbwq password=Maat@-+2026
- Tables clés : `student_event` (INSERT-only), `larcauth_type_event` (27 lignes, 4 catégories), `larcauth_lieu` (lieux)
- `autocommit = True`
- Terme actif : `larcauth_academicyear.current_term_number`
- `larcauth_type_event` IDs : 100-107 (Bureau BI), 200-204 (Médical), 300-306 (Sortie), 400-406 (Suivi)
- Fichier SQL versionné : `LarcSuperviseur/sql/type_event_data.sql`

## User roles

SUPERVISEUR (write), COORD (write + validate), ADMIN (full).
Columns: `type_supervisor`, `type_coordonator`, `is_adm`.

## Tracing

- `common/trace.py` : fonction `trace(msg)` qui écrit dans `trace.log`
- Activation : créer `trace.log` (fichier vide) à la racine du projet
- Désactivation : supprimer `trace.log`
- Utilisation : `from LarcSuperviseur.common.trace import trace; trace("mon message")`

## Internationalisation (i18n)

- Système : `larccommon/l10n/` — `Translator` + fichiers `fr.json` / `en.json`
- Clés : `prefix.section.key` (ex: `kpi.total`, `history.title`, `student.contact.email`)
- Activation : variable d'env `LARC_LANG=fr` ou `LARC_LANG=en`
- Initialisation : dans `login.py` via `Translator.instance(lang).load_dir(Translator.l10n_dir())`
- Usage dans le code : `from larccommon.l10n import _` puis `_("key")`
- 17 vues traduites (LarcSuperviseur + LarcSecretaire)
- Test : `LarcSuperviseur/tools/test_i18n.py`
- Gestionnaire : `LarcSuperviseur/tools/i18n_manager.py` (status, missing, unused, add, search, sync, export)

## DB notes

- `student_event`: INSERT-only temporal traces
- `event_type`: hierarchical paths like "Bureau BI > Violence > Auteur"
- Old keywords (`absence`, `exit`) still work via `ILIKE`
- **`ILIKE 'Absence%'` ajouté** dans les 7 requêtes stats pour les nouveaux types `Absence > *`
- `autocommit = True` on all connections
- Table `larcauth_type_event`: IDs 100-499, 4+ categories, fichier versionné dans `sql/type_event_data.sql`
- **Terme actif** : défini par l'admin dans `larcauth_academicyear.current_term_number`, PAS par les dates
  (`start_date`/`end_date` de `larcauth_term` servent de cadre indicatif)
- `_load_active_term()` utilise maintenant `academicyear.current_term_number` + `fk_language = 2`

## État actuel (07/07/2026)

✅ **Terminé** :
- EventGenerator wizard complet (3 modes + breadcrumb + matières conditionnelles)
- Icônes MD3 intégrées dans top_bar, menus contextuels, main_window
- `theme_manager.phi_theme` unifié (plus de violet M3 par défaut)
- 25 wrappers M3 dans `phibuilder/widgets/` — **plus d'imports PySide6.QtWidgets dans les vues**
- `ImageScale` centralisé dans `larccommon/theme.py`
- DB type_event restaurée et versionnée (Intranet + Supabase)
- **i18n** : 662 clés dans `fr.json`/`en.json`, 17 vues traduites (LarcSuperviseur + LarcSecretaire)
- Test i18n : `tools/test_i18n.py`
- **Gestionnaire i18n** : `tools/i18n_manager.py` (status, missing, unused, add, search, sync, export)
- AGENTS.md complet à `C:\Projets\LarcSuperviseur\AGENTS.md`

⚠ **Problèmes connus** :
- `student_detail.py` ligne 226 : f-string avec backslash (Python 3.11 limitation, pré-existant)
- LarcHub pas encore traduit (vues login.py, hub_window.py)
- 95 clés inutilisées dans les JSON (clés prévisionnelles pour d'autres apps)

## Commandes utiles

```bash
cd C:\Projets
pip install -e LarcCommon          # si larccommon/phibuilder changent
set LARC_LANG=fr
python -m LarcSuperviseur          # Supervision
python -m LarcSecretaire           # Secrétariat
python -m LarcHub                  # Hub
python -m LarcDesign               # Designer (i18n, thèmes, rôles, logs, types, lieux)
python -m LarcSuperviseur.tools.show_icons  # Aperçu icônes MD3
```


## eLarcProfPy — Architecture (09/07/2026)

App desktop pour professeurs : notes, évaluations, synchronisation device↔serveur.
SQLite locale (`elarc.db`) + psycopg2 PostgreSQL (Intranet/Cloud).
PySide6 widgets directs + QSS via `_STYLE` + Fibonacci via `phi_theme.spacing`.
**Nom affiché** : LarcProf.

| Fichier | Rôle | Lignes |
|---|---|---|
| `main.py` | Point d'entrée + modes CLI (`--mode4`, `--test-create-db`) | 137 |
| `views/login.py` | Login 4 onglets (Intranet/Cloud/PIN/Nouvelle instance) + i18n | ~1180 |
| `views/home_window.py` | Dashboard intermédiaire : profil, synchro, boutons PEI/DP | ~650 |
| `views/main_window.py` | Espace de travail : top bar + grille élèves × notes | ~1438 |
| `views/eval_manager.py` | Gestionnaire d'évaluations (non-modal) | 431 |
| `views/password.py` | ChangePinDialog + ChangePasswordDialog | — |
| `common/theme.py` | ThemeManager local + `phi_theme` (Theme phibuilder unifié) | ~370 |
| `common/database.py` | Database (PostgreSQL Intranet/Cloud + SQLite) | 203 |
| `common/session.py` | UserRole, ConnMode, AuthResult, Session | 82 |
| `common/sync.py` | SyncManager (shadow-table _ref, diff cellule, pull/push) | 489 |
| `common/sqlite_init.py` | SQLiteInit (DDL, seed, take_teacher_data, migrations) | 793 |
| `common/auth.py` | AuthManager (Intranet) + OAuth2Manager (Google PKCE) | — |
| `common/network.py` | detect_network() shim → larccommon | — |
| `common/logger.py` | log() shim → larccommon | — |
| `common/grid_config.py` | GridConfig loader (couleurs notes, largeurs colonnes) | — |

### HomeWindow — Dashboard

Écran intermédiaire entre login et espace de travail. Divisé en 2 colonnes :

**Gauche** :
- Carte Profil : nom, email, rôle, année, trimestre, nb classes-matières, nb élèves
- Indicateurs connexion : `Intranet : ●/○`, `Cloud : ●/○`, `Hors connexion`
- Carte Synchro : date dernière sync, source, compteur modifs non synchronisées (détail par table), bouton **Synchroniser**

**Droite** — boutons conditionnels selon le profil du prof :
- **Section PEI** (visible si prof enseigne PEI/MYP) :
  - Unité de groupes de matières → `college_notes_0` (ex-MainWindow)
  - Unités interdisciplinaires → `college_notes_opt1`
  - Projet Personnel → `college_notes_opt2`
  - **Mes classes PEI** → `colleges_eleves` (visible seulement si serveur connecté — Intranet ou Cloud)
- **Section DP** (visible si prof enseigne DP/DPFr/DPEn) :
  - Unité de groupes de matières → `lycee_notes_0`
  - TDC → `lycee_notes_opt2`
  - CAS → `lycee_notes_opt3`
  - Mémoire → `lycee_notes_opt1`
  - **Mes classes DP** → `lycee_eleves` (visible seulement si serveur connecté)
- **Professeur principal** (notes/commentaires, utilise SQLite) :
  - PEI → `college_bulletin`
  - DP → `lycee_bulletin`
- **Déconnexion**

`_detect_programs()` interroge les CTS → classroom → level → program pour savoir PEI/DP.

#### Visibilité individuelle des boutons (`_detect_button_visibility`)

| Bouton | Table | Condition |
|---|---|---|
| `pei_grp_matieres` | `larcauth_classroom_termsubject` | prof, trim, enabled=1, `fk_program_id IN (12,22)` |
| `pei_interdisc` | `larcauth_classroom_termothersubject` | prof, trim, enabled=1, `fk_program_id IN (12,22)`, `unit_multisubjects=1` |
| `pei_pp` | `larcauth_classroom_termothersubject` | prof, trim, enabled=1, `fk_program_id IN (12,22)`, label LIKE `Personal%`/`Projet%` |
| `pei_mes_classes` | = pei_grp_matieres **+ serveur connecté** | |
| `dp_grp_matieres` | `larcauth_classroom_termsubject` | prof, trim, enabled=1, `fk_program_id IN (13,23)` |
| `dp_tdc` | `larcauth_classroom_termothersubject` | prof, trim, enabled=1, label LIKE `Th%` |
| `dp_cas` | `larcauth_classroom_termothersubject` | prof, trim, enabled=1, label LIKE `Cr%` |
| `dp_memoire` | `larcauth_classroom_termothersubject` | prof, trim, enabled=1, label LIKE `Mé%`/`Ext%` |
| `dp_mes_classes` | = dp_grp_matieres **+ serveur connecté** | |
| Professeur principal | `larcauth_classroom` | `fk_headteacher_id = prof` |

### Mapping boutons → vues cibles

```python
_BTN_VIEW = {
    'pei_grp_matieres': 'college_notes_0',
    'pei_interdisc':     'college_notes_opt1',
    'pei_pp':            'college_notes_opt2',
    'pei_mes_classes':   'colleges_eleves',
    'dp_grp_matieres':   'lycee_notes_0',
    'dp_memoire':        'lycee_notes_opt1',
    'dp_tdc':            'lycee_notes_opt2',
    'dp_cas':            'lycee_notes_opt3',
    'dp_mes_classes':    'lycee_eleves',
    'pei_prof_principal':'college_bulletin',
    'dp_prof_principal': 'lycee_bulletin',
}
```

- `colleges_eleves` / `lycee_eleves` : connexion serveur directe (PostgreSQL), pas SQLite. Fonctionnement simplifié LarcSuperviseur, limité aux classes du prof.
- `main_window.py` → renommé `college_notes_0` (titre fenêtre : « LarcProf — College Notes »).

### Login — 4 onglets + i18n

- Onglets : Intranet, Cloud, Hors connexion (PIN), Nouvelle instance
- Style : `_STYLE` property + QSS classes (`.btn-primary`, `.btn-google`, `.btn-pin`, `.btn-create`, `.panel`, `.section-title`, etc.)
- Espacement : `self._sp(SpacingToken.XXL)` Fibonacci via `theme_manager.phi_theme.spacing`
- i18n : `Translator.instance(lang).load_dir(...)` dans `__init__`, clés `prof_login.*` dans LarcCommon
- Taille fenêtre : 480×780 (ratio 1.625 ≈ φ)

### phi_theme dans eLarcProfPy

`common/theme.py` ThemeManager expose `phi_theme` (property) :
- Construit un `PhiTheme(ThemeConfig(...))` avec `PhiScale(base_spacing=4)`
- `_M3Colors` mappe la palette eLarcProfPy → propriétés M3 (primary, surface, error, outline, etc.)
- Reset automatique au `set_active()`
- Utilisé pour `spacing.spacing(SpacingToken.XXL)` dans login et home_window

### i18n eLarcProfPy

- Initialisation : `Translator.instance(lang).load_dir(Translator.l10n_dir())` dans `LoginWindow.__init__`
- Clés centralisées dans `LarcCommon/larccommon/l10n/fr.json` et `en.json`
- Préfixe `prof_login.*` pour les clés spécifiques (18 clés) :
  `title`, `subtitle`, `tab_pin`, `tab_new`, `pin_title`, `pin_placeholder`, `pin_note`,
  `connect_pin`, `change_pin`, `change_password`, `new_title`, `new_info`, `new_dest`,
  `create_instance`, `info_cloud`, `status.internet`, `status.offline`
- Réutilisation des clés `login.*` existantes : `tab_intranet`, `tab_cloud`, `email_placeholder`,
  `password_placeholder`, `connect_intranet`, `connect_google`, `error.required`, `error.auth_failed`,
  `status.intranet`, `status.cloud`
- Attention : ne pas utiliser `_` comme variable throwaway (écrase la fonction i18n)
  → utiliser `_outer`, `_ignored` à la place

## Mise à jour 10/07/2026

✅ **Terminé** :
- **design_system.py** : singleton `ds` avec tous les tokens dynamiques (Fibonacci, espacements, hauteurs, bordures, couleurs, QSS helpers, golden ratio)
- **LarcSecretaire Design System refactor** : student_form (M3Card identity/address/parents), parent_manager (ParentEditDialog + ParentManager), supervisor_panel (52px buttons), dossier_panel, password, login
- **phi_theme** déployé partout : `theme_manager.phi_theme` remplace `phibuilder.theme if ... else None`
- **PreferencesDialog** partagé dans LarcCommon (langue, thème, taille vignettes)
- **i18n** : +18 clés prof_login, +20 clés profile, +2 clés menu (topbar.my_profile, sec_main.preferences)
- **AGENTS.md** : section Design System complète + audit padding/margin + règles icônes + règles padding champs
- **Pushed** : LarcCommon, LarcSecretaire, LarcSuperviseur, LarcProf

🚧 **Restant LarcSecretaire** :
- ~72 hardcodings restants (padding QSS, setSpacing, etc.) — priorité basse, UI fonctionnelle
- Fichier de référence : `parent_manager.py` → 0 hardcoded

## Mise à jour 09/07/2026

✅ **Terminé eLarcProfPy** :
- **HomeWindow** : dashboard intermédiaire login→notes avec profil, synchro, boutons PEI/DP conditionnels
- **Login reconstruit** : QSS classes + Fibonacci + i18n 4 onglets
- **phi_theme** ajouté au ThemeManager local (spacing Fibonacci + couleurs M3)
- **Boutons Mes classes PEI/DP** : visibles seulement si serveur connecté (Intranet/Cloud), invisibles en Offline
- **Bouton Professeur principal** : accès notes/commentaires via SQLite
- **Indicateurs connexion** dans la carte Profil (Intranet/Cloud ●/○)
- **i18n** : 18 clés `prof_login.*` ajoutées dans LarcCommon fr.json/en.json
- **Renommage** : "LarcProf" (ex-eLarcProf) dans tous les titres de fenêtres

🚧 **À faire** :
- Brancher larccommon/login.py dans les 3 apps (LarcSuperviseur, LarcSecretaire, LarcHub)
- Brancher M3SidebarNav dans StudentEditDialog
- Algorithme de visibilité individuelle des boutons PEI/DP (`_detect_button_visibility`)
- Vue "Mes classes PEI/DP" (fonctionnement simplifié LarcSuperviseur, connexion serveur directe)
- Vue "Professeur principal" (notes et commentaires, SQLite)

## Mise a jour 08/07/2026

✅ **Termine** :
- **Themes unifies** : 1 seul ThemeManager dans larccommon/theme.py (4 themes)
- **QssHelper** : 14 generateurs QSS partages
- **Login harmonise** : golden ratio, force toggle, tabs auto
- **StudentEditDialog** : sidebar verticale + QStackedWidget + Fibonacci
- **DossierPanel** : sections M3 + table triee + fichiers par entree + apercu
- **StudentDetail** : composant reutilisable, KPIs + events/charts cote a cote
- **CI** : ruff + black + pre-commit + GitHub Actions (6 repos)
- **Composants** : FileViewer, FilePanel, FileResolver, TableSettings, M3SidebarNav, M3ChipBar
- **Tests** : 19 tests (FileResolver, TableSettings, FileViewer, FilePanel)
- **i18n** : 551/551 cles completes
- **Preferences** : larcauth_config DB
- **EventGenerator** : types depuis larcauth_type_status (DB, filtre langue)
- **Login partage** : larccommon/login.py (a brancher)

🚧 **A faire** :
- Brancher larccommon/login.py dans les 3 apps
- Brancher M3SidebarNav dans StudentEditDialog

⚠ **Problemes connus** :
- ruff supprime des imports (restaures manuellement)
- config.ini dans .gitignore



✅ **Termine** :
- **Themes unifies** : 1 seul ThemeManager dans larccommon/theme.py (4 themes)
- **QssHelper** : 14 generateurs QSS partages
- **Login harmonise** : golden ratio, force toggle, tabs auto
- **StudentEditDialog** : sidebar verticale + QStackedWidget + Fibonacci
- **DossierPanel** : sections M3 + table triee + fichiers par entree + apercu
- **StudentDetail** : composant reutilisable, KPIs + events/charts cote a cote
- **CI** : ruff + black + pre-commit + GitHub Actions (6 repos)
- **Composants** : FileViewer, FilePanel, FileResolver, TableSettings, M3SidebarNav, M3ChipBar
- **Tests** : 19 tests (FileResolver, TableSettings, FileViewer, FilePanel)
- **i18n** : 551/551 cles completes
- **Preferences** : larcauth_config DB
- **EventGenerator** : types depuis larcauth_type_status (DB, filtre langue)
- **Login partage** : larccommon/login.py (a brancher)

🚧 **A faire** :
- Brancher larccommon/login.py dans les 3 apps
- Brancher M3SidebarNav dans StudentEditDialog

⚠ **Problemes connus** :
- ruff supprime des imports (restaures manuellement)
- config.ini dans .gitignore

## Mise a jour 08/07/2026 (soir)

✅ **LarcSecretaire harmonise avec LarcSuperviseur** :
- **Design unifie** : QWidgets + QSS (QPushButton/QLabel/QFrame) au lieu de M3 widgets
- **Login partage** : larccommon/login.py utilise par LarcSecretaire (callbacks on_intranet_login, on_cloud_login, on_success)
- **Sidebar** : boutons #section_btn + #class_btn via QssHelper, identique a LarcSuperviseur
- **Top bar** : icone theme M3 dynamique, plus d'emojis
- **Dashboard** : QFrame + QLabel + QTableWidget comme LarcSuperviseur
- **Couleurs** : suppression de 	heme_manager.bind(app) → plus de violet M3
- **Preferences** : 	heme_pref charge depuis DB au demarrage
- **i18n** : Translator initialise dans main.py, toggle FR/EN dans menu profil

🚧 **Login partage** : larccommon/login.py avec callbacks on_intranet_login, on_cloud_login, 	itle_prefix, subtitle. LarcSuperviseur pas encore branche.

⚠ **LarcSecretaire** : dossier_panel.py encore en M3 widgets (non converti).

## Mise à jour 10/07/2026

✅ **Terminé (LarcProf)** :
- **Gradient pastel** notes : rouge(0)→blanc(milieu)→vert(max), visible via ColorItem + ColorDelegate
- **Nature dans top bar** : remplace le doublon label DB par la nature réelle
- **Critères par évaluation** : seules les colonnes des critères activés pour chaque éval sont affichées
- **EditTriggers Excel-like** : `AnyKeyPressed`, clic simple, flèches de navigation
- **Tri Nom/Prénom** : clic sur l'en-tête bascule entre "Nom Prénom" et "Prénom Nom"
- **Cellules centrées** + **padding** via tokens `ds`
- **Boutons adaptatifs** : "Enregistrer" (hors ligne) vs "Synchroniser" (en ligne)
- **Sauvegarde locale** : corrigée — `learner_has_termsubject_ptr_id` au lieu de `fk_student_id`
- **Fenêtre maximisée** : `showMaximized()` au lancement depuis home_window
- **Sync perf** : commit unique par table (plus par cellule), log verbeux retiré
- **EvalManager** : `take_teacher_data` ajouté dans `_on_create` (base vide corrigée)
- **sync_state** : migration + non-bloquant (ne rollback plus la transaction)
- **Traces [INIT]** : visibilité sur la création/peuplement SQLite
- **Disconnect warning** : connecté une fois dans `_build_students_grid`, plus de disconnect

🚧 **Restant** :
- Sync `pull_push` lent sur grosses tables (>10K lignes) — diff `compute_cell_diff` lit toutes les lignes × colonnes
- EvalManager ne fait que UPDATE (pas INSERT) — création d'évaluation nécessite le serveur
