# AGENTS.md — LarcSuperviseur V1.2

## What this is

PySide6 (Qt6) desktop app for student attendance/event supervision.
Direct psycopg2 PostgreSQL — no ORM, no REST API.
Windows-only. Bilingual UI (FR/EN via `LARC_LANG` env var).

## How to run

```bash
# From C:\Projets (parent dir), NOT inside LarcSuperviseur/
set LARC_LANG=fr    # Français (défaut)
set LARC_LANG=en    # English
python -m LarcSuperviseur
```

Requires `LarcCommon` installed (`pip install -e C:\Projets\LarcCommon`).

## Architecture (V1.2 — 23 juin 2026)

| Path | Role | Lines |
|---|---|---|
| `views/main_window.py` | Orchestrator | ~1700 |
| `views/top_bar.py` | Top bar UI (date, réseau, thème, périodes) | 204 |
| `views/panels/sidebar.py` | Left nav: programs + classes (Fibonacci) | ~160 |
| `views/panels/group_panel.py` | Group stats: KPIs, charts, history, absents list | ~500 |
| `views/panels/class_panel.py` | Student cards grid | 90 |
| `views/panels/student_detail.py` | Student detail: photo, info, events | ~400 |
| `views/core/time_manager.py` | Centralized time state (date, period, unit) | 49 |
| `views/core/data_loader.py` | ALL DB queries (33 methods) | 752 |
| `views/core/event_actions.py` | Event CRUD | 117 |
| `views/core/event_dialog.py` | Event edit dialog | 87 |
| `views/core/cardsList/` | StudentCard, grid, avatar, config | ~200 |
| `views/dialogs/event_generator.py` | Event creation dialog (DataLoader) | 432 |
| `views/dialogs/timetable_editor.py` | Timetable editor + TimeSlotGrid (DataLoader) | 209 |
| `common/*.py` | Shims → `larccommon` package | 1 each |
| `common/trace.py` | Debug tracing to `trace.log` | 25 |

## External dependencies

- `LarcCommon` (`C:\Projets\LarcCommon/`) — `larccommon` + `phibuilder` packages
- `materialyoucolor` — color scheme engine

## Rules

- No test framework, no linting — run the app to verify
- Imports: `LarcSuperviseur.*` package paths only
- Panels: never write SQL directly, use DataLoader / EventActions
- `event_icon()` / `event_color()` in `common/event_helpers.py` (shim to `larccommon`)
- Photos: `photos/{sid}.png`, cached in `photos/cache/`
- Refresh timer: 30s in MainWindow

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
- Les 8 vues LarcSuperviseur sont traduites (~200 clés)

## DB notes

- `student_event`: INSERT-only temporal traces
- `event_type`: hierarchical paths like "Bureau BI > Violence > Auteur"
- Old keywords (`absence`, `exit`) still work via `ILIKE`
- **`ILIKE 'Absence%'` ajouté** dans les 7 requêtes stats pour les nouveaux types `Absence > *`
- `autocommit = True` on all connections
- Table `larcauth_type_event`: IDs 100-499, 4+ categories. Fichier SQL perdu
- **Terme actif** : défini par l'admin dans `larcauth_academicyear.current_term_number`, PAS par les dates
  (`start_date`/`end_date` de `larcauth_term` servent de cadre indicatif)
- `_load_active_term()` utilise maintenant `academicyear.current_term_number` + `fk_language = 2`
- Après restauration DB: `python -m LarcSuperviseur.sql.run_ddl`

## User roles

SUPERVISEUR (write), COORD (write + validate), ADMIN (full).
Columns: `type_supervisor`, `type_coordonator`, `is_adm`.

## Next

- Ajouter types « Absence justifiée > Maladie/Accident/Vacances » dans la DB (FAIT)
- Remplir l'emploi du temps T3
- Interface mobile Flutter (phase ultérieure)
- Langue préférence utilisateur en DB : stocker `fk_language` dans `larcauth_aecuser` (per user) + `larcauth_config` (global) — permettra de choisir la langue du trimestre affiché
