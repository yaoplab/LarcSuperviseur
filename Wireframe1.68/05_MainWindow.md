# MainWindow — Analyse Φ Fibonacci

**Fichier :** `views/main_window.py:826` — **~1850 lignes** — **Taille d'ouverture :** 1200×750 — **Statut :** 🔲 Non implémenté

---

## 1. Principes utilisables aujourd'hui : 5/5

| # | Principe | Applicable ? | État actuel |
|---|---|---|---|
| 1 | Rectangle d'Or | ✅ | `resize(1200, 750)` → ratio 1,60 (très proche de 1,618). Ajustement mineur : 1200×742 ou 1200×750 (déjà quasi-Φ) |
| 2 | Division 62/38 | ✅ | Sidebar (38% / 62% contenu) ou Top bar (38% / 62% contenu) |
| 3 | Suite de Fibonacci | ⚠️ Partiel | Quelques Fibonacci (8px border-radius, 22px date), beaucoup de valeurs arbitraires |
| 4 | Point Focal / Spirale | ✅ | Bouton "Aujourd'hui" à droite dans la top bar, boutons d'action |
| 5 | Whitespace | ⚠️ Partiel | `setSpacing(6)`, `setContentsMargins(6)` — trop serré |

## 2. Détail par principe

### Rectangle d'Or (1)
- Actuel : 1200×750 (ratio = 1,600) → très proche de Φ (1,618)
- Proposition : conserver 1200×750 (l'écart est imperceptible)
- `MainWindow` est maximisée → le ratio dépend du moniteur
- **Éléments :** fenêtre principale
- **Effet utilisateur :** proportion déjà naturelle

### Division Harmonique 62/38 — Deux lectures possibles

**Verticale (Top bar / Contenu)** :
- Top bar actuelle : ~55px sur 750 → 7% (très faible)
- Proposition : utiliser 62%/38% pour les sections principales (ex: Sidebar = 38%, Content = 62%)
- C'est déjà le cas : sidebar `setFixedWidth(260)` / total 1200 → 260/1200 = 21% (plus proche de 21% que 38%)
- **Ajustement :** sidebar à 456px pour 38% de 1200
  - Mais 456px est trop large pour une barre latérale
  - **Alternative :** utiliser le ratio Φ² = 2,618. Sidebar = 1200/2,618 ≈ 458px → trop large
  - **Recommandation :** garder 260px pour la sidebar (c'est un standard MD3), mais appliquer 38/62 à l'intérieur de la sidebar et du contenu

**Horizontale (Sidebar / Content)** :
- La sidebar fait 260px / 1200 = 21% (plus proche de Fibonacci 21 que de 38)
- Pas besoin de changer — 21% est une proportion valide (principe de la section dorée inverse)

### Suite de Fibonacci (3)

| Actuel | Fibonacci | Éléments |
|---|---|---|
| `border-radius: 6px` | 8px | Top bar, panels |
| `font-size: 22px` date | 21px | Date, heure |
| `font-size: 24px` KPI | 21px ou 34px | Valeurs KPI |
| `font-size: 10px` labels KPI | 13px | Labels |
| `font-size: 28px` bouton "+" | 21px ou 34px | Ajouter événement |
| `font-size: 18px` KPI détail | 21px | KPIs élève |
| `font-size: 9px` mini labels | 8px | Labels KPIs élève |
| `spacing: 6` partout | 8, 13, 21 selon hiérarchie | Layouts |
| `margins: 6` partout | 8, 13, 21 | Contents margins |

- **Éléments :** toute l'interface
- **Effet utilisateur :** cohérence typographique, hiérarchie visuelle claire

### Point Focal / Spirale (4)
- **Top bar** : "Aujourd'hui" et "⟳" à droite → le regard termine sa course sur les actions
- **Student detail** : bouton "➕" en bas à droite de la section contact → point focal
- **Cards** : clic sur une carte → navigation vers le détail
- **Sidebar** : "Toutes les classes" en bas → bouton d'action principale
- **À ajuster :** le bouton "➕" (100×100, police 28px) devrait faire 89×89 (Fibonacci) avec texte en 34px ou 55px

### Whitespace / Espacement (5)
- Actuel : `setSpacing(6)` et `setContentsMargins(6, 6, 6, 6)` uniforme
- Problème : pas de hiérarchie d'espacement
- Proposition :
  - `outer.setContentsMargins(13, 13, 13, 13)` (Fibonacci)
  - `main_h.setSpacing(13)`
  - Cartes KPI : `setSpacing(8)` entre cartes
  - `group_layout.setSpacing(13)` (au lieu de 8)
  - `sd_layout.setSpacing(8)` (au lieu de 6)
- **Éléments :** tous les layouts
- **Effet utilisateur :** espacement naturel, respiration visuelle

## 3. Structure détaillée

### Sidebar (`_build_sidebar`, ligne 1399)
| Composant | Actuel | Φ-Fibonacci |
|---|---|---|
| Boutons section | min_h=28, font 12px | min_h=34, font 13px |
| En-têtes colonnes | min_h=26, font 10px | min_h=21, font 13px |
| Boutons classe | min_h=32, font 10px | min_h=34, font 13px |
| "Toutes les classes" | min_h=36, font 11px | min_h=55, font 13px |
| Grid spacing | 2px | 8px |
| Section spacing | 4px | 13px |
| Marges sidebar | 6px | 8px |

### Top bar (ligne 928)
| Composant | Actuel | Φ-Fibonacci |
|---|---|---|
| Date/time font | 22px | 21px |
| Marges | 10, 6, 10, 6 | 13, 8, 13, 8 |
| "Aujourd'hui" | fixedWidth 100 | 89px (Fibonacci) |
| "⟳" refresh | fixedWidth 36 | 34px (Fibonacci) |
| "🎨" theme | fixedWidth 36 | 34px (Fibonacci) |

### Cartes KPI (ligne 1010)
| Composant | Actuel | Φ-Fibonacci |
|---|---|---|
| fixedHeight | 80px | 89px (Fibonacci) |
| Valeur font | 24px | 21px |
| Label font | 10px | 13px |
| Marges internes | 8, 4, 8, 4 | 13, 8, 13, 8 |

### Student Card Grid (ligne 1170)
| Composant | Actuel | Φ-Fibonacci |
|---|---|---|
| `setSpacing` | 6px | 8px |
| Marges cards_frame | 0 | 8px |
| Titre "Élèves" | panel_title (4px) | 13px padding |

### Student Detail (ligne 1220)
| Composant | Actuel | Φ-Fibonacci |
|---|---|---|
| Marges | 6px | 13px |
| Spacing | 6px | 8px |
| Photo | 150×150 | 144×144 (Fibonacci 144) ou 89×89 |
| Bouton "+" | 100×100, font 28px | 89×89, font 34px |
| KPIs font | 18px | 21px |
| Mini labels | 9px | 8px |

## 4. Relation avec Material Design 3

- **MD3 Navigation Rail** : la sidebar (260px) est dans les spécifications (Rail = 80px, mais pour une liste de classes, 260px est acceptable)
- **MD3 Top App Bar** : hauteur 64px recommandée (actuel ~55px). À augmenter à 64px pour conformité MD3
- **MD3 Cards** : utilisent 12px border-radius (vs 8px Fibonacci). Compromis : 8px (Fibonacci) ou 13px (≈ proche de 12 MD3)
- **MD3 Data Tables** : l'historique des événements et le tableau de stats devraient avoir des lignes de 52-72px
- **MD3 FAB** : le bouton "➕" (100×100) ressemble à un FAB. MD3 recommande 56px (FAB standard) ou 96px (large FAB). 89px (Fibonacci) est entre les deux.

**Ajustements recommandés pour MD3 :**
- Top bar → hauteur 64px
- Navigation rail → garder 260px (c'est un panel, pas un rail)
- FAB "+" → 89×89 au lieu de 100×100
- Tables → lignes 52px minimum
- Cartes KPI → 89px standard

## 5. Réflexion couleurs

- Les KPIs utilisent des couleurs différentes : présent (vert), absent (rouge), sortie (orange)
- Proposition : harmoniser avec les tokens MD3 :
  - Présent → `primary`
  - Absent → `error`
  - Sortie → `secondary`
  - Total → `tertiary`
- **Avantage :** changement de thème (dark/contrast) mettra à jour les couleurs
- **Risque :** perte de sens si le thème change (ex: vert absent en theme contrast ?)
