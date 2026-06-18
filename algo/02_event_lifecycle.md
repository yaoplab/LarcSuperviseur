# Cycle de vie d'un événement

## Création

1. `StudentDetail._on_add_event()` ou `TimeSlotGrid._open_event_dialog()`
2. `EventGenerator(student_id).exec()` → dialog modal
3. Arbre de sélection du type (N1 → N2 → N3)
4. Validation des champs requis
5. `DataLoader.insert_event(data)` → INSERT INTO student_event
6. Rechargement de la vue (`load(student_id)`)

## Visualisation

- Dans `StudentDetail` : tableau des 20 derniers
- Dans `GroupPanel` : historique avec filtres (classe, type, date)
- Icône + couleur selon le type via `event_helpers.event_icon()` / `event_color()`

## Modification

1. Clic droit → menu contextuel → Modifier
2. `EventEditDialog(event_id).exec()` → dialog modal
3. Chargement des données actuelles
4. Sauvegarde : `UPDATE student_event SET event_type, note WHERE event_id = %s`

## Validation

1. Clic droit → Valider / Dévalider
2. `EventActions.toggle_validation(event_id, validate: bool)`
3. Bascule `validated_by = user_id` ou `validated_by = NULL`
4. Réservé aux rôles COORD et ADMIN

## Suppression

1. Clic droit → Supprimer
2. Confirmation `QMessageBox.question()`
3. `EventActions.delete_event(event_id)` → DELETE FROM student_event
4. Rechargement de la vue
