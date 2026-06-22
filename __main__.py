import sys
import os

# Ajouter la racine du projet pour les imports (common.*)
_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Ajouter LarcCommon pour larccommon.* et phibuilder.*
_common_root = os.path.normpath(os.path.join(_root, 'LarcCommon'))
if os.path.isdir(_common_root) and _common_root not in sys.path:
    sys.path.insert(0, _common_root)

from LarcSuperviseur.main import main

if __name__ == '__main__':
    main()
