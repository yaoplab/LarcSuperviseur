# StudentCard — Analyse Φ Fibonacci

**Fichier :** `views/main_window.py:62` — **Taille actuelle :** 160×200px — **Statut :** 🔲 Non implémenté

---

## 1. Principes utilisables aujourd'hui : 2/5

| # | Principe | Applicable ? | État actuel |
|---|---|---|---|
| 1 | Rectangle d'Or | ✅ Facile | Carte = 160×200 → ratio 1,25 (carré quasi-parfait). À passer à Φ. |
| 2 | Division 62/38 | ✅ | Photo-badge (38%) / Infos texte (62%) |
| 3 | Suite de Fibonacci | ⚠️ Partiel | `border-radius: 8px` ✅ ; police 11-13px ✅ ; pas de Fibonacci pour tailles/taille photo |
| 4 | Point Focal / Spirale | ❌ Non | Carte trop petite, pas de bouton d'action |
| 5 | Whitespace | ⚠️ Partiel | Marges 6px + spacing 4px (trop serré vs 8/13/21) |

## 2. Détail par principe

### Rectangle d'Or (1)
- Actuel : 160×200 (ratio 1,25)
- Cible Φ : largeur = 124px × hauteur = 200px (200/124 = 1,612) ou 160×259 (259/160 = 1,618)
- **Éléments :** `setFixedSize` de la carte
- **Effet utilisateur :** carte plus élancée, plus élégante qu'un quasi-carré
- **Contrainte :** la grille (`QGridLayout` avec `setSpacing(6)`) doit s'adapter à la nouvelle largeur

### Division Harmonique 62/38 (2)
- Photobadge (110×110) : actuellement ≈ 55% de la hauteur totale
- Proposition : badge = 38% (76px sur 200), texte + statut = 62%
- **Éléments :** `_photo_badge`, `_name_label`, `_status_label`, `_exit_label`
- **Effet utilisateur :** l'accent visuel passe du badge photo aux infos textuelles (nom, statut)

### Suite de Fibonacci (3)
- Actuel : quelques valeurs non-standards (11px, 12px, 6px, 10px, 4px)
- Cible Fibonacci :
  - `border-radius` : 8px ✅ déjà
  - `_photo_badge` : 89px (au lieu de 110px)
  - `_photo` : 55px (au lieu de 100px)
  - Police nom : 13px (au lieu de 13px → OK)
  - Police statut : 13px (au lieu de 12px)
  - Police sorties : 8px (au lieu de 11px)
  - `layout.setSpacing(8)` (au lieu de 4px)
  - `layout.setContentsMargins(8, 8, 8, 8)` (au lieu de 6)
- **Éléments :** dimensions, polices, espacements
- **Effet utilisateur :** meilleure hiérarchie visuelle, espacement plus confortable

## 3. Relation avec Material Design 3

- **MD3 Cards** : utilise 12px de `border-radius` (vs 8px Fibonacci). Les cartes MD3 ont des marges internes de 16px.
- **Divergence** : MD3 préfère des cartes plus larges et aérées.
- **Ajustement MD3** : utiliser 8px (Fibonacci) pour le radius est acceptable (MD3 autorise les small/medium/large tokens).

## 4. Réflexion couleurs

Actuellement `primary_container` pour le badge. Proposition :
- Utiliser une variante plus claire (opacité Φ² ≈ 38% de la couleur primaire) pour le fond du badge
- Bordure de carte en `outline_variant` (0,38 × primary), valeur harmonique 38%
- Texte du statut : `primary` ou `error` selon l'état (pas de changement nécessaire)

## 5. Proposition de redimensionnement Φ

| Élément | Actuel | Φ-Fibonacci |
|---|---|---|
| Carte | 160×200 | 124×200 ou 160×259 |
| Photo badge | 110×110 | 89×89 |
| Photo | 100×100 | 55×55 |
| Avatar circle | 100px | 55px |
| Avatar text | 36px | 21px |
| `border-radius` carte | 8px | 8px |
| `border-radius` badge | 12px | 8px |
| `layout.setSpacing` | 4px | 8px |
| `setContentsMargins` | 6px | 8px |
