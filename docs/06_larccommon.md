
# LarcSuperviseur — Migration vers LarcCommon

## Changements au 22 juin 2026

### common/ → Modules passerelle

L'ancien dossier `common/` a été remplacé par des modules passerelle
qui réexportent depuis `larccommon` :

```
common/database.py      → from larccommon.database import db, Database, DBMode
common/session.py       → from larccommon.session import session, Session, UserRole, ConnMode
common/logger.py        → from larccommon.logger import log
common/network.py       → from larccommon.network import detect_network
common/theme.py         → from larccommon.theme import theme_manager, ThemeManager
common/photos.py        → from larccommon.photos import get_photo_path, PhotoPreloader
common/event_helpers.py → from larccommon.event_helpers import event_icon, event_color
common/auth.py          → from larccommon.auth import OAuth2Manager
common/app_config.py    → from larccommon.app_config import app_config
common/config_loader.py → from larccommon.config_loader import find_cfg
```

**Aucune modification** des imports dans les vues n'a été nécessaire.

### PhiBuilder — Thème Material Design 3

Le `ThemeManager` intègre maintenant `PhiBuilder` :

- `bind(app)` → crée un `PhiBuilder` avec seed couleur et mode dark
- `set_active(name)` → change seed + mode dark sur le PhiBuilder
- `_reapply()` → combine QSS M3 (PhiBuilder) + QSS personnalisé

Les boutons, champs texte, scrollbars, menus et autres widgets standards
reçoivent automatiquement le style M3.

### 5 thèmes

| Thème | Seed | Mode |
|---|---|---|
| Océan | `#0D47A1` | clair |
| Forêt | `#2E7D32` | clair |
| Nuit | `#4A148C` | sombre |
| Lave | `#C62828` | sombre |
| Sable | `#E65100` | clair |

Le sélecteur dans le TopBar affiche une vignette colorée pour chaque thème.

### Traductions (l10n)

Le module `larccommon/l10n/` fournit les traductions de base.
Pour ajouter les traductions spécifiques à LarcSuperviseur :

1. Créer `LarcSuperviseur/l10n/fr.json` et `en.json`
2. Au démarrage : `Translator.instance().load_dir("LarcSuperviseur/l10n")`
3. Remplacer les textes en dur par `_("cle.contextuelle")`

### sys.path

`__main__.py` et `main.py` ajoutent `C:\projets\LarcCommon` à sys.path
pour permettre les imports de `larccommon.*` et `phibuilder.*`.
