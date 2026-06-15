# AGENTS.md

## What this is

PySide6 (Qt6) desktop app for student attendance/event supervision.
Direct psycopg2 connection to PostgreSQL — no REST API, no ORM, no local DB.
Windows-only target. French-language UI and code comments.

## How to run

```bash
# From the PARENT directory (C:\Projets), NOT from inside LarcSuperviseur/
python -m LarcSuperviseur
```

The package uses `LarcSuperviseur` as its import root. `main.py` and `__main__.py` both add the parent dir to `sys.path`.

## Critical: sibling project dependency

`eLarcProfPy/` must exist as a sibling directory at `C:\Projets\eLarcProfPy\`. It provides:
- `config.ini` (database credentials) — referenced by `common/database.py`, `common/network.py`, `common/auth.py`
- Auth module (`common/auth.py`) imported at runtime

Without it, login fails. The `_find_cfg()` function in `database.py`, `network.py`, and `auth.py` searches both `../config.ini` and `../../eLarcProfPy/config.ini`.

## config.ini — never commit

`config.ini` is in `.gitignore`. It holds DB credentials for:
- `IntranetDatabase` section (PostgreSQL `127.0.0.1:5432/NewLarcDB`)
- `SupabaseDatabase` section (Cloud, read-only)
- OAuth2 settings in `[OAuth2]` section

If missing, the app logs a warning and uses hardcoded defaults (localhost:5432).

## Architecture

| Path | Role |
|---|---|
| `main.py` | Entry point: QApplication + LoginWindow |
| `common/database.py` | `db` singleton — psycopg2 connections to Intranet and Cloud |
| `common/session.py` | `session` global — holds current user, role, conn_mode |
| `common/auth.py` | OAuth2 PKCE + local password auth |
| `common/network.py` | `detect_network()` → (intranet_ok, internet_ok) |
| `common/theme.py` | `theme_manager` — 3 Material Design 3 themes |
| `common/photos.py` | `get_photo_path(sid)` — local or Supabase Storage download |
| `common/app_config.py` | `app_config` — loads key/value from `larcauth_config` table |
| `views/login.py` | LoginWindow with rate limiting (5 attempts → 30s lockout) |
| `views/main_window.py` | MainWindow (~2650 lines) + EventGenerator — the entire UI |
| `sql/student_event.sql` | DDL for `student_event` table + trigger |
| `sql/run_ddl.py` | Runs DDL against Intranet DB |

## Database notes

- `student_event` is INSERT-only (temporal traces, no update/delete)
- `event_type` stores hierarchical paths like `"Bureau BI > Violence > Auteur"` from `larcauth_type_event` (27 rows, IDs 100-499)
- Old keyword values (`absence`, `exit`, etc.) still work via `ILIKE` in queries
- `agenda_day_id` is auto-resolved by trigger from `event_at` timestamp
- `autocommit = True` on all connections

## User roles

SUPERVISEUR (write), COORD (write + validate), ADMIN (full). Checked via `type_supervisor`, `type_coordonator`, `is_adm` boolean columns.

## Key conventions

- No test framework, no linting, no type checking configured — verify changes by running the app
- All imports use `LarcSuperviseur.*` package paths (not relative)
- Photos: `photos/{student_id}.png` (500×500, transparent background)
- Refresh timer: 30 seconds in MainWindow
- Theme switch rebuilds the entire stylesheet (not just palette swap)

## Gotchas

- `main_window.py` is a single ~2650-line file containing MainWindow and EventGenerator — read it in sections
- `_event_icon()` and `_event_color()` must handle both old keywords and new hierarchical paths
- The app expects to be run on a machine with network access to the PostgreSQL server at `192.168.2.90` (or configured host)
- `sql/run_ddl.py` has hardcoded path `C:\Projets\eLarcProfPy` — adjust if running elsewhere
