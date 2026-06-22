# TimeSlotGrid — Analyse Φ Fibonacci

**Fichier :** `views/main_window.py:193` — **Taille :** contenu dans un `QGridLayout` — **Statut :** 🔲 Non implémenté

---

## 1. Principes utilisables aujourd'hui : 3/5

| # | Principe | Applicable ? | État actuel |
|---|---|---|---|
| 1 | Rectangle d'Or | ❌ | Widget intégré, pas de fenêtre propre |
| 2 | Division 62/38 | ❌ | Structure en grille, pas de split vertical |
| 3 | Suite de Fibonacci | ✅ | Police 10px, 9px (non-Fibonacci). Espacements 1px (bien trop serré) |
| 4 | Point Focal / Spirale | ❌ | Pas de bouton focal unique |
| 5 | Whitespace | ✅ | Besoin d'espacement entre les créneaux |

## 2. Détail par principe

### Suite de Fibonacci (3)
- Actuel : `setSpacing(1)`, police 9-10px, padding 2-4px
- Cible Fibonacci :
  - Espacement grille : 8px (au lieu de 1px)
  - Police en-têtes : 13px (au lieu de 10px)
  - Police boutons créneaux : 13px
  - `border-radius` : 8px (au lieu de 0)
  - Hauteur minimale des cellules : 55px (confort tactile)
  - Padding interne : 8px
- **Éléments :** `QGridLayout`, `QLabel` en-têtes, `QPushButton` créneaux
- **Effet utilisateur :** créneaux plus grands et lisibles, espacement confortable, cibles tactiles plus grandes

### Whitespace (5)
- Actuel : `setSpacing(1)` = quasi aucun espace
- Cible : 8px entre colonnes, 8px entre lignes
- **Éléments :** grille entière
- **Effet utilisateur :** les créneaux "respirent", l'œil distingue facilement chaque colonne

## 3. Relation avec Material Design 3

- **MD3 Data Tables** : recommandent des lignes de 52-72px de hauteur, espacement 16px entre cellules
- **Divergence** : l'espacement 1px actuel est contraire à MD3
- **Ajustement MD3** : utiliser 8px (Fibonacci) est un bon compromis (MD3 recommande 16px, mais l'espace est limité dans une grille horaire)

## 4. Proposition

| Élément | Actuel | Φ-Fibonacci |
|---|---|---|
| `grid.setSpacing` | 1px | 8px |
| Police en-têtes | 10px | 13px |
| Police boutons | 9px | 13px |
| Bouton "Ajouter événement" | police 9px, padding 4px | hauteur 55px, police 13px |
| `border-radius` | 0px | 8px |
| Hauteur ligne | auto | 55px (Fibonacci) |
