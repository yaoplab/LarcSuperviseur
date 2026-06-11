DO $$
DECLARE
    v_agenda_id INT;
    v_student1 INT;
    v_student2 INT;
    v_user INT;
BEGIN
    SELECT id INTO v_agenda_id FROM larcauth_agenda WHERE date_all = CURRENT_DATE;
    IF v_agenda_id IS NULL THEN
        INSERT INTO larcauth_agenda (id, date_all, j, m, w, year, working_day, week_day)
        VALUES ((SELECT COALESCE(MAX(id),0)+1 FROM larcauth_agenda), CURRENT_DATE,
                EXTRACT(DAY FROM CURRENT_DATE)::smallint,
                EXTRACT(MONTH FROM CURRENT_DATE)::smallint,
                EXTRACT(WEEK FROM CURRENT_DATE)::smallint,
                EXTRACT(YEAR FROM CURRENT_DATE)::smallint,
                TRUE, EXTRACT(DOW FROM CURRENT_DATE)::smallint)
        RETURNING id INTO v_agenda_id;
    END IF;

    SELECT id INTO v_user FROM larcauth_aecuser WHERE type_supervisor = TRUE LIMIT 1;
    IF v_user IS NULL THEN
        SELECT id INTO v_user FROM larcauth_aecuser WHERE type_director = TRUE LIMIT 1;
    END IF;
    IF v_user IS NULL THEN
        SELECT id INTO v_user FROM larcauth_aecuser WHERE type_coordonator = TRUE LIMIT 1;
    END IF;

    SELECT aecuser_ptr_id INTO v_student1 FROM larcauth_student WHERE enabled = TRUE LIMIT 1 OFFSET 0;
    SELECT aecuser_ptr_id INTO v_student2 FROM larcauth_student WHERE enabled = TRUE LIMIT 1 OFFSET 1;

    INSERT INTO student_event (student_id, agenda_day_id, event_type, event_at, created_by)
    VALUES (v_student1, v_agenda_id, 'arrival', CURRENT_DATE + TIME '08:15:00', v_user);

    INSERT INTO student_event (student_id, agenda_day_id, event_type, event_at, created_by)
    VALUES (v_student1, v_agenda_id, 'departure', CURRENT_DATE + TIME '16:00:00', v_user);

    INSERT INTO student_event (student_id, agenda_day_id, event_type, event_at, created_by)
    VALUES (v_student2, v_agenda_id, 'absence', CURRENT_DATE + TIME '09:00:00', v_user);

    INSERT INTO student_event (student_id, agenda_day_id, event_type, event_at, created_by)
    VALUES (v_student1, v_agenda_id, 'exit', CURRENT_DATE + TIME '11:30:00', v_user);

    INSERT INTO student_event (student_id, agenda_day_id, event_type, event_at, created_by)
    VALUES (v_student1, v_agenda_id, 'return', CURRENT_DATE + TIME '12:00:00', v_user);
END $$;
