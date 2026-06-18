# Flux des données

## Principe

```
PostgreSQL ← DataLoader → Panel (UI)
                  ↑
            EventActions (CRUD)
```

## Règles

- **DataLoader** : méthodes pures, pas d'import PySide6
- **EventActions** : CRUD uniquement, pas d'UI
- **Panels** : appellent DataLoader, affichent les résultats
- Les panels ne font **jamais** de SQL directement (sauf group_panel pour l'edit dialog legacy, à migrer)

## Exemple : chargement d'une classe

```python
# ClassPanel.load(class_id)
students = self._loader.get_students(class_id)           # → list[dict]
student_ids = [s['id'] for s in students]
event_stats = self._loader.get_student_event_stats(
    student_ids, date_from, date_to)                     # → dict {sid: {exit, presence}}
fill_cards_grid(self._grid_layout, self._scroll,
                students, event_stats, self._on_card_click)
```

## Exemple : statistiques groupe

```python
# GroupPanel.load(mode, date_from, date_to)
rows = self._loader.get_class_stats(mode, date_from, date_to)          # KPIs + tableau
trend = self._loader.get_attendance_trend(mode, date_from, date_to)   # chart tendance
rate = self._loader.get_presence_rate(mode, date_from, date_to)       # donut
history = self._loader.get_event_history(mode, date_from, date_to,
    class_id=sel_class, type_filter=sel_type)                          # tableau historique
```
