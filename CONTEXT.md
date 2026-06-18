# LarcSuperviseur — V1.1

Application PySide6 de supervision des présences/événements élèves.

## Architecture actuelle (18 juin 2026)

`views/main_window.py`: 310 lignes (orchestrateur)
Plus aucun fichier > 700 lignes.

### 4 systèmes indépendants

| Système | Path | Responsabilité |
|---|---|---|
| **Panels** | `views/panels/` | UI: Sidebar, GroupPanel, ClassPanel, StudentDetail |
| **Core** | `views/core/` | Logique: DataLoader, EventActions, EventEditDialog, cardsList |
| **Dialogs** | `views/dialogs/` | Modales: EventGenerator, TimetableEditor |
| **Common** | `common/` | Infrastructure (en attente LarcCommon) |

### Refactoring V1.1 (aujourd'hui)

- `main_window.py`: 2573 → 310 lignes
- `functions/` supprimé, migré dans `views/core/cardsList/`
- `common/event_helpers.py` mutualisé (3 copies supprimées)
- `EventEditDialog` extrait, réutilisé par GroupPanel + StudentDetail
- `EventActions` utilisé par les 2 panels (fini le SQL inline dupliqué)
- Doc archivée V0.1 → `LarcSuperviseur V0.1.zip`

### Dépendance

- `config.ini` dans `../../eLarcProfPy/config.ini`
- PostgreSQL `NewLarcDB`

### Prochaine étape

Création de `LarcCommon` (package partagé avec eLarcProfPy et LarcSecretaire) pour mutualiser: database, network, logger, session, auth, theme, photos, event_helpers.

### Notes

- Docs architecture: `docs/`
- Algorithmes: `algo/`
- Photos: `photos/{student_id}.png`
- Refresh auto: 30s
- Thèmes: Material Design 3 (Light/Dark/Contrast)
