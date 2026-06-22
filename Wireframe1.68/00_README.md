# Wireframe 1.68 — Analyse d'application des principes Φ Fibonacci

## Principe directeur

Interface structurée par le Nombre d'Or (Φ ≈ 1,618) et la Suite de Fibonacci (8, 13, 21, 34, 55, 89, 144…) pour une ergonomie naturelle, stable et confortable.

## Principes de design

1. **Rectangle d'Or** — Fenêtre dont L/l = Φ (proportion instinctivement équilibrée)
2. **Division Harmonique 62/38** — Espace divisé en deux zones asymétriques (grande 62%, petite 38%)
3. **Suite de Fibonacci** — Échelle de dimensions cohérente (8, 13, 21, 34, 55, 89, 144…)
4. **Point Focal / Spirale Dorée** — Bouton d'action aligné à droite, largeur = 61,8%
5. **Whitespace** — Marges et espacements respirant grâce aux écarts fibonacciens

## Écrans analysés

| # | Écran | Classe | Fichier |
|---|---|---|---|
| 1 | **LoginWindow** | `LoginWindow` | `views/login.py` |
| 2 | **Carte Élève** | `StudentCard` | `views/main_window.py:62` |
| 3 | **Grille Emploi du Temps** | `TimeSlotGrid` | `views/main_window.py:193` |
| 4 | **Génération d'Événement** | `EventGenerator` | `views/main_window.py:306` |
| 5 | **Fenêtre Principale** | `MainWindow` | `views/main_window.py:826` |
| 6 | **Éditeur EDT** | `TimetableEditor` | `views/main_window.py:2495` |
