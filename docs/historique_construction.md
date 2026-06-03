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

_3 juin 2026_
