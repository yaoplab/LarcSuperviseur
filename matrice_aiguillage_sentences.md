# Spécifications Techniques : Matrice d'Aiguillage des Événements Scolaires

Ce document définit l'architecture de l'interface utilisateur (UI) et la logique métier pour le logiciel de récolte d'événements. L'organisation est structurée selon une approche **basée sur la sentence (Outcome-Based Routing)** afin d'optimiser la vitesse de saisie sur le terrain et de fiabiliser les indicateurs statistiques (Analytics).

---

## 📱 L'Écran Unique d'Aiguillage (Workflow Top-Level)

Dès qu'un élève est sélectionné, l'application affiche **4 Boutons de premier niveau**. Le choix de l'un de ces boutons filtre instantanément les options disponibles et définit le routage des notifications.

---

## 🔴 1. BOUTON : Bureau BI (Urgence Critique)

* **Comportement UI :** Bouton grand format, couleur rouge vif (`#EF4444`).
* **Workflow :** L'élève quitte la classe immédiatement sous escorte. Une alerte pop-up sonore et visuelle s'affiche instantanément sur les consoles de la direction et des superviseurs de service.

| Code | Cause / Option Sélectionnable | Sanction / Conséquence Légale | Canal de Notification |
| :--- | :--- | :--- | :--- |
| **SEC-01** | **Violence Physique / Rixe** | Suspension conservatoire immédiate + Convocation du Conseil de Discipline. | 🚨 SMS Urgence aux Parents + Alerte console Admin |
| **SEC-02** | **Objet Dangereux / Arme** | Saisie et sécurisation immédiate + Exclusion définitive + Signalement légal aux autorités. | 🚨 SMS Urgence aux Parents + Alerte console Sécurité & Admin |
| **SEC-03** | **Substances Interdites** | Confiscation des produits + Suspension temporaire de l'établissement (1 à 3 jours). | ⚠️ Email Prioritaire aux Parents + Rapport Direction |
| **SEC-05** | **Vandalisme Majeur** | Travaux de réparation / Intérêt général + Facturation financière des dégâts matériels. | ⚠️ Email aux Parents (Responsabilité Civile) + Direction |
| **BEH-05** | **Harcèlement / Bullying** | Retrait immédiat de l'élève + Ouverture d'une enquête administrative + Mesures d'éloignement. | 📞 Convocation Officielle des Parents (Auteur + Victime) |

---

## 🩺 2. BOUTON : Urgence Médicale & Secours

* **Comportement UI :** Bouton grand format, couleur bleue ou verte avec picto médical (`#3B82F6` ou `#10B981`).
* **Workflow :** L'élève nécessite des soins immédiats (sur place ou extraction vers l'infirmerie). **Routage exclusif vers le personnel de santé.** Événement totalement décorrélé du système disciplinaire.

| Code | Cause / Option Sélectionnable | Flux Opérationnel | Canal de Notification |
| :--- | :--- | :--- | :--- |
| **WEL-05** | **Malaise / Blessure / Panique** | Prise en charge infirmerie ou appel direct des secours médicaux extérieurs (Ambulance). **ZÉRO SANCTION.** | 🚨 Appel Téléphonique Direct + SMS urgent aux Parents + Alerte Infirmerie |

---

## 🟧 3. BOUTON : Sortie de Cours (Rupture du cadre)

* **Comportement UI :** Bouton moyen format, couleur orange (`#F97316`).
* **Workflow :** L'élève est extrait physiquement de la classe pour le reste de la période afin de préserver l'accès à l'enseignement pour le groupe, mais sans déclencher la cellule de crise de la direction générale.

| Code | Cause / Option Sélectionnable | Destination / Prise en charge | Canal de Notification |
| :--- | :--- | :--- | :--- |
| **BEH-01** | **Insubordination Grave** | Aiguillage direct vers le bureau de permanence des superviseurs + Heure de retenue (Detention). | 📧 Email Standard automatique aux Parents + Superviseur |
| **BEH-02** | **Abus Verbal / Injure** | Extraction de la classe + Retenue obligatoire + Rédaction supervisée d'une lettre d'excuses formelle. | 📧 Email Standard automatique aux Parents + Prof Principal |
| **WEL-01** | **Urgence Biologique / Fuite** | Autorisation de circulation temporaire pour se rendre aux sanitaires ou à l'infirmerie. **ZÉRO SANCTION.** | 🔒 Log Interne uniquement (Traçabilité des flux élèves) |

---

## 🟡 4. BOUTON : Notification Simple & Suivi

* **Comportement UI :** Bouton format standard, couleur jaune ou grise (`#EAB308` ou `#64748B`).
* **Workflow :** L'élève reste dans la classe. L'action consiste en une saisie de données ultra-rapide (1 clic) pour l'historique de l'élève (tracking) et pour une information passive des familles.

| Code | Cause / Option Sélectionnable | Règle Métier / Impact Système | Canal de Notification |
| :--- | :--- | :--- | :--- |
| **BEH-04** | **Fraude / Triche / Vol mineur** | Attribution automatique d'une note de zéro à l'évaluation + Rapport écrit consigné au dossier. | ⚠️ Email aux Parents + Direction Pédagogique |
| **ACA-01** | **Absence Injustifiée** | Verrouillage du statut de l'élève pour la période. Justificatif officiel exigé sous 24h. | 🤖 SMS Automatique immédiat aux Parents |
| **BEH-03** | **Perturbation mineure / Bavardage** | Incrémentation du compteur (+1). Une règle métier déclenche automatiquement une retenue au 3e clic. | 📱 Flux Application Parents (Synthèse de fin de journée) |
| **ACA-04** | **Oubli de Matériel / Devoir** | Prêt de matériel pour le cours. Génère une alerte d'organisation si le total trimestriel > 4. | 📱 Flux Application Parents (Suivi logistique) |
| **WEL-02** | **Somnolence / Fatigue chronique** | Note de vigilance éducative. Permet de détecter les ruptures de rythme ou problèmes de santé. | 🔒 Note interne partagée au sein de l'équipe pédagogique |
| **WEL-03** | **Changement brutal d'attitude** | Signal faible (isolement, baisse soudaine des notes). Déclenche une demande de bilan tuteur. | 🔒 Note interne sécurisée (Hors Parents initialement) |

---

## 📊 Modèle de Données et Statistiques (Business Intelligence)

Cette architecture permet de structurer le schéma de votre base de données avec 4 index principaux. Le Dashboard de la direction se compose ainsi de 4 graphiques clés :

1. **Indice de Sécurité (Sécurité & Climat Scolaire) :** Généré par l'analyse des volumes du **Bouton 1**. Permet de mesurer les menaces physiques réelles sur l'établissement.
2. **Indice de Santé (Charge Médicale) :** Généré par le **Bouton 2**. Permet de piloter les ressources de l'infirmerie et de tracer les urgences sanitaires.
3. **Indice de Tenue des Classes (Taux d'Exclusion) :** Généré par le **Bouton 3**. Mesure l'efficacité de la gestion de classe et le recours à l'extraction physique.
4. **Indice Académique & Organisationnel (Signaux Faibles) :** Généré par le **Bouton 4**. Regroupe les statistiques de ponctualité, de bavardages, d'oublis de matériel et de suivi du bien-être.
