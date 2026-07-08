"""Vérifie que toutes les clés _('key') utilisées dans le code existent dans fr.json et en.json."""

import json
import os
import re


def main():
    fr = set(
        json.load(open(r"C:\Projets\LarcCommon\larccommon\l10n\fr.json", encoding="utf-8")).keys()
    )
    en = set(
        json.load(open(r"C:\Projets\LarcCommon\larccommon\l10n\en.json", encoding="utf-8")).keys()
    )

    code_keys = set()
    for root, dirs, files in os.walk(r"C:\Projets"):
        dirs[:] = [d for d in dirs if d != "__pycache__" and "node_modules" not in d]
        for f in files:
            if not f.endswith(".py"):
                continue
            if "test_i18n" in f:
                continue
            text = open(os.path.join(root, f), encoding="utf-8").read()
            for m in re.finditer(r"""_\s*\(\s*['"]([^'"]+)['"]\s*\)""", text):
                k = m.group(1)
                if "." in k and not k.startswith(("__", "...", "....")):
                    code_keys.add(k)

    print(f"fr.json: {len(fr)} cles")
    print(f"en.json: {len(en)} cles")
    print(f"Code: {len(code_keys)} cles utilisees")
    print()

    mf = code_keys - fr
    me = code_keys - en
    nf = fr - code_keys

    if mf:
        print(f"Manque dans fr.json ({len(mf)}):")
        for k in sorted(mf)[:30]:
            print(f"  - {k}")
    if me:
        print(f"Manque dans en.json ({len(me)}):")
        for k in sorted(me)[:30]:
            print(f"  - {k}")
    if nf:
        print(f"Cles inutilisees dans fr.json ({len(nf)}):")
        for k in sorted(nf)[:20]:
            print(f"  - {k}")
    if not mf and not me:
        print("TOUT OK - toutes les cles sont presentes dans les deux fichiers JSON")
        return 0
    return len(mf) + len(me)


if __name__ == "__main__":
    exit(main())
