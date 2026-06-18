# Statistiques groupe

## Modes

| Mode | Filtre | Classes incluses |
|---|---|---|
| `grp_all` | Aucun | Toutes (PEI, MYP, DPEn, DPFr) |
| `grp_college` | Collège | PEI + MYP |
| `grp_lycee` | Lycée | DPEn + DPFr |
| `grp_pei` | Programme | PEI |
| `grp_myp` | Programme | MYP |
| `grp_dpfr` | Programme | DPFr |
| `grp_dpen` | Programme | DPEn |

## Périodes

| Période | Calcul |
|---|---|
| Jour | `date_from = date_to = aujourd'hui` |
| Semaine | `lundi → dimanche` |
| Mois | `1er → fin du mois` |
| Trimestre | `aujourd'hui - 3 mois → aujourd'hui` |

## KPIs

```
Total élèves = SUM(DISTINCT students dans les classes filtrées)
Absences = COUNT(event_type = 'absence' OR ILIKE 'Suivi > Absence%')
Sorties = COUNT(event_type = 'exit' OR ILIKE 'Sortie%' OR ILIKE '%Fuite%')
Présents = MAX(0, Total - Absences)
```

## Charts

| Chart | Type | Source |
|---|---|---|
| Absences | QBarSeries | `get_class_stats().abs_count` |
| Sorties | QBarSeries | `get_class_stats().exit_count` |
| Tendance | QLineSeries | `get_attendance_trend()` |
| Taux présence | QPieSeries (donut) | `get_presence_rate()` présence/absence |
