import os

_TRACE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'trace.log')
_ENABLED = os.path.isfile(_TRACE_FILE)
_logger = None


def trace(msg: str):
    if not _ENABLED:
        return
    global _logger
    if _logger is None:
        _logger = open(_TRACE_FILE, 'a', encoding='utf-8')
    _logger.write(f"{msg}\n")
    _logger.flush()


def enable():
    global _ENABLED, _logger
    if not _ENABLED:
        _ENABLED = True
        _logger = open(_TRACE_FILE, 'a', encoding='utf-8')
        trace("[trace] ACTIVÉ")


def disable():
    global _ENABLED, _logger
    if _logger:
        _logger.close()
    _logger = None
    _ENABLED = False
