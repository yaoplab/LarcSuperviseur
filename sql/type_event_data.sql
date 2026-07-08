-- larcauth_type_event — 27 lignes, 4 catégories
-- Reconstruction d'après historique_construction.md
-- IDs: 100-107 (Bureau BI), 200-204 (Médical), 300-306 (Sortie), 400-406 (Suivi)

DELETE FROM larcauth_type_event WHERE idtypeevent >= 100;

INSERT INTO larcauth_type_event (idtypeevent, type_event, "Event_Niveau2", "Event_Niveau3", "Enabled") VALUES
-- Bureau BI (8 lignes: 100-107)
(100, 'Bureau BI', 'Violence',     'Auteur',     TRUE),
(101, 'Bureau BI', 'Violence',     'Victime',    TRUE),
(102, 'Bureau BI', 'Violence',     'Témoin',     TRUE),
(103, 'Bureau BI', 'Harcèlement',  'Auteur',     TRUE),
(104, 'Bureau BI', 'Harcèlement',  'Victime',    TRUE),
(105, 'Bureau BI', 'Harcèlement',  'Témoin',     TRUE),
(106, 'Bureau BI', 'Fugue',        NULL,         TRUE),
(107, 'Bureau BI', 'Entretien',    NULL,         TRUE),
-- Médical (5 lignes: 200-204)
(200, 'Médical', 'Maladie',        NULL,         TRUE),
(201, 'Médical', 'Accident',       'Scolaire',   TRUE),
(202, 'Médical', 'Accident',       'Sportif',    TRUE),
(203, 'Médical', 'Infirmerie',     NULL,         TRUE),
(204, 'Médical', 'Hospitalisation', NULL,        TRUE),
-- Sortie (7 lignes: 300-306)
(300, 'Sortie', 'Perturbation',    'Bavardage',  TRUE),
(301, 'Sortie', 'Perturbation',    'Agitation',  TRUE),
(302, 'Sortie', 'Perturbation',    'Insolence',  TRUE),
(303, 'Sortie', 'Exclusion',       'Interne',    TRUE),
(304, 'Sortie', 'Exclusion',       'Externe',    TRUE),
(305, 'Sortie', 'Renvoi',          NULL,         TRUE),
(306, 'Sortie', 'Demande',         NULL,         TRUE),
-- Suivi (7 lignes: 400-406)
(400, 'Suivi', 'Absence',          'Maladie',    TRUE),
(401, 'Suivi', 'Absence',          'Accident',   TRUE),
(402, 'Suivi', 'Absence',          'Vacances',   TRUE),
(403, 'Suivi', 'Absence',          'Non justifiée', TRUE),
(404, 'Suivi', 'Retard',           NULL,         TRUE),
(405, 'Suivi', 'Comportement',     NULL,         TRUE),
(406, 'Suivi', 'Suivi pédagogique', NULL,        TRUE);
