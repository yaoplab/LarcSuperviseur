# Common — Infrastructure partagée

En attente de migration vers `LarcCommon`. Actuellement dans `common/`.

| Module | Rôle | Lignes |
|---|---|---|
| `database.py` | Singleton `db` : connexions Intranet + Cloud PostgreSQL | 155 |
| `session.py` | `session` global : user, role, conn_mode | 47 |
| `auth.py` | OAuth2 PKCE Google + auth locale | 198 |
| `network.py` | `detect_network()` → (intranet_ok, internet_ok) | 48 |
| `theme.py` | ThemeManager : 3 thèmes MD3 (Light/Dark/Contrast) | 244 |
| `logger.py` | `log()` vers fichier | 34 |
| `photos.py` | `get_photo_path(sid)` : locale ou Supabase | 41 |
| `app_config.py` | `app_config` : clés/valeurs depuis `larcauth_config` | 40 |
| `event_helpers.py` | `event_icon()` / `event_color()` | 29 |

## Migration vers LarcCommon

Ces modules seront extraits dans un package `LarcCommon` partagé entre LarcSuperviseur, eLarcProfPy et LarcSecretaire.

Chaque projet ajoutera ses spécificités :
- Rôles utilisateur (SUPERVISEUR / COORD / ADMIN vs PROF / SECR)
- Thèmes (couleurs spécifiques à chaque métier)
- Modules additionnels (sync, grid_config pour Prof)
