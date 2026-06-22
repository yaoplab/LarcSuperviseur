# TimetableEditor — Analyse Φ Fibonacci

**Fichier :** `views/main_window.py:2495` — **Taille min :** 800×500 — **Statut :** 🔲 Non implémenté

---

## 1. Principes utilisables aujourd'hui : 4/5

| # | Principe | Applicable ? | État actuel |
|---|---|---|---|
| 1 | Rectangle d'Or | ✅ | `setMinimumSize(800, 500)` → ratio 1,6 (quasi-Φ). À ajuster à 800×494 ou 800×500 |
| 2 | Division 62/38 | ✅ | Table (62%) / Boutons (38%) ou colonne Heure (38%) / Jours (62%) |
| 3 | Suite de Fibonacci | ⚠️ Partiel | `border-radius: 6px` (≈ 8px) pour le bouton save. Peu d'autres valeurs Fibonacci |
| 4 | Point Focal / Spirale | ✅ | Bouton "💾 Enregistrer" aligné à droite (action principale) |
| 5 | Whitespace | ⚠️ Partiel | Layout simple, pas de marges définies explicitement (utilise les valeurs par défaut) |

## 2. Détail par principe

### Rectangle d'Or (1)
- Actuel : 800×500 (ratio = 1,600)
- Cible Φ : 800×494 (494 = 800/1,618) ou garder 800×500 (écart de 6px imperceptible)
- **Éléments :** fenêtre dialog
- **Effet utilisateur :** proportions équilibrées

### Division Harmonique 62/38 (2)
- **Option A (verticale) :** Table = 62%, Boutons = 38%
  - Le bouton save + layout prend ~50px sur 500 = 10% seulement
  - Proposition : ne pas forcer 38% pour une simple rangée de boutons
- **Option B (horizontale) :** Colonne Heure = 38% de la largeur, colonnes jours = 62%
  - Actuel : colonne Heure = 80px, colonnes jours = 140px × 5 = 700px
  - 80 / (80+700) = 10% → trop faible
  - Ajustement : Heure = 0,38 × 780 = 296px → trop large
- **Recommandation :** ne pas forcer 38% ici, la grille a ses propres contraintes (taille des jours)

### Suite de Fibonacci (3)
| Actuel | Fibonacci | Éléments |
|---|---|---|
| `border-radius: 6px` (save btn) | 8px | Bouton enregistrer |
| Police 12px (save btn) | 13px | Bouton |
| Padding 6px 20px (save btn) | 8px 21px | Padding bouton |
| `setMinimumHeight(36)` (save btn) | 55px | Hauteur bouton |
| Police combo (défaut Qt) | 13px | Combobox matières |
| `setColumnWidth(0, 80)` | 89px (Fibonacci) | Colonne heure |

- **Éléments :** bouton save, grille
- **Effet utilisateur :** meilleure cohérence avec le reste de l'app

### Point Focal / Spirale (4)
- Bouton "💾 Enregistrer" : aligné à droite (`btn_row.addStretch()`)
- C'est déjà conforme au principe du point focal
- **Éléments :** `save_btn`
- **Effet utilisateur :** l'action de sauvegarde est l'aboutissement de l'édition

### Whitespace (5)
- Actuel : pas de `setContentsMargins` explicite sur le layout principal (utilisation des défauts Qt = 11px)
- Proposition : `layout.setContentsMargins(13, 13, 13, 13)`
- `btn_row` pas de marges explicites
- **Éléments :** layout principal
- **Effet utilisateur :** espacement conforme au système de design global

## 3. Relation avec Material Design 3

- **MD3 Dialog** : `setMinimumSize(800, 500)` est large pour un dialog MD3 (full-screen dialog). Recommandation : Full-screen dialog avec hauteur variable
- **MD3 Table** : lignes alternées ✅ déjà présent, `setAlternatingRowColors(True)`
- **MD3 Button** : le bouton "Enregistrer" utilise `primary` comme fond ✅ conforme
- **Divergence** : MD3 recommande des boutons de 48px de hauteur vs 55px Fibonacci. Compromis : garder 55px (confort tactile)

## 4. Proposition de redimensionnement Φ

| Élément | Actuel | Φ-Fibonacci |
|---|---|---|
| Fenêtre | 800×500 | 800×500 (garder, déjà quasi-Φ) |
| Marges layout | défaut Qt (11px) | 13px |
| Colonne Heure | 80px | 89px |
| Colonne jour | 140px | 144px (Fibonacci) |
| Hauteur bouton save | 36px | 55px |
| Police save | 12px | 13px |
| Border-radius save | 6px | 8px |
| Padding save | 6px 20px | 8px 21px |

## 5. Réflexion couleurs

- Bouton "💾 Enregistrer" utilise déjà `primary` → conforme
- Les combobox matière utilisent les couleurs par défaut → s'harmonisent avec le thème active
- Proposition : ajouter un fond `surface_variant` pour les lignes paires de la grille (`setAlternatingRowColors` déjà actif)
- Couleur du texte de la colonne Heure : `text_strong` (déjà)
