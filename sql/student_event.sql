-- ============================================================
-- student_event : Table centralisée de présence / événements
-- ============================================================
-- Principes :
--   - INSERT only (pas de gabarit — les événements sont des traces
--     temporelles, pas des entités pré-allouées)
--   - Tous les profils (SUPERVISEUR, COORD, ADMIN) écrivent dans
--     la même table, sans conflit
--   - Modifiable uniquement depuis l'Intranet (écriture directe
--     PostgreSQL via psycopg2)
--   - Cloud = lecture seule (sync unidirectionnelle Intranet → Cloud)
-- ============================================================

CREATE TABLE IF NOT EXISTS student_event (
    event_id       INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    student_id     INTEGER NOT NULL REFERENCES larcauth_student(aecuser_ptr_id)
                             ON DELETE CASCADE,
    agenda_day_id  INTEGER NOT NULL,  -- fk vers larcauth_agenda_day (à créer)
    event_type     TEXT NOT NULL
                     CHECK (event_type IN (
                       'arrival',     -- arrivée de l'élève
                       'departure',   -- départ définitif de la journée
                       'exit',        -- sortie temporaire
                       'return',      -- retour après sortie
                       'absence',     -- absence constatée
                       'justified',   -- absence justifiée a posteriori
                       'late'         -- retard
                     )),
    event_at       TIMESTAMP NOT NULL,  -- horodatage réel du constat
    note           TEXT CHECK (length(note) <= 200),
    created_by     INTEGER NOT NULL REFERENCES larcauth_aecuser(id),
    validated_by   INTEGER REFERENCES larcauth_aecuser(id),  -- NULL = en attente
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les requêtes courantes
CREATE INDEX IF NOT EXISTS idx_event_student_day
    ON student_event(student_id, agenda_day_id);

CREATE INDEX IF NOT EXISTS idx_event_day
    ON student_event(agenda_day_id);

CREATE INDEX IF NOT EXISTS idx_event_type
    ON student_event(event_type);

CREATE INDEX IF NOT EXISTS idx_event_validated
    ON student_event(validated_by) WHERE validated_by IS NULL;

-- Index pour le dashboard temps réel (élève + date + type)
CREATE INDEX IF NOT EXISTS idx_event_student_date_type
    ON student_event(student_id, event_at, event_type);


-- ============================================================
-- Vues de synthèse (stats temps réel)
-- ============================================================

-- Présence résumée par élève × jour
CREATE OR REPLACE VIEW student_daily_summary AS
SELECT
    se.student_id,
    se.agenda_day_id,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM student_event e2
            WHERE e2.student_id = se.student_id
              AND e2.agenda_day_id = se.agenda_day_id
              AND e2.event_type = 'absence'
              AND e2.validated_by IS NULL
        ) THEN 'ABSENT'
        WHEN EXISTS (
            SELECT 1 FROM student_event e3
            WHERE e3.student_id = se.student_id
              AND e3.agenda_day_id = se.agenda_day_id
              AND e3.event_type != 'absence'
        ) THEN 'PRESENT'
        ELSE 'UNKNOWN'
    END AS presence,
    MIN(CASE WHEN se.event_type = 'arrival'  THEN se.event_at END) AS first_arrival,
    MAX(CASE WHEN se.event_type = 'departure' THEN se.event_at END) AS last_departure,
    COUNT(*) FILTER (WHERE se.event_type = 'exit')   AS exit_count,
    COUNT(*) FILTER (WHERE se.event_type = 'late')   AS late_count,
    COUNT(*) FILTER (WHERE se.event_type = 'absence'
        AND se.validated_by IS NULL) AS absence_count,
    COUNT(*) FILTER (WHERE se.event_type = 'justified') AS justified_count,
    COUNT(*) AS total_events,
    json_agg(json_build_object(
        'type', se.event_type,
        'at', se.event_at,
        'note', se.note,
        'created_by', se.created_by,
        'validated_by', se.validated_by
    ) ORDER BY se.event_at) AS events
FROM student_event se
GROUP BY se.student_id, se.agenda_day_id;

-- Dernière semaine : alertes (3+ sorties ou absence non justifiée)
CREATE OR REPLACE VIEW student_alerts AS
SELECT
    se.student_id,
    s.lastname || ' ' || s.firstname AS student_name,
    se.agenda_day_id,
    COUNT(*) FILTER (WHERE se.event_type = 'exit') AS exit_count,
    CASE
        WHEN COUNT(*) FILTER (WHERE se.event_type = 'absence'
            AND se.validated_by IS NULL) > 0 THEN TRUE
        ELSE FALSE
    END AS has_unjustified_absence,
    MAX(se.event_at) AS last_event
FROM student_event se
JOIN larcauth_student s ON s.id = se.student_id
WHERE se.event_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY se.student_id, s.lastname, s.firstname, se.agenda_day_id
HAVING
    COUNT(*) FILTER (WHERE se.event_type = 'exit') >= 3
    OR COUNT(*) FILTER (WHERE se.event_type = 'absence'
        AND se.validated_by IS NULL) > 0
ORDER BY has_unjustified_absence DESC, exit_count DESC;
