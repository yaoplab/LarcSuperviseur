import os
from larccommon.app_config import app_config, AppConfig

# Surcharger les chemins des photos (LarcCommon/larccommon/ ≠ LarcSuperviseur/common/)
_here = os.path.dirname(os.path.abspath(__file__))
app_config._cache['photos_dir'] = os.path.normpath(
    os.path.join(_here, '..', 'photos'))
app_config._cache['photos_cache_dir'] = os.path.normpath(
    os.path.join(_here, '..', 'photos', 'cache'))

__all__ = ["app_config", "AppConfig"]
