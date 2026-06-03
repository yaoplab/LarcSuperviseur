import sys
import os

# Ajouter la racine du projet pour les imports (common.auth, common.network, etc.)
_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

from LarcSuperviseur.main import main

if __name__ == '__main__':
    main()
