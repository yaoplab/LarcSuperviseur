def event_icon(event_type: str) -> str:
    icons = {'arrival': '▲', 'departure': '▼', 'exit': '→', 'return': '←',
             'absence': '✕', 'justified': '✓', 'late': '⏰'}
    if event_type in icons:
        return icons[event_type]
    if event_type.startswith('Bureau BI'):
        return '🔴'
    if event_type.startswith('Médical'):
        return '🏥'
    if event_type.startswith('Sortie'):
        return '🚪'
    if event_type.startswith('Suivi'):
        return '👁'
    return '●'

def event_color(event_type: str) -> str:
    colors = {'arrival': '#27ae60', 'departure': '#2980b9', 'exit': '#e67e22',
              'return': '#2ecc71', 'absence': '#e74c3c', 'justified': '#95a5a6',
              'late': '#f1c40f'}
    if event_type in colors:
        return colors[event_type]
    if event_type.startswith('Bureau BI'):
        return '#d32f2f'
    if event_type.startswith('Médical'):
        return '#1976d2'
    if event_type.startswith('Sortie'):
        return '#e65100'
    if event_type.startswith('Suivi'):
        return '#f9a825'
    return '#555'
