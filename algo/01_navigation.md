# Navigation

## Principe

`MainWindow` contient un `QStackedWidget` à 3 pages :
- Index 0 : `GroupPanel` (statistiques groupe)
- Index 1 : `ClassPanel` (grille de cartes)
- Index 2 : `StudentDetail` (détail élève)

```
Sidebar.signaux
  │
  ├── class_selected(class_id, label)
  │   → MainWindow._on_class_selected()
  │     → content_stack.setCurrentIndex(1)
  │     → class_panel.load(class_id)
  │
  ├── group_selected(mode)
  │   → MainWindow._on_group_selected()
  │     → content_stack.setCurrentIndex(0)
  │     → group_panel.load(mode)
  │
  └── all_selected()
      → MainWindow._on_group_selected('grp_all')
```

## Changement d'état

```python
_current_group_mode    # 'grp_all', 'grp_college', 'grp_lycee', 'grp_pei', 'class'
_current_class_id      # int (0 si mode groupe)
_current_class_label   # str
_selected_student_id   # int (0 si aucun)
```

## Refresh

`refresh_all()` vérifie `_current_group_mode` et recharge la vue active.
Appelé par le bouton ⟳ et le timer 30s.
