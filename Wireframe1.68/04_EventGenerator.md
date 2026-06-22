# EventGenerator — Analyse Φ Fibonacci

**Fichier :** `views/main_window.py:306` — **Taille min :** 600px large — **Statut :** 🔲 Non implémenté

---

## 1. Principes utilisables aujourd'hui : 4/5

| # | Principe | Applicable ? | État actuel |
|---|---|---|---|
| 1 | Rectangle d'Or | ✅ | Largeur = 600 → hauteur idéale Φ = 600 × 1,618 = 970px. Aujourd'hui : `setMinimumWidth(600)` sans hauteur fixe |
| 2 | Division 62/38 | ✅ | Top bar infos (38%) / Type d'événement + note + boutons (62%) |
| 3 | Suite de Fibonacci | ⚠️ Partiel | Quelques valeurs : 8px spacing, 4-6px padding, 10px police. Bcp de valeurs hors Fibonacci |
| 4 | Point Focal / Spirale | ✅ | Bouton OK (dans `QDialogButtonBox`) — mais aligné à gauche par défaut |
| 5 | Whitespace | ⚠️ Partiel | `sp = 8` partout = monotone. MD3 veut des hiérarchies d'espacement |

## 2. Détail par principe

### Rectangle d'Or (1)
- Actuel : `setMinimumWidth(600)` mais hauteur libre
- Proposition : `setFixedSize(600, 970)` pour respecter Φ
- **Éléments :** fenêtre dialog
- **Effet utilisateur :** proportions stables, pas de redimensionnement intempestif
- **Contrainte :** le `QStackedWidget` à l'intérieur (types hiérarchiques) doit garder sa flexibilité → utiliser un `setMinimumHeight` plutôt qu'un stretch

### Division Harmonique 62/38 (2)
- 38% haut : nom élève + date/lieu/matière + infos
- 62% bas : type d'événement (stacked) + note + boutons OK/Cancel
- **Éléments :** répartition verticale du `QVBoxLayout`
- **Effet utilisateur :** la zone de sélection du type d'événement (la plus complexe) a plus d'espace

### Suite de Fibonacci (3)
| Actuel | Fibonacci | Éléments |
|---|---|---|
| `sp = 8` uniforme | 8, 13, 21 selon hiérarchie | Espacements entre sections |
| `fs = 10` | 13px partout | Police labels et boutons |
| `rd = 4` | 8px | Border-radius partout |
| `padding: 6px` | 8px | Padding des champs |
| `padding: 4px` | 8px | Padding interne |
| `setMinimumHeight(64)` boutons lieu | 55px | Hauteur boutons |
| `setMinimumHeight(60)` boutons matière | 55px | Hauteur boutons |
| `setMaximumHeight(80)` note | 55px (ou 89px) | Hauteur champ note |

- **Effet utilisateur :** hiérarchie visuelle cohérente, éléments homogènes

### Point Focal / Spirale (4)
- `QDialogButtonBox` avec OK à droite (automatique sur Windows)
- Proposition : garder OK/Cancel, mais si on ajoute un bouton principal "Valider l'événement" il devrait être à droite et faire 61,8% de la largeur utile (≈ 370px sur 600)
- **Éléments :** boutons de validation
- **Effet utilisateur :** l'action finale est bien mise en évidence

### Whitespace (5)
- Actuel : `sp = 8` uniforme → pas de hiérarchie
- Proposition :
  - Entre sections majeures : 21px
  - Entre sous-sections : 13px  
  - Entre éléments proches : 8px
- **Éléments :** tous les `addSpacing(sp)`
- **Effet utilisateur :** l'œil navigue naturellement d'une section à l'autre

## 3. Relation avec Material Design 3

| Point | Actuel | MD3 | Ajustement |
|---|---|---|---|
| Dialog width | 600px | 560px recommandé | 560 serait mieux (mais 600 OK) |
| `border-radius` | 4px | 12px (large) ou 4px (small) | 8px (Fibonacci) = entre small et medium |
| Hauteur boutons | 64px | 48px | 55px (Fibonacci) = plus proche de MD3 |
| Police | 10px | 14px (body) | 13px (Fibonacci) = acceptable |

## 4. Réflexion couleurs

- Boutons des catégories d'événement : couleurs hardcodées (`#d32f2f`, `#1976d2`, etc.)
- Proposition : mapper ces couleurs sur les tokens MD3 :
  - "Bureau BI" → `error`
  - "Médical" → `tertiary`
  - "Sortie" → `secondary` (ou une couleur personnalisée)
  - "Suivi" → `primary_container`
- **Avantage :** respect du thème MD3 actif (light/dark/contrast)
- **Risque :** perte de sens sémantique si les couleurs changent avec le thème
