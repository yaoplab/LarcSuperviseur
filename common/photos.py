import os
import glob
import shutil
import urllib.request
from .session import session, ConnMode
from .app_config import app_config
from .logger import log

SUPABASE_REF = "crvyxfsuvwqxzlhsfbwq"
STORAGE_BUCKET = "student-photos"
PHOTO_EXT = ".png"
_STORAGE_URL = f"https://{SUPABASE_REF}.supabase.co/storage/v1/object/public/{STORAGE_BUCKET}"
_SUPABASE_TIMEOUT = 5


def _intranet_path(sid: int) -> str:
    return os.path.join(app_config.get("photos_dir"), f"{sid}{PHOTO_EXT}")


def _cache_path(sid: int) -> str:
    return os.path.join(app_config.get("photos_cache_dir"), f"{sid}{PHOTO_EXT}")


def _supabase_download(sid: int, dest: str) -> bool:
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        url = f"{_STORAGE_URL}/{sid}{PHOTO_EXT}"
        with urllib.request.urlopen(url, timeout=_SUPABASE_TIMEOUT) as resp:
            with open(dest, 'wb') as f:
                f.write(resp.read())
        return True
    except Exception as e:
        log(f"Photos: echec telechargement {sid}{PHOTO_EXT} ({e})")
        return False


def get_photo_path(sid: int) -> str:
    cache = _cache_path(sid)
    if os.path.isfile(cache):
        return cache

    if session.conn_mode == ConnMode.INTRANET:
        path = _intranet_path(sid)
        if os.path.isfile(path):
            return path
        return cache

    _supabase_download(sid, cache)
    return cache


def ensure_cached(sid: int) -> bool:
    cache = _cache_path(sid)
    if os.path.isfile(cache):
        return True

    src = _intranet_path(sid)
    if os.path.isfile(src):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        shutil.copy2(src, cache)
        return True

    return False


def get_uncached_ids() -> list[int]:
    ids_src = set()
    ids_cached = set()

    src_dir = app_config.get("photos_dir")
    if os.path.isdir(src_dir):
        for f in glob.glob(os.path.join(src_dir, "*.png")):
            sid = int(os.path.splitext(os.path.basename(f))[0])
            ids_src.add(sid)

    cache_dir = app_config.get("photos_cache_dir")
    if os.path.isdir(cache_dir):
        for f in glob.glob(os.path.join(cache_dir, "*.png")):
            sid = int(os.path.splitext(os.path.basename(f))[0])
            ids_cached.add(sid)

    return sorted(ids_src - ids_cached)


# --- Pr\u00e9chargeur Qt r\u00e9utilisable (LarcSuperviseur, LarcSecretaire, etc.) ---
try:
    from PySide6.QtCore import QThread, Signal

    class PhotoPreloader(QThread):
        progress = Signal(int, int, str)
        done = Signal(int, int)

        def __init__(self, student_ids: list[int], parent=None):
            super().__init__(parent)
            self._student_ids = student_ids
            self._cancelled = False

        def run(self):
            loaded = 0
            total = len(self._student_ids)
            for i, sid in enumerate(self._student_ids):
                if self._cancelled:
                    break
                self.progress.emit(i + 1, total, str(sid))
                if ensure_cached(sid):
                    loaded += 1
            self.done.emit(loaded, total - loaded)

        def cancel(self):
            self._cancelled = True

except ImportError:
    class PhotoPreloader:
        pass
