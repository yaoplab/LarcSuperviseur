# Dialogs

## EventGenerator (`views/dialogs/event_generator.py`)

Dialog modal de création d'événement.

- 497 lignes, 21 méthodes
- Reçoit un `student_id`
- Arbre de sélection du type d'événement :
  - Catégories N1 (Bureau BI, Médical, Sortie, Suivi)
  - Sous-catégories N2 et N3
  - Affichage en grille de boutons (QGridLayout)
- Champs : lieu (détecté depuis la classe), matière, note, source
- `get_data() → dict` retourne les données après validation

## TimetableEditor (`views/dialogs/timetable_editor.py`)

Éditeur d'emploi du temps d'une classe.

- 263 lignes
- Contient : `TimeSlotGrid(QWidget)` + `TimetableEditor(QDialog)`
- Grille modifiable : Heures × 5 jours
- ComboBox de matières pour chaque créneau
- `_save()` → UPDATE `classroom_has_timeperiod`
