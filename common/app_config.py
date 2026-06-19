import os
from .database import db
from .logger import log

_here = os.path.dirname(os.path.abspath(__file__))


class AppConfig:
    CONFIG_TABLE = 'larcauth_config'

    DEFAULTS = {
        'photos_dir': os.path.normpath(
            os.path.join(_here, '..', 'photos')),
        'photos_cache_dir': os.path.normpath(
            os.path.join(_here, '..', 'photos', 'cache')),
    }

    def __init__(self):
        self._cache = dict(self.DEFAULTS)
        self._loaded = False

    def load(self):
        conn = db.server_conn
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT key, value FROM {self.CONFIG_TABLE}")
            for key, value in cur.fetchall():
                self._cache[key] = value
            self._loaded = True
            log(f"AppConfig: charge {len(self._cache)} clefs depuis PostgreSQL")
        except Exception as e:
            log(f"AppConfig: echec chargement ({e}), fallback valeurs par defaut")

    def get(self, key: str, default=None):
        if not self._loaded:
            self.load()
        return self._cache.get(key, default)


app_config = AppConfig()
