# Historique de construction — LarcSuperviseur

> Journal chronologique des itérations de développement.

---

## Itération 1 — Lancement du projet (3 juin 2026)

### Contexte
Besoin d'une application de supervision des présences et événements élèves,
distincte d'eLarcProfPy (notes/évaluations) mais partageant la même base
PostgreSQL Intranet.

### Décisions clés
| Décision | Choix | Raison |
|---|---|---|
| Modèle données | **INSERT only** | Les événements sont des traces temporelles, pas des entités pré-allouées. Pas de conflit possible (pas de gabarit). |
| Écriture hors école | **Interdite** | Les événements ne sont modifiables que depuis l'Intranet. Cloud = lecture seule. |
| Sync Cloud | **Unidirectionnelle** | Intranet → Cloud seulement. Aucun risque de corruption des données source. |
| Connexion mobile | **PgBouncer direct** | Même infra que le desktop. Pas d'API REST à déployer. |
| Rôles | SUPERVISEUR, COORD, ADMIN | Calqué sur le système existant (is_adm, is_coordonator, is_secretary). |
| Validation | `validated_by` | NULL = en attente, rempli par ADMIN/COORD. Pas de table séparée. |

### Fichiers créés
```
LarcSuperviseur/
├── __init__.py
├── __main__.py
├── main.py                    # Point d'entrée QApplication
├── common/
│   ├── __init__.py
│   ├── database.py            # Database (singleton db, pg direct)
│   ├── session.py             # UserRole (SUPERVISEUR/COORD/ADMIN), Session
│   ├── logger.py              # log() vers superviseur.log
│   └── network.py             # detect_network()
├── views/
│   ├── __init__.py
│   ├── login.py               # LoginWindow (Intranet uniquement)
│   └── main_window.py         # MainWindow (tableau events + validation)
├── sql/
│   ├── __init__.py
│   └── student_event.sql      # DDL + index + vues
├── docs/
│   ├── __init__.py
│   ├── README.md              # Index documentation
│   ├── 01_architecture.md     # Architecture globale
│   ├── etat_projet.md         # Audit
│   └── historique_construction.md  # Itération 1
└── requirements.txt
```

### Détail technique — table `student_event`
- INSERT only, pas de UPDATE/DELETE métier (sauf `validated_by`)
- 7 types d'événements contraints par `CHECK`
- Index sur (student_id, agenda_day_id), (event_type), (validated_by NULL)
- Vues : `student_daily_summary`, `student_alerts`

### Détail technique — IHM
- Login : email + password → `AuthManager.check_teacher_exists` + `verify_password`
- Vérification rôle : seuls SUPERVISEUR, COORD, ADMIN accèdent
- Filtres par type d'événement (checkboxes)
- Rafraîchissement auto toutes les 30s
- Validation : sélection multi-lignes → UPDATE `validated_by`

