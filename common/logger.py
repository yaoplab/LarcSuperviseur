import os
from datetime import datetime

LOG_TO_FILE = True

_LOG_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'superviseur.log'
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
