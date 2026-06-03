import os
import configparser
from enum import Enum, auto
from typing import Optional

try:
    import psycopg2
    _PG_OK = True
except ImportError:
    _PG_OK = False

from .logger import log as _log


def _find_cfg() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, '..', 'config.ini'),
        os.path.join(here, '..', '..', 'eLarcProf', 'config.ini'),
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.isfile(p):
            return p
    _log("AVERTISSEMENT : config.ini introuvable. Utilisation des valeurs par défaut.")
    print("AVERTISSEMENT : config.ini introuvable. Utilisation des valeurs par défaut.")
    return os.path.normpath(candidates[0])


class DBMode(Enum):
    NONE     = auto()
    INTRANET = auto()
    CLOUD    = auto()


class Database:
    def __init__(self) -> None:
        self._intranet: Optional[object] = None
        self._cloud:    Optional[object] = None
        self._mode = DBMode.NONE
        self._server_mode = DBMode.NONE

    def _pg_params(self, section: str) -> dict:
        cfg = configparser.ConfigParser()
        cfg.read(_find_cfg())
        default_db = 'NewLarcDB' if section == 'IntranetDatabase' else 'postgres'
        return {
            'host':             cfg.get(section, 'Host', fallback='127.0.0.1'),
            'port':             cfg.getint(section, 'Port', fallback=5432),
            'dbname':           cfg.get(section, 'DB',   fallback=default_db),
            'user':             cfg.get(section, 'User', fallback='postgres'),
            'password':         cfg.get(section, 'Pass', fallback=''),
            'application_name': 'LarcSuperviseur',
            'connect_timeout':  5,
        }

    def connect_intranet(self) -> bool:
        if not _PG_OK:
            _log("connect_intranet: psycopg2 non installé")
            return False
        try:
            if self._intranet:
                self._intranet.close()
            params = self._pg_params('IntranetDatabase')
            self._intranet = psycopg2.connect(**params)
            self._intranet.autocommit = True
            self._mode = DBMode.INTRANET
            self._server_mode = DBMode.INTRANET
            _log("connect_intranet: connexion réussie")
            return True
        except Exception as e:
            _log(f"connect_intranet: échec : {e}")
            self._mode = DBMode.NONE
            self._server_mode = DBMode.NONE
            return False

    def connect_cloud(self) -> bool:
        if not _PG_OK:
            _log("connect_cloud: psycopg2 non installé")
            return False
        try:
            if self._cloud:
                self._cloud.close()
            params = self._pg_params('SupabaseDatabase')
            self._cloud = psycopg2.connect(**params)
            self._cloud.autocommit = True
            self._mode = DBMode.CLOUD
            self._server_mode = DBMode.CLOUD
            _log("connect_cloud: connexion réussie")
            return True
        except Exception as e:
            _log(f"connect_cloud: échec : {e}")
            self._mode = DBMode.NONE
            self._server_mode = DBMode.NONE
            return False

    def disconnect_all(self) -> None:
        for attr in ('_intranet', '_cloud'):
            conn = getattr(self, attr, None)
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
                setattr(self, attr, None)
        self._mode = DBMode.NONE
        self._server_mode = DBMode.NONE

    @property
    def server_conn(self):
        if self._server_mode == DBMode.INTRANET:
            return self._intranet
        if self._server_mode == DBMode.CLOUD:
            return self._cloud
        return None

    @property
    def mode(self) -> DBMode:
        return self._mode

    @property
    def server_mode(self) -> DBMode:
        return self._server_mode

    @property
    def is_server_connected(self) -> bool:
        return self.server_conn is not None

    def __del__(self) -> None:
        self.disconnect_all()


db = Database()
