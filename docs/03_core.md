# Core — Logique métier

## DataLoader (`views/core/data_loader.py`)

Toutes les requêtes SQL en un seul endroit.

- 32 méthodes, 682 lignes
- Aucune UI — retourne des `dict` / `list[dict]` / `int` / `str`
- Se connecte via `db.server_conn`
- Méthodes organisées par domaine :

| Section | Méthodes |
|---|---|
| Terme | `get_active_term()`, `get_term_id()`, `get_current_term_label()` |
| Programmes/Classes | `get_programs()` , `get_classes()`, `get_all_classrooms()` |
| Statistiques groupe | `get_class_stats()`, `get_attendance_trend()`, `get_presence_rate()` |
| Historique | `get_all_event_types()`, `get_event_history()` |
| Élèves | `get_students()`, `get_student_event_stats()`, `get_student_info()`, `get_student_kpis()`, `get_student_absence_trend()`, `get_student_events()` |
| Événements | `insert_event()`, `get_event_details()`, `check_event_validated()`, `toggle_event_validation()`, `update_event()`, `delete_event()` |
| Lieux/Matières | `get_locations()`, `get_classroom_subjects()` |
| Types événements | `get_event_types_tree()` |
| Emploi du temps | `get_classroom_timeperiods()`, `get_timeperiods()`, `get_classroom_timetable()`, `get_available_subjects()`, `update_timetable_slot()` |

## EventActions (`views/core/event_actions.py`)

CRUD sur `student_event`.

- `get_event_by_id(event_id) → dict`
- `edit_event(event_id, data) → bool`
- `toggle_validation(event_id, validate: bool) → bool`
- `delete_event(event_id) → bool`

## EventEditDialog (`views/core/event_dialog.py`)

Dialog modal d'édition d'un événement.

- Réutilisé par GroupPanel et StudentDetail
- Charge l'événement depuis la DB
- Affiche infos élève + type + note
- ComboBox des types disponibles, TextEdit pour la note
- `exec()` → `QDialog.Accepted` si sauvegardé

## cardsList (`views/core/cardsList/`)

Composants de la grille de cartes élèves.

| Fichier | Rôle |
|---|---|
| `config.py` | `CardConfig` dataclass (144×233, Fibonacci) |
| `avatar.py` | `make_avatar()` — avatar circulaire avec initiales |
| `card.py` | `StudentCard(QFrame)` — carte cliquable 144×233 |
| `grid.py` | `fill_cards_grid()` — remplit un QGridLayout |
