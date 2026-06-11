# LarcSuperviseur — Contexte projet

_Dernière mise à jour : 10 juin 2026_

## Décision technique
Application PySide6 pour la supervision des présences/événements élèves.
Connexion directe psycopg2 au PostgreSQL Intranet.
Pas d'API REST, pas de SQLite locale, pas de sync device.

## Environnement
- Python 3.x + PySide6 (Qt6)
- Venv : `.venv/` dans le répertoire du projet
- Dépendances : `pip install -r requirements.txt`
- Lancement : `python main.py`
- OS cible : Windows desktop

## Base de données
- **Intranet** : PostgreSQL `127.0.0.1:5432/NewLarcDB` (écriture + lecture)
- **Cloud** : Supabase PostgreSQL via PgBouncer (lecture seule)
- Config dans `config.ini` (jamais commité)
- Sync unidirectionnelle Intranet → Cloud via daemon `LarcCloudSync`

## Architecture fichiers
```
LarcSuperviseur/
├── main.py                  # QApplication + LoginWindow + modes
├── common/
│   ├── network.py           # detect_network()
│   ├── session.py           # UserRole, Session, session (global)
│   ├── database.py          # Database (db singleton, psycopg2)
│   ├── theme.py             # ThemeManager MD3 (3 thèmes + fix border/outline_variant)
│   ├── audit.py             # Audit trail
│   └── logger.py            # log()
├── views/
│   ├── login.py             # LoginWindow (showMaximized)
│   └── main_window.py       # MainWindow (~2250 lignes) + EventGenerator
├── photos/                  # 25 PNG élèves 500×500
├── sql/
│   ├── student_event.sql    # DDL + vues
│   ├── 01_add_type_event.sql   # INSERT larcauth_type_event (27 lignes)
│   ├── run_ddl.py           # Exécution DDL
│   └── test_queries.py      # Tests SQL
├── docs/
│   ├── 01_architecture.md
│   ├── etat_projet.md
│   └── historique_construction.md
├── matrice_aiguillage_sentences.md  # Spécification UI 4 boutons événements
└── requirements.txt
```

## Rôles utilisateurs
| Rôle | Écriture | Validation | Lecture Cloud |
|---|---|---|---|
| SUPERVISEUR | Oui | Non | Non |
| COORD | Oui | Oui (via validated_by) | Oui |
| ADMIN | Oui | Oui | Oui |

Vérification via `type_supervisor = TRUE` ou `type_coordonator = TRUE` ou `is_adm = TRUE`.

## Fonctionnalités principales
- **Sidebar** : 2 sections (Collège/Lycée) × 2 colonnes programmes (PEI|MYP / DP|DPEn)
- **Page groupe** : KPIs + QtCharts (barres absences/sorties, courbe tendance, donut présence)
- **Page classe** : cartes élèves responsive (1-8 colonnes) avec photo + statut
- **Détail élève** : QStackedWidget avec onglets Coordonnées/Parents, photo 150×150, KPIs, courbe, événements, bouton ajouter
- **TimetableEditor** : grille emploi du temps modifiable
- **EventGenerator** : sélection hiérarchique 3 niveaux (catégorie → sous-type → précision) depuis `larcauth_type_event`, QDateTimeEdit éditable, combo classe filtrée, checkbox En classe + matière liée
- **Table `larcauth_type_event`** : 27 lignes, 4 catégories (Bureau BI, Médical, Sortie, Suivi) — remplace les radio-boutons en dur
- **`_event_icon()` / `_event_color()`** : fonctions supportant anciens mots-clés + nouveaux chemins hiérarchiques
- **Requêtes SQL mises à jour** : 6 requêtes filtrant sur `event_type = 'absence'/'exit'` passées en `ILIKE` pour compatibilité ascendante
- **3 thèmes MD3** : Material Light, Dark, Contrast (reconstruction complète au switch, fix border→outline_variant)
- **INSERT only** pour `student_event` (traces temporelles, pas de gabarit)
- **Ouverture maximisée** : `showMaximized()` dans LoginWindow
- **Colonnes événements harmonisées** : historique global (Élève 140px, Classe 80px, Type 110px, Heure 60px, Note Stretch, Créé par 120px)
- Rafraîchissement toutes les 30s

## Données connues
- 25 étudiants actifs, classes DP-1En et al.
- Prof 1021 (Patrice LABONNE) — également compte test secrétaire dans LarcSecretaire
- Photos : 500×500, fond transparent, chargées depuis `photos/{id}.png`
- Termes : id=1..6 (EN/FR en parallèle). T3 = id=5 (anglais) ou id=6 (français)
- Emploi du temps vide pour T3 (pas de créneaux `classroom_has_timeperiod`)
- `larcauth_type_event` : 27 lignes, IDs 100-107 (Bureau BI), 200-204 (Médical), 300-306 (Sortie), 400-406 (Suivi)

## Base de données — Table `larcauth_type_event`

| Colonne | Type | Description |
|---|---|---|
| idtypeevent | SMALLINT PK | 100-499, groupé par catégorie |
| type_event | VARCHAR | Catégorie niveau 1 (Bureau BI, Médical, Sortie, Suivi) |
| Event_Niveau2 | VARCHAR | Sous-type (Violence, Malaise, Insubordination, …) |
| Event_Niveau3 | VARCHAR | Précision (Auteur/Victime/Témoin, Envers adulte/élève, …) |
| Enabled | BOOLEAN | Activation |

Stockage dans `student_event.event_type` sous forme de chemin : `"Catégorie > Niveau2 > Niveau3"`.

## Prochaines étapes
1. Connecter EventGenerator à `larcauth_type_event` (boutons radio → hiérarchie 3 niveaux) — FAIT
2. Navigateur de date ← →
3. Remplir emploi du temps T3
4. Adapter PP et PYP
