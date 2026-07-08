#!/usr/bin/env python3
"""
Gestionnaire i18n pour les apps Larc (LarcSuperviseur, LarcSecretaire, LarcHub).
Gère fr.json et en.json simultanément.

Usage:
    python tools/i18n_manager.py status          # Stats + couverture
    python tools/i18n_manager.py missing         # Clés manquantes dans les JSON
    python tools/i18n_manager.py unused          # Clés inutilisées dans le code
    python tools/i18n_manager.py add key "fr" "en"   # Ajouter ou mettre à jour une clé
    python tools/i18n_manager.py search "texte"  # Chercher par valeur FR
    python tools/i18n_manager.py sync            # Ajouter les clés manquantes auto
    python tools/i18n_manager.py export          # Exporter en CSV
"""

import csv
import json
import re
import sys
from pathlib import Path

L10N_DIR = Path(r"C:\Projets\LarcCommon\larccommon\l10n")
FR_PATH = L10N_DIR / "fr.json"
EN_PATH = L10N_DIR / "en.json"
PROJETS = [r"C:\Projets\LarcSuperviseur", r"C:\Projets\LarcSecretaire", r"C:\Projets\LarcHub"]


def load():
    """Charge les deux JSON."""
    fr = json.loads(FR_PATH.read_text(encoding="utf-8"))
    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    return fr, en


def save(fr, en):
    """Sauvegarde les deux JSON."""
    FR_PATH.write_text(json.dumps(fr, indent=2, ensure_ascii=False), encoding="utf-8")
    EN_PATH.write_text(json.dumps(en, indent=2, ensure_ascii=False), encoding="utf-8")


def scan_code():
    """Extrait toutes les clés _('key') du code source."""
    keys = set()
    for projet in PROJETS:
        for f in Path(projet).rglob("*.py"):
            if "__pycache__" in str(f):
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"""_\s*\(\s*['"]([^'"]+)['"]\s*\)""", text):
                k = m.group(1)
                if "." in k and not k.startswith(("_", "..")):
                    keys.add(k)
    return keys


def cmd_status():
    fr, en = load()
    code = scan_code()
    mf = code - set(fr.keys())
    me = code - set(en.keys())
    nf = set(fr.keys()) - code
    # Filtrer les faux positifs (noms de modules Python)
    modules = {
        k
        for k in mf
        if "__" in k
        or k.count(".") >= 3
        and not k.split(".")[0].startswith(
            (
                "login",
                "chart",
                "common",
                "event",
                "main",
                "student",
                "sidebar",
                "kpi",
                "history",
                "topbar",
                "timetable",
                "context_menu",
                "app",
                "network",
                "class_panel",
                "dossier",
                "notes",
                "parent",
                "password",
                "sec_",
                "supervisor",
                "student_form",
                "hub",
                "event_dialog",
                "event_label",
                "card",
                "group_panel",
                "loading_message",
            )
        )
    }
    mf_reelles = mf - modules
    nf_reelles = nf - modules
    me_reelles = me - modules
    print(f"{'=' * 50}")
    print("  GESTIONNAIRE i18n — Larc Apps")
    print(f"{'=' * 50}")
    print(f"  fr.json         : {len(fr):>4} clés")
    print(f"  en.json         : {len(en):>4} clés")
    print(f"  Clés dans code  : {len(code):>4}")
    print()
    print(f"  [OK] Complètes    : {len(code - mf_reelles - me_reelles):>4}")
    if mf_reelles:
        print(f"  [!!]  Manque fr    : {len(mf_reelles):>4}")
    if me_reelles:
        print(f"  [!!]  Manque en    : {len(me_reelles):>4}")
    if nf_reelles:
        print(f"  [i]   Inutilisées : {len(nf_reelles):>4}")
    if modules:
        print(f"  [i]   Faux positifs: {len(modules):>4} (modules Python)")
    print()


def cmd_missing():
    fr, en = load()
    code = scan_code()
    for lang, d, label in [("fr", fr, "fr.json"), ("en", en, "en.json")]:
        miss = code - set(d.keys())
        if not miss:
            print(f"[OK] {label} : toutes les clés sont présentes")
        else:
            modules = {k for k in miss if "__" in k or k.count(".") >= 3}
            reelles = miss - modules
            if reelles:
                print(f"[!!]  {label} : {len(reelles)} clé(s) manquante(s) :")
                for k in sorted(reelles):
                    print(f"    - {k}")
            if modules:
                print(f"[i]  {label} : {len(modules)} faux positif(s) ignoré(s)")
    print()


def cmd_unused():
    fr, en = load()
    code = scan_code()
    for lang, d in [("fr", fr), ("en", en)]:
        unused = set(d.keys()) - code
        if unused:
            print(f"[i]  {lang}.json : {len(unused)} clé(s) inutilisée(s) dans le code")
            for k in sorted(unused)[:30]:
                print(f"    - {k}")
            if len(unused) > 30:
                print(f"    ... et {len(unused) - 30} autre(s)")
    print()


def cmd_add(key, fr_val, en_val):
    fr, en = load()
    if key in fr:
        print(f"[!!]  La clé '{key}' existe déjà (sera mise à jour)")
    fr[key] = fr_val
    en[key] = en_val
    save(fr, en)
    print(f"[OK] Clé '{key}' ajoutée : fr='{fr_val}' | en='{en_val}'")


def cmd_search(texte):
    fr, en = load()
    found = []
    for k, v in fr.items():
        if texte.lower() in v.lower():
            en_v = en.get(k, "—")
            found.append((k, v, en_v))
    if found:
        print(f"{len(found)} résultat(s) pour '{texte}':")
        print(f"{'Clé':40s} {'FR':30s} {'EN':30s}")
        print("-" * 100)
        for k, v_fr, v_en in sorted(found):
            print(f"{k:40s} {v_fr:30s} {v_en:30s}")
    else:
        print(f"Aucun résultat pour '{texte}'")
    print()


def cmd_sync():
    fr, en = load()
    code = scan_code()
    added = 0
    for k in sorted(code):
        if k not in fr or k not in en:
            fr[k] = fr.get(k, f"TODO: {k}")
            en[k] = en.get(k, f"TODO: {k}")
            added += 1
            print(f"  + {k}")
    if added:
        save(fr, en)
        print(f"[OK] {added} clé(s) ajoutée(s) avec des valeurs TODO")
    else:
        print("[OK] Rien à ajouter — toutes les clés sont présentes")


def cmd_export():
    fr, en = load()
    keys = sorted(set(list(fr.keys()) + list(en.keys())))
    out = sys.stdout
    writer = csv.writer(out)
    writer.writerow(["Key", "Français", "English", "Statut"])
    for k in keys:
        v_fr = fr.get(k, "")
        v_en = en.get(k, "")
        if v_fr and v_en:
            statut = "OK"
        elif v_fr:
            statut = "EN MANQUE"
        else:
            statut = "FR MANQUE"
        writer.writerow([k, v_fr, v_en, statut])


def help():
    print(__doc__)


if __name__ == "__main__":
    cmds = {
        "status": cmd_status,
        "missing": cmd_missing,
        "unused": cmd_unused,
        "add": cmd_add,
        "search": cmd_search,
        "sync": cmd_sync,
        "export": cmd_export,
        "help": help,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        help()
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "add":
        if len(sys.argv) < 5:
            print('Usage: python tools/i18n_manager.py add "ma.clef" "valeur fr" "english value"')
            sys.exit(1)
        cmd_add(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        cmds[cmd]()
