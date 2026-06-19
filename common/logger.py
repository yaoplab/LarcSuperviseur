import os
from datetime import datetime

LOG_TO_FILE = True

LOG_FILENAME = 'superviseur.log'

_LOG_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', LOG_FILENAME
))


def log(msg: str) -> None:
    if not LOG_TO_FILE:
        return
    try:
        with open(_LOG_PATH, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


def set_log_to_file(value: bool) -> None:
    global LOG_TO_FILE
    LOG_TO_FILE = value


def get_log_path() -> str:
    return _LOG_PATH


def set_log_filename(name: str) -> None:
    global _LOG_PATH, LOG_FILENAME
    LOG_FILENAME = name
    _LOG_PATH = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', name
    ))
