# AGENTS.md — Projets Larc (Mise à jour 07/07/2026)

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
