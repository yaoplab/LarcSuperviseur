import sys
import os

_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Pour importer common/auth.py depuis eLarcProfPy
_prof_root = os.path.normpath(os.path.join(_root, 'eLarcProfPy'))
if os.path.isdir(_prof_root) and _prof_root not in sys.path:
    sys.path.insert(0, _prof_root)

# Ajouter LarcCommon pour larccommon.* et phibuilder.*
_common_root = os.path.normpath(os.path.join(_root, 'LarcCommon'))
if os.path.isdir(_common_root) and _common_root not in sys.path:
    sys.path.insert(0, _common_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from LarcSuperviseur.views.login import LoginWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName('LarcSuperviseur')
    app.setOrganizationName('Arc-en-Ciel')
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 10))

    window = LoginWindow()
    window.resize(1000, 650)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
