import os
import socket
import configparser
import urllib.request
from enum import Enum

from .config_loader import find_cfg


class NetworkMode(Enum):
    INTRANET = 'intranet'
    INTERNET = 'internet'
    OFFLINE  = 'offline'


def detect_network() -> tuple[bool, bool]:
    cfg = configparser.ConfigParser()
    cfg.read(find_cfg())
    host = cfg.get('IntranetDatabase', 'Host', fallback='192.168.2.90')
    port = cfg.getint('IntranetDatabase', 'Port', fallback=5432)

    intranet_ok = False
    internet_ok = False

    try:
        with socket.create_connection((host, port), timeout=1.5):
            intranet_ok = True
    except OSError:
        pass

    try:
        urllib.request.urlopen('https://www.google.com', timeout=3)
        internet_ok = True
    except Exception:
        pass

    return (intranet_ok, internet_ok)
