# Rapport i18n — Session 07/07/2026

## Objectif
Internationaliser toutes les vues de LarcSuperviseur et LarcSecretaire (FR/EN).

## Résultat

| Métrique | Valeur |
|---|---|
| Fichiers JSON | `fr.json` et `en.json` |
| Clés totales | **649** chacune |
| Vues modifiées LarcSuperviseur | 9 fichiers |
| Vues modifiées LarcSecretaire | 8 fichiers |
| Vues modifiées LarcHub | à faire (voire infra) |
| Chaînes traduites | ~550 |

## Fichiers modifiés

**LarcSuperviseur :**
- `views/login.py` — 26 remplacements
- `views/top_bar.py` — 8 remplacements
- `views/main_window.py` — 4 remplacements
- `views/panels/group_panel.py` — 25 remplacements
- `views/panels/class_panel.py` — 1 remplacement
- `views/core/event_actions.py` — 3 remplacements
- `views/core/event_dialog.py` — 7 remplacements
- `views/dialogs/event_generator.py` — 8 remplacements
- `views/dialogs/timetable_editor.py` — 9 remplacements

**LarcSecretaire :**
- `views/login.py` — ~30 remplacements
- `views/main_window.py` — ~25 remplacements
- `views/dossier_panel.py` — ~15 remplacements
- `views/notes_panel.py` — ~20 remplacements
- `views/parent_manager.py` — ~40 remplacements
- `views/password.py` — ~12 remplacements
- `views/student_form.py` — ~60 remplacements
- `views/supervisor_panel.py` — ~25 remplacements

## Couverture
- Test i18n : `LarcSuperviseur/tools/test_i18n.py` — vérifie que tous les `_('key')` existent dans fr.json et en.json
- Les seules clés manquantes sont des faux positifs (noms de modules Python détectés par la regex)
- 95 clés inutilisées dans les JSON (clés prévisionnelles ou d'autres apps)

## Restant (LarcHub)
LarcHub n'a PAS été traité car il n'importe pas `_` et ses vues (login.py, hub_window.py) utilisent des `from larccommon.l10n import _` qui existe mais les chaînes sont en dur. À faire dans une prochaine session.

## Commandes
```bash
python -m LarcSuperviseur.tools.test_i18n   # Vérifier la couverture
python -m LarcSuperviseur                    # Lancer l'app
set LARC_LANG=en && python -m LarcSuperviseur # Lancer en anglais
```
