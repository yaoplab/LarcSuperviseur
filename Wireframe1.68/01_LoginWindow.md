# LoginWindow — Analyse Φ Fibonacci

**Fichier :** `views/login.py` — **Statut :** ✅ Implémenté

---

## 1. Principes utilisés : 5/5

| # | Principe | Appliqué ? | Éléments touchés |
|---|---|---|---|
| 1 | Rectangle d'Or | ✅ | Fenêtre 400×647 (L/l = 1,618) |
| 2 | Division 62/38 | ✅ | Top zone (logo → checkbox) ≈ 38%, tabs stretch 62% |
| 3 | Suite de Fibonacci | ✅ | 8px (border-radius), 13px (police), 21px (spacing, titre), 34px (marges), 55px (hauteur champs/boutons), 89px (logo) |
| 4 | Point Focal / Spirale | ✅ | Bouton Intranet 210px (61,8%) aligné à droite |
| 5 | Whitespace | ✅ | Marges 34px latérales, espacements 21px inter-sections |

## 2. Détail par principe

### Rectangle d'Or (1)
- Fenêtre `setFixedSize(400, 647)` → 647/400 = 1,618
- **Éléments :** fenêtre entière
- **Effet utilisateur :** proportion stable et élégante, instinctivement perçue comme harmonieuse

### Division Harmonique 62/38 (2)
- 38% haut (≈ 246px) : logo (89px) + titre (21px) + sous-titre (13px) + infos réseau + checkbox
- 62% bas (≈ 402px) : tabs + erreur + statut avec stretch factor 1
- **Éléments :** découpage vertical du contenu
- **Effet utilisateur :** évite la monotonie 50/50, donne du poids visuel au formulaire

### Suite de Fibonacci (3)
| Valeur | Usage |
|---|---|
| 8 px | `border-radius` des champs, boutons, panes |
| 13 px | Police des labels, inputs, boutons, messages d'erreur |
| 21 px | Espacements inter-sections, `font-size` du titre |
| 34 px | Marges extérieures horizontales (`setContentsMargins`) |
| 55 px | Hauteur des champs email/mdp et boutons |
| 89 px | Hauteur du logo (`scaledToHeight`) |

- **Éléments :** tous les widgets
- **Effet utilisateur :** cohérence visuelle parfaite, hiérarchie lisible, confort tactile (55px)

### Point Focal / Spirale Dorée (4)
- Bouton "Connexion Intranet" : largeur 210px → 210/340 ≈ 61,8%
- Alignement à droite via `QHBoxLayout` + `addStretch()`
- Le regard balaie le formulaire et termine sur le bouton (point focal naturel)
- **Éléments :** bouton principal Intranet
- **Effet utilisateur :** gestalt naturelle, l'œil est guidé vers l'action principale

### Whitespace (5)
- Marges 34px : créent une "respiration" autour du contenu
- Espacements 21px entre sections : évitent la surcharge cognitive
- **Éléments :** tous les espacements verticaux et horizontaux
- **Effet utilisateur :** réduction de la charge cognitive, interface aérée

## 3. Relation avec Material Design 3

| Principe | MD3 | Cohérence |
|---|---|---|
| Rectangle d'Or | MD3 recommande des proportions naturelles mais pas spécifiquement Φ | ✅ Compatible — MD3 n'impose pas de ratio fixe |
| Suite de Fibonacci | MD3 utilise une grille 8dp | ✅ Compatible — 8, 16, 24 de MD3 ≈ 8, 13, 21 de Fibonacci (légèrement plus serré) |
| Whitespace | MD3 préconise l'espace négatif | ✅ Renforce MD3 — l'espacement généreux améliore la lisibilité |
| Point Focal | MD3 place les actions à droite (App bar, Dialog actions) | ✅ Compatible |

**Réflexion :** Les valeurs Fibonacci (13, 21, 34) sont légèrement plus petites que les équivalents MD3 (16, 24, 32). Cela donne une interface un peu plus dense mais toujours confortable. Pour renforcer MD3, on pourrait passer à (16, 24, 32) tout en gardant le ratio Φ.

## 4. Réflexion couleurs du thème

Les couleurs actuelles :
- Primary `#0D47A1` (bleu foncé)
- Secondary `#00897B` (teal)
- Tertiary `#E65100` (orange)

Proposition d'optimisation :
- Utiliser la Suite de Fibonacci pour la luminosité : `lightness` des couleurs suivant 34, 55, 89
- Ajouter des variations de surface basées sur les ratios Φ (ex: surface = primary à 1/Φ² d'opacité)
- Respecter les rôles MD3 : `primary`, `primary_container`, `on_primary`, `surface`, `surface_variant`
