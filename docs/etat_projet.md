# État du Projet — LarcSuperviseur

_Audit du 3 juin 2026 — Dernière mise à jour : 3 juin 2026_

## 1. Verdict Global

✅ **Projet lancé.** Architecture définie, table `student_event` créée, DDL avec vues,
application desktop PySide6 en structuration initiale.

## 2. Terminé

- Architecture validée : INSERT only, pas de gabarit, écriture Intranet uniquement
- Table `student_event` : DDL complet avec CHECK, clés étrangères, index
- Vues de synthèse : `student_daily_summary`, `student_alerts`
- Structure projet : `common/`, `views/`, `sql/`, `docs/`
- Modules communs : `database.py`, `session.py`, `logger.py`, `network.py`
- Login window : connexion Intranet avec vérification des rôles
- Main window : écran superviseur complet (top bar date/heure, groupes/classes, période)
- Mode groupe : stats par classe + historique événements
- Mode classe : cartes élèves avec photo, présence, nb sorties + emploi du temps cliquable
- Écran génération d'événement (clic élève + créneau)
- Rafraîchissement automatique toutes les 30s

## 3. En cours

- Tests de connexion réelle sur l'Intranet
- Intégration de la table `student_event` dans le daemon `LarcCloudSync` (direction unique)

## 4. Bloquant

- Aucun

## 5. Reste à Faire (Priorité)

1. Créer la table `agenda_day` (pré-allouer les jours de l'année scolaire)
2. Ajouter `student_event` aux tables sync du daemon `LarcCloudSync` (N1 ou N2)
3. Tester l'écriture directe PostgreSQL depuis le desktop
4. Interface mobile Flutter (phase ultérieure)
5. Page web admin pour consultation depuis l'extérieur (phase ultérieure)

## 6. Documentation

- `docs/01_architecture.md` — à jour
- `docs/etat_projet.md` — à jour
- `docs/historique_construction.md` — à jour
- `sql/student_event.sql` — DDL + vues

---

_Mémoire persistante LarcSuperviseur — 3 juin 2026_
