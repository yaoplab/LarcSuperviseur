# Panels

## Sidebar (`views/panels/sidebar.py`)

Barre de navigation latérale gauche.

- Hérite de `QScrollArea`
- Charge les programmes (PEI, MYP, DPEn, DPFr) et classes depuis la DB
- Sections cliquables : Collège / Lycée
- Boutons programme avec code couleur (PEI=primary, MYP=secondary, DP=error, DPEn=tertiary)
- Boutons classe sous chaque programme
- `class_selected(int, str)` → quand une classe est cliquée
- `group_selected(str)` → quand un programme/section est cliqué
- `all_selected()` → "Toutes les classes"
- Appelle `load_data()` qui rafraîchit depuis la DB

## GroupPanel (`views/panels/group_panel.py`)

Statistiques agrégées pour un groupe de classes.

- 4 cartes KPI : Total élèves, Présents, Absents, Sorties
- Tableau des statistiques par classe
- 4 onglets de chartes QtCharts :
  - Absences par classe (barres)
  - Sorties par classe (barres)
  - Tendance des absences (ligne, période)
  - Taux de présence (donut)
- Historique des événements (tableau filtré)
- `load(mode, date_from, date_to)` → recharge tout

## ClassPanel (`views/panels/class_panel.py`)

Grille de cartes élèves pour une classe.

- Utilise `fill_cards_grid()` depuis `core/cardsList/grid.py`
- Chaque carte = `StudentCard` (144×233 px, ratio Φ)
- `student_selected(int)` → quand on clique sur un élève
- `load(class_id)` → charge les élèves + stats
- `reflow()` → recalcule le nombre de colonnes au resize

## StudentDetail (`views/panels/student_detail.py`)

Détail complet d'un élève.

- Photo 150×150 (depuis `common/photos.py`)
- Coordonnées : nom, email, téléphones, date d'entrée
- KPIs : absences, sorties, total événements
- Tableau des 20 derniers événements (avec icônes et couleurs)
- Chart d'évolution des absences (QLineSeries, 90 jours)
- Onglet Parents (placeholder)
- `load(student_id)` → recharge tout
- `back_requested()` → signal pour retour à la grille
- `refresh_theme()` → reconstruction après changement de thème
