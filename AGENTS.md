# AGENTS.md — LarcSuperviseur V1.1

## What this is

PySide6 (Qt6) desktop app for student attendance/event supervision.
Direct psycopg2 PostgreSQL — no ORM, no REST API.
Windows-only. French UI.

## How to run

```bash
# From C:\Projets (parent dir), NOT inside LarcSuperviseur/
python -m LarcSuperviseur
```

`main.py` / `__main__.py` add parent dir to `sys.path`.

## Critical: sibling dependency

`eLarcProfPy/` at `C:\Projets\eLarcProfPy/` provides `config.ini` (DB creds).
Without it, login fails. `_find_cfg()` searches `../config.ini` then `../../eLarcProfPy/config.ini`.

## Architecture (V1.1 — 18 juin 2026)

| Path | Role | Lines |
|---|---|---|
| `views/main_window.py` | Orchestrator: top bar, signal wiring | 310 |
| `views/panels/sidebar.py` | Left nav: programs + classes | 150 |
| `views/panels/group_panel.py` | Group stats: KPIs, charts, history | 464 |
| `views/panels/class_panel.py` | Student cards grid | 72 |
| `views/panels/student_detail.py` | Student detail: photo, info, events | 415 |
| `views/core/data_loader.py` | ALL DB queries (32 methods) | 682 |
| `views/core/event_actions.py` | Event CRUD | 117 |
| `views/core/event_dialog.py` | Event edit dialog | 87 |
| `views/core/cardsList/` | StudentCard, grid, avatar, config | ~200 |
| `views/dialogs/event_generator.py` | Event creation dialog | 497 |
| `views/dialogs/timetable_editor.py` | Timetable editor | 263 |
| `common/` | Shared infra (to migrate to LarcCommon) | — |

## Refactoring done today

- `main_window.py`: 2573 → 310 lines (EventGenerator + TimetableEditor + TimeSlotGrid extracted)
- `functions/` deleted → migrated to `views/core/cardsList/`
- `common/event_helpers.py` created (was 3 copies)
- `views/core/event_dialog.py` (shared edit dialog, was 2 copies)
- EventActions used by both group_panel & student_detail (SQL inline removed)
- Old docs archived as `LarcSuperviseur V0.1.zip`
- New docs in `docs/`, algorithms in `algo/`

## Rules

- No test framework, no linting — run the app to verify
- Imports: `LarcSuperviseur.*` package paths only
- Panels: never write SQL directly, use DataLoader / EventActions
- `event_icon()` / `event_color()` in `common/event_helpers.py` (single source)
- Photos: `photos/{sid}.png`, cached in `photos/cache/`
- Refresh timer: 30s in MainWindow

## DB notes

- `student_event`: INSERT-only temporal traces
- `event_type`: hierarchical paths like "Bureau BI > Violence > Auteur" (27 rows, IDs 100-499)
- Old keywords (`absence`, `exit`) still work via `ILIKE`
- `autocommit = True` on all connections
- Table `larcauth_type_event`: 27 lignes (IDs 100-499, 4 categories). Fichier SQL perdu — à re-générer si restauration DB
- Après restauration DB: `python -m LarcSuperviseur.sql.run_ddl`

## User roles

SUPERVISEUR (write), COORD (write + validate), ADMIN (full).
Columns: `type_supervisor`, `type_coordonator`, `is_adm`.

## Next

- Create `LarcCommon` shared package (with eLarcProfPy, LarcSecretaire):
  database, network, logger, session, auth, theme, photos, app_config, event_helpers, audit, mail
