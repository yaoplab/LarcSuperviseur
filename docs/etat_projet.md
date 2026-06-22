# État du Projet — LarcSuperviseur

_Audit du 3 juin 2026 — Dernière mise à jour : 22 juin 2026_

## 1. Verdict Global

✅ **Projet bien avancé.** Application desktop PySide6 fonctionnelle avec :
- Sidebar avec navigation par sections (Collège/Lycée) et programmes (PEI/MYP/DP/DPEn)
- Page groupe avec KPIs + 4 graphiques QtCharts (barres absences/sorties, courbe tendance, donut présence)
- Page classe avec cartes élèves responsive + détail élève en QStackedWidget
- Édition feuille de présence + génération d'événements hiérarchique (3 niveaux depuis `larcauth_type_event`)
- Emploi du temps éditable
- 3 thèmes MD3 avec reconstruction des composants inline

## 2. Terminé

- Architecture validée : INSERT only, pas de gabarit, écriture Intranet uniquement
- Table `student_event` : DDL complet avec CHECK, clés étrangères, index
- Vues de synthèse : `student_daily_summary`, `student_alerts`
- Structure projet : `common/`, `views/`, `docs/`
- Modules communs : `database.py`, `session.py`, `logger.py`, `network.py`, `theme.py`
- Login window : connexion Intranet avec vérification des rôles
- Top bar : date, heure, état réseau bouton thème
- **Sidebar restructurée** : 2 sections (Collège/Lycée) × 2 colonnes programmes (PEI|MYP / DP|DPEn). Headers section cliquables + headers programme cliquables
- **Page groupe** : 4 KPIs (Total/Présents/Absents/Sorties) + barres absences par classe + barres sorties par classe + courbe tendance absences (QDateTimeAxis) + donut taux présence (QPieSeries) + stats table + historique événements
- **Page classe** : grille cartes responsive (1-8 colonnes selon largeur) avec photo, statut, nb sorties. Clic → détail élève
- **QStackedWidget** pour page classe : cartes (0) + détail élève (1) avec bouton ← Retour. Pas de redimensionnement des cartes
- **Détail élève** : refactoré en `_build_student_detail()` avec QTabWidget. Onglet "Coordonnées" (photo 150×150, nom, email, tél, date entrée, KPIs, courbe absences, table événements, bouton ajouter) + onglet "Parents" (placeholder)
- **TimetableEditor** : dialog grille Heure × Lundi-Vendredi avec QComboBox matières, UPDATE `classroom_has_timeperiod`
- **EventGenerator** : dialog création événement avec sélection hiérarchique 3 niveaux depuis `larcauth_type_event` (4 catégories), QDateTimeEdit éditable, combo classe filtrée, checkbox "En classe" + matière conditionnelle
- **Changement de thème** : reconstruit sidebar, détail élève, rafraîchit vue active
- **Photos élèves** : 25 PNG redimensionnées 2268×2268 → 500×500 (LANCZOS)
- Rafraîchissement automatique toutes les 30s
- **Table `larcauth_type_event`** : 27 lignes INSERT, 4 catégories (Bureau BI, Médical, Sortie, Suivi)
- **Fonctions `_event_icon()` / `_event_color()`** : support anciens mots-clés + nouveaux chemins hiérarchiques (icône + couleur par catégorie)
- **Requêtes SQL migrées** : 6 requêtes filtrant sur event_type passées en ILIKE (compatibilité ascendante)
- **Ouverture maximisée** : `showMaximized()` au login
- **Colonnes événements harmonisées** : largeurs fixes cohérentes entre historique global et détail élève
- **Fix ThemeManager** : `d.design` → var locales, `p.border` → `p.outline_variant`

## 3. En cours

- Emploi du temps vide pour T3 (pas de créneaux `classroom_has_timeperiod` pour term_id=5/6 sur ce serveur)

## 4. Bloquant

- Aucun

## 5. Reste à Faire (Priorité)

1. Navigation date avec boutons ← → jour
2. Remplir l'emploi du temps T3 en base
3. Adapter l'app pour PP et PYP si besoin
4. Interface mobile Flutter (phase ultérieure)
5. Page web admin pour consultation depuis l'extérieur (phase ultérieure)

## 5b. Nouveau (22 juin 2026)

- Migration `common/` → `larccommon` (LarcCommon) via modules passerelle
- Intégration PhiBuilder dans ThemeManager (QSS Material Design 3 pour 16 widgets)
- 5 thèmes au lieu de 3 : Océan, Forêt, Nuit, Lave, Sable (+ vignettes colorées)
- Module de traduction l10n disponible (fr/en)
- Voir `docs/06_larccommon.md` pour les détails

## 6. Documentation

- `docs/01_architecture.md` — à jour
- `docs/etat_projet.md` — à jour
- `docs/historique_construction.md` — à jour (itérations 1 et 2)
- `sql/student_event.sql` — DDL + vues

---

_Mémoire persistante LarcSuperviseur — 5 juin 2026_
