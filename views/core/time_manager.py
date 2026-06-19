from PySide6.QtCore import QDate


class TimeManager:
    """Centralised session time state: current date, period, unit periods, term."""

    def __init__(self):
        self.current_date: QDate = QDate.currentDate()
        self.current_period: str = 'day'  # day, week, month, term, year, unit_N
        self.unit_periods: list[dict] = []
        self.term_id: int = 0
        self.term_label: str = ''

    def period_dates(self) -> tuple[str, str]:
        d = self.current_date
        p = self.current_period
        if p == 'day':
            return d.toString('yyyy-MM-dd'), d.toString('yyyy-MM-dd')
        if p == 'week':
            start = d.addDays(-(d.dayOfWeek() - 1))
            return start.toString('yyyy-MM-dd'), start.addDays(6).toString('yyyy-MM-dd')
        if p == 'month':
            start = QDate(d.year(), d.month(), 1)
            return start.toString('yyyy-MM-dd'), QDate(d.year(), d.month(), d.daysInMonth()).toString('yyyy-MM-dd')
        if p == 'year':
            return QDate(d.year(), 1, 1).toString('yyyy-MM-dd'), QDate(d.year(), 12, 31).toString('yyyy-MM-dd')
        if p.startswith('unit_'):
            uid = int(p.split('_')[1])
            for up in self.unit_periods:
                if up['id'] == uid:
                    return up['start_date'], up['end_date']
            return d.toString('yyyy-MM-dd'), d.toString('yyyy-MM-dd')
        start = d.addMonths(-3)
        return start.toString('yyyy-MM-dd'), d.toString('yyyy-MM-dd')

    def go_today(self):
        self.current_date = QDate.currentDate()

    def select_period(self, key: str) -> bool:
        if key == self.current_period and key == 'day':
            self.go_today()
            return True
        self.current_period = key
        return False

    def set_term(self, term_id: int, term_label: str):
        self.term_id = term_id
        self.term_label = term_label
