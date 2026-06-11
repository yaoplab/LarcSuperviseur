# LarcSuperviseur — Supervision des présences et événements élèves

> Application desktop pour la collecte, la visualisation et la validation
> des événements de présence/absence des élèves (usage interne école).

## Architecture

```
Intranet PostgreSQL (192.168.2.90:5432/NewLarcDB)
        ↕
┌──────────────────┐    ┌──────────────────┐
│ Desktop PySide6  │    │ Mobile Flutter   │
│ (école)          │    │ (école, WiFi)    │
│ psycopg2 direct  │    │ PgBouncer direct │
└──────────────────┘    └──────────────────┘
        │                        │
        └────────┬───────────────┘
                 ↓
        ┌──────────────────┐
        │ Supabase Cloud   │
        │ (lecture seule)  │ ← sync unidirectionnelle Intranet → Cloud
        └──────────────────┘
                 │
        ┌────────┘
        ↓
┌──────────────────┐
│ Navigateur (admin)│
│ (depuis maison)   │
│ lecture seule     │
└──────────────────┘
```

## Principes fondamentaux
- **INSERT only** pour `student_event` (pas de gabarit — événements = traces temporelles)
- **Écriture uniquement depuis l'Intranet** — jamais depuis le Cloud
- **Sync unidirectionnelle** Intranet → Cloud (lecture seule côté Cloud)
- **Validation** possible par ADMIN/COORD (colonne `validated_by`)
- **Mêmes règles métier** pour tous les clients (contraintes CHECK + triggers PostgreSQL)
- **Pas de daemon quotidien** — tout est temps réel via la base

## Tables principales

### `student_event`
| Colonne | Type | Description |
|---|---|---|
| event_id | INTEGER PK | Auto-généré |
| student_id | INTEGER FK | Référence `larcauth_student` |
| agenda_day_id | INTEGER | Jour de l'agenda |
| event_type | TEXT | Chemin hiérarchique : `"Catégorie > Niveau2 > Niveau3"` (ex: `"Suivi > Absence injustifiée"`) ou ancien mot-clé (`arrival`, `absence`, `exit`) |
| event_at | TIMESTAMP | Horodatage réel du constat |
| note | TEXT | Remarque libre (≤200 chars) |
| created_by | INTEGER FK | Référence `larcauth_aecuser` |
| validated_by | INTEGER FK | NULL = en attente de validation |
| created_at | TIMESTAMP | Auto |

### `larcauth_type_event` (table de référence, PostgreSQL seule)
| Colonne | Type | Description |
|---|---|---|
| idtypeevent | SMALLINT PK | 100-499, groupé par catégorie |
| type_event | VARCHAR | Catégorie niveau 1 (Bureau BI, Médical, Sortie, Suivi) |
| Event_Niveau2 | VARCHAR | Sous-type (Violence, Malaise, Insubordination, …) |
| Event_Niveau3 | VARCHAR | Précision (Auteur/Victime/Témoin, Envers adulte/élève, …) |
| Enabled | BOOLEAN | Activation |

Les 3 niveaux sont présentés dans l'EventGenerator sous forme de boutons progressifs :
1. 4 boutons catégories (🔴🏥🚪👁)
2. Sous-types Niveau 2 (apparaissent au clic sur la catégorie)
3. Précision Niveau 3 (apparaît au clic sur le Niveau 2)

Stockage dans `event_type` : chemin complet `"Catégorie > Niveau2"` (ou `"Catégorie > Niveau2 > Niveau3"`).

### Vues
- `student_daily_summary` — résumé présence/absence par élève × jour
- `student_alerts` — alertes (3+ sorties ou absence non justifiée dans la semaine)

## Rôles utilisateurs
| Rôle | Écriture | Validation | Lecture extérieure |
|---|---|---|---|
| SUPERVISEUR | Oui | Non | Non |
| COORD | Oui | Oui | Non |
| ADMIN | Oui | Oui | Oui (Cloud) |

## Technologies
- **Desktop** : Python 3.x + PySide6
- **Base** : PostgreSQL 15 (Intranet) + Supabase (Cloud, lecture seule)
- **Connexion** : psycopg2 direct via PgBouncer
- **Config** : `config.ini` (même fichier que eLarcProfPy)
- **Sync Cloud** : daemon `LarcCloudSync` (direction unique Intranet → Cloud)