### Prochaines étapes
1. Table `agenda_day` (pré-allocation des jours de l'année)
2. Intégration sync Cloud dans `LarcCloudSync`
3. Tests sur données réelles Intranet
4. Mobile Flutter (phase 2)
5. Page web admin consultation externe (phase 3)

---

## Itération 2 — 27 mai au 5 juin 2026 : Refonte complète de l'IHM

### Sidebar restructurée (27 mai)
- Passage de 4 programmes séparés à 2 sections × 2 colonnes :
  - **Collège** : PEI \| MYP
  - **Lycée** : DP \| DPEn
- Headers section cliquables → filtrent tout le groupe
- Headers programme cliquables → filtrent le programme seul
- Couleurs MD3 : PEI=primary, MYP=secondary, DP=error, DPEn=tertiary
- Bouton "📊 Toutes les classes" → mode groupe global
- Bouton classe sélectionnée mémorisé dans `_selected_btn` (inversion fond/texte)

### Page groupe enrichie avec QtCharts (28 mai)
- 4 KPIs : Total/Présents/Absents/Sorties
- **Barres absences** par classe (QBarSeries)
- **Barres sorties** par classe (QBarSeries)
- **Courbe tendance** absences trimestre glissant (QLineSeries + QDateTimeAxis)
- **Donut** taux de présence (QPieSeries)
- Table statistiques + historique des derniers événements groupés
- Données ajoutées avant `addSeries` pour éviter les charts vides
- QDateTime converti proprement depuis Python date
- Titre "— aucune donnée" quand vide

### Photos redimensionnées (29 mai)
- 25 PNG élèves : 2268×2268 → 500×500 via PIL LANCZOS
- Gain ~20× en pixels, chargement instantané dans les cartes

### Panneau détail élève (30 mai)
- Remplace l'emploi du temps : nom/classe, KPIs (absences/sorties/total), courbe absences trimestre glissant (QLineSeries), table derniers événements (20 max), bouton "➕ Ajouter un événement"
- `EventGenerator` dialog : sélection type, date, note ; INSERT + rafraîchissement

### QStackedWidget pour la page classe (1er juin)
- Remplacer le QSplitter : cartes (page 0), détail élève (page 1)
- Le détail s'affiche par-dessus sans resize des cartes
- Bouton "← Retour" pour revenir aux cartes

### Grille cartes responsive (2 juin)
- 1-8 colonnes selon largeur du viewport (160px/carte)
- `resizeEvent` → `_reflow_cards()` conserve les `StudentCard` et recrée les spacers
- Les cartes sont filtrées par `isinstance()` pour ne pas confondre avec les spacers

### TimetableEditor (3 juin)
- Bouton "🕐 Emploi du temps" dans l'en-tête des cartes élèves
- Dialog : grille Heure × Lundi-Vendredi, QComboBox matières
- UPDATE `classroom_has_timeperiod` avec term_id courant
- Chargement depuis `larcauth_timeperiod` triés par jour/heure

### Thème MD3 switch rebuild (4 juin)
- `_on_theme_selected` reconstruit la sidebar (`_build_sidebar()`), le détail élève (`_rebuild_student_detail_theme()`), rafraîchit la vue active
- Palettes enrichies : `secondary`, `on_secondary`, `secondary_container`, `tertiary`, `on_tertiary`, `tertiary_container`, `on_error`
- 3 thèmes : Material Light, Material Dark, Material Contrast

### Refactor détail élève avec tabs (5 juin)
- `_build_student_detail()` extrait dans une méthode dédiée
- Code inline supprimé de `_init_ui`
- QTabWidget avec 2 onglets :
  - **Coordonnées** : photo 150×150 + nom/prénom + email (pro/perso) + tél (maison/portable) + date entrée → KPIs → courbe absences → événements → bouton Ajouter
  - **Parents** : placeholder
- QScrollArea dans chaque onglet
- `_on_back_to_cards` : cache les tabs, montre le placeholder
- `_rebuild_student_detail_theme()` : supprime l'ancien, reconstruit, réinsère dans le stack

### Fichiers modifiés
- `views/main_window.py` : ~1400 → ~1960 lignes (refactor + nouvelles fonctionnalités)
- `common/theme.py` : palette MD3 enrichie

### Prochaines étapes
1. Navigation date ← →
2. Remplir l'emploi du temps T3
3. Adapter pour PP et PYP

---

## Itération 3 — 10 juin 2026 : Hiérarchie des types d'événements + EventGenerator enrichi

### Contexte
Transformation du système de types d'événements : passage de 7 mots-clés en dur
(`arrival`, `departure`, `exit`, `return`, `absence`, `late`, `justified`)
à une hiérarchie 3 niveaux stockée en base, basée sur les spécifications de
`matrice_aiguillage_sentences.md`.

### Changements

#### 1. Table `larcauth_type_event` alimentée (27 lignes)
- 4 catégories : Bureau BI (🔴), Médical (🏥), Sortie (🚪), Suivi (👁)
- Navigation 3 niveaux : Catégorie → Sous-type → Précision
- IDs groupés : 100-107 (Bureau BI), 200-204 (Médical), 300-306 (Sortie), 400-406 (Suivi)
- Colonnes sensibles à la casse : `"Event_Niveau2"`, `"Event_Niveau3"`, `"Enabled"`

#### 2. EventGenerator refactoré (vues/main_window.py)
- Remplacement des 7 `QRadioButton` par une hiérarchie interactive :
  - 4 boutons catégories colorés (exclusifs via QButtonGroup)
  - Sous-types Niveau 2 apparaissent au clic sur une catégorie (boutons checkable)
  - Précision Niveau 3 apparaît au clic sur un Niveau 2
  - Chemin complet stocké dans `_selected_type_path` (ex: `"Sortie > Perturbation > Bavardage"`)
- `QDateTimeEdit` éditable avec calendrier popup (remplace QDateTime fixed)
- Combo classe chargée depuis `larcauth_classroom WHERE enabled = TRUE`
- Checkbox "En classe" + combo matière filtrée par classe
  (`larcauth_classroom_termsubject` → `larcauth_levelsubject`)
- Méthodes : `_load_types_from_db()`, `_on_cat_toggled()`, `_populate_niv2()`,
  `_on_niv2_clicked()`, `_populate_niv3()`, `_on_niv3_clicked()`, `_update_selection()`
- `_load_types_from_db()` appelé dans `__init__` avant `_init_ui()`

#### 3. Fonctions `_event_icon()` / `_event_color()`
- Remplacent les dicts `EVENT_ICONS` et `EVENT_COLORS`
- Supportent les anciens mots-clés (`absence`, `exit`, etc.) et les nouveaux chemins
  hiérarchiques (par préfixe de catégorie)
- Icônes par catégorie : Bureau BI 🔴, Médical 🏥, Sortie 🚪, Suivi 👁
- Couleurs : Bureau BI `#d32f2f`, Médical `#1976d2`, Sortie `#e65100`, Suivi `#f9a825`

#### 4. Requêtes SQL mises à jour (6 emplacements)
Toutes les requêtes filtrant sur `event_type = 'absence'` ou `event_type = 'exit'`
passent en `ILIKE` pour matcher aussi les nouveaux chemins :
- Stats groupe (class-level KPIs)
- Courbe tendance absences (QLineSeries)
- Donut taux de présence (QPieSeries)
- Stats classe (cartes élèves)
- Détail élève (KPIs, courbe)
- Utilisation de `ILIKE 'Suivi > Absence%'`, `'Sortie%'`, `'%Fuite%'`

#### 5. Ouverture maximisée
- `showMaximized()` dans `LoginWindow` (`views/login.py`)

#### 6. Colonnes événements harmonisées
- Historique global : Élève 140px, Classe 80px, Type 110px, Heure 60px, Note Stretch, Créé par 120px
- Détail élève : Type 90px, Date 100px, Note Stretch, Créé par 120px

#### 7. ThemeManager — Correction compatibilité
- `d.design` → utilisation directe des variables `sp`/`rd` locales
- `p.border` → `p.outline_variant` (supprimé dans Qt6.11.1/Qt6Material)

### Fichiers modifiés
- `views/main_window.py` : ~1960 → ~2250 lignes (EventGenerator + icon/color functions + queries)
- `views/login.py` : `showMaximized()` ligne 139
- `common/theme.py` : palette sans attributs `border` ni `design`
- `CONTEXT.md` : création + remplissage
- `sql/01_add_type_event.sql` : INSERT 27 lignes

### Prochaines étapes
1. Navigateur de date ← → (boutons jour précédent/suivant)
2. Remplir l'emploi du temps T3 en base
3. Adapter pour PP et PYP
4. Menu contextuel sur les événements (éditer note, valider)

---

## Itération 4 — Refonte EventGenerator + migration M3 (07 juillet 2026)

### Changements

#### 1. EventGenerator réécrit en wizard séquentiel
- 3 modes : Absence journée / Retard / Événements
- Breadcrumb cumulatif cliquable (`Événements > Classe > Violence > Auteur`)
- Un seul espace réinitialisé à chaque étape (plus de cartes empilées)
- Retard : durée (5mn à 01h00), badge tertiaire
- Matières affichées seulement si salle de cours + classe assignée
- 3 boutons de mode égaux (plus de stretch factor)

#### 2. Icônes Material Design 3
- `larccommon/icons.py` : 40 icônes MD3 en SVG → QIcon
- Remplacé tous les emoji dans top_bar, menus contextuels, main_window
- `md3_icon('name', color, size)` utilisable partout

#### 3. Thème unifié Larccommon → phibuilder
- `theme_manager.phi_theme` : thème phibuilder avec les 4 couleurs LarcCommon
- `_LarcM3Colors` : mappe `palette` → propriétés M3 (plus de violet M3 par défaut)
- `secondary_container` mappé vers `primary_container` (évite vert pastel)
- `ImageScale` : tailles standard (logo 89, icon_btn 18, theme_btn 34, etc.)

#### 4. 25 wrappers M3 dans phibuilder/widgets/
- Créés : M3TabWidget, M3DateEdit, M3TimeEdit, M3Frame, M3ScrollArea,
  M3StackedWidget, M3Menu, M3HeaderView, M3DialogButtonBox, M3TextEdit,
  M3ProgressBar, M3GroupBox, M3Splitter, M3ProfileButton
- 22 fichiers de vues migrés (plus d'imports PySide6.QtWidgets directs)

#### 5. DB type_event restaurée
- `sql/type_event_data.sql` : 27 lignes versionnées (IDs 100-499)
- Injecté dans Intranet ET Supabase

### Fichiers modifiés
- `views/dialogs/event_generator.py` : réécrit (~480 lignes)
- `views/top_bar.py` : icônes MD3 + ImageScale
- `views/main_window.py` : icônes MD3 + ImageScale
- `views/panels/group_panel.py`, `class_panel.py`, `sidebar.py`, `student_detail.py` : migration M3
- `views/login.py` : Logo via ImageScale
- `views/core/event_actions.py`, `event_dialog.py` : migration M3
- `views/dialogs/preferences.py`, `timetable_editor.py` : migration M3
- `LarcCommon/larccommon/theme.py` : phi_theme + ImageScale + _LarcM3Colors
- `LarcCommon/larccommon/icons.py` : nouveau module icônes
- `LarcCommon/phibuilder/widgets/` : 13 nouveaux wrappers + __init__.py
- `LarcHub/views/login.py`, `hub_window.py` : migration M3
- `LarcSecretaire/views/*.py` : migration M3 (8 fichiers)
- `sql/type_event_data.sql` : nouveau fichier versionné

### Problèmes connus
- `student_detail.py` ligne 226 : f-string backslash Python 3.11 (pré-existant)
- Les selects `QPushButton` dans les QSS fonctionnent encore via héritage Qt

---
