"""AuthManager + OAuth2 PKCE."""
import os
import hashlib
import secrets
import base64
import configparser
import threading
import webbrowser
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Tuple

from .session import AuthResult, UserRole
from .database import db, DBMode
from .logger import log
from .config_loader import find_cfg


def _deduce_role_superviseur(is_dir: bool, is_coord: bool, is_sup: bool) -> UserRole:
    if is_dir: return UserRole.ADMIN
    if is_coord: return UserRole.COORD
    if is_sup: return UserRole.SUPERVISEUR
    return UserRole.SUPERVISEUR


def _load_active_term(cur) -> Tuple[int, str]:
    try:
        cur.execute("SELECT id, label FROM larcauth_term ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return row[0], row[1]
    except Exception:
        pass
    return 0, ''


# ---------------------------------------------------------------------------
# OAuth2 PKCE — Google Workspace @arc-en-ciel.org
# ---------------------------------------------------------------------------

class _CallbackHandler(BaseHTTPRequestHandler):
    code:  str             = ''
    event: threading.Event = threading.Event()

    def do_GET(self) -> None:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'code' in qs:
            _CallbackHandler.code = qs['code'][0]
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(
            ('<html><body style="font-family:sans-serif;text-align:center;padding:40px">'
             '<h2>✔ Authentification réussie</h2>'
             '<p>Vous pouvez fermer cet onglet et revenir à {0}.</p>'
             '</body></html>').format(OAuth2Manager.APP_DISPLAY).encode('utf-8')
        )
        _CallbackHandler.event.set()

    def log_message(self, *args) -> None:
        pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


class OAuth2Manager:
    PORT           = 8765
    HOSTED_DOMAIN  = 'arc-en-ciel.org'
    APP_DISPLAY    = 'LarcSuperviseur'
    REDIRECT       = f'http://localhost:{PORT}/callback'
    GOOGLE_AUTH    = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_TOKEN   = 'https://oauth2.googleapis.com/token'

    @classmethod
    def authenticate(cls) -> Tuple[bool, AuthResult, str]:
        cfg = configparser.ConfigParser()
        cfg.read(find_cfg())
        client_id     = cfg.get('OAuth2', 'ClientID',     fallback='')
        client_secret = cfg.get('OAuth2', 'ClientSecret', fallback='')
        if not client_id:
            return False, AuthResult(), 'ClientID OAuth2 manquant dans config.ini'

        verifier  = _b64url(secrets.token_bytes(32))
        challenge = _b64url(hashlib.sha256(verifier.encode('ascii')).digest())
        state     = _b64url(secrets.token_bytes(16))

        params = {
            'client_id':             client_id,
            'redirect_uri':          cls.REDIRECT,
            'response_type':         'code',
            'scope':                 'openid email profile',
            'code_challenge':        challenge,
            'code_challenge_method': 'S256',
            'state':                 state,
            'hd':                    cls.HOSTED_DOMAIN,
            'access_type':           'offline',
            'prompt':                'select_account',
        }
        auth_url = cls.GOOGLE_AUTH + '?' + urllib.parse.urlencode(params)

        _CallbackHandler.code = ''
        _CallbackHandler.event.clear()

        srv = HTTPServer(('localhost', cls.PORT), _CallbackHandler)
        threading.Thread(target=srv.handle_request, daemon=True).start()
        webbrowser.open(auth_url)

        if not _CallbackHandler.event.wait(timeout=120):
            srv.server_close()
            return False, AuthResult(), 'Délai de 2 min dépassé'

        srv.server_close()
        code = _CallbackHandler.code
        if not code:
            return False, AuthResult(), 'Code OAuth2 non reçu'

        token_body = urllib.parse.urlencode({
            'code':          code,
            'client_id':     client_id,
            'client_secret': client_secret,
            'redirect_uri':  cls.REDIRECT,
            'grant_type':    'authorization_code',
            'code_verifier': verifier,
        }).encode()
        try:
            req = urllib.request.Request(
                cls.GOOGLE_TOKEN, data=token_body, method='POST',
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                tokens = json.loads(resp.read())
        except Exception as e:
            return False, AuthResult(), f'Échange de token échoué : {e}'

        id_token = tokens.get('id_token', '')
        if not id_token:
            return False, AuthResult(), 'Token ID absent de la réponse'

        parts = id_token.split('.')
        if len(parts) < 2:
            return False, AuthResult(), 'Token ID malformé'
        pad     = '=' * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))

        email = payload.get('email', '')
        hd    = payload.get('hd', '')
        if hd != cls.HOSTED_DOMAIN:
            return False, AuthResult(), f'Domaine non autorisé : {hd or "(aucun)"}'

        conn = db.server_conn
        if conn is None:
            return True, AuthResult(email=email, full_name=payload.get('name', '')), ''

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, first_name, last_name, "
                    "type_director, type_coordonator, type_supervisor "
                    "FROM public.larcauth_aecuser WHERE LOWER(email) = %s",
                    (email.lower(),)
                )
                row = cur.fetchone()
            if row is None:
                return False, AuthResult(), f'Utilisateur {email} non trouvé'

            user_id, first_name, last_name = row[0], row[1], row[2]
            is_dir, is_coord, is_sup = row[3], row[4], row[5]
            full_name = f"{first_name} {last_name}".strip()

            if not (is_dir or is_coord or is_sup):
                return False, AuthResult(), (
                    'Accès réservé aux superviseurs, coordinateurs et administrateurs.')

            role = _deduce_role_superviseur(is_dir, is_coord, is_sup)

            with conn.cursor() as cur:
                term_id, term_label = _load_active_term(cur)

            return True, AuthResult(
                user_id=user_id, email=email, full_name=full_name,
                role=role, term_id=term_id, term_label=term_label,
            ), ''
        except Exception as e:
            return False, AuthResult(), str(e)
