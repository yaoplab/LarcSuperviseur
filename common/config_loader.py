import os
from typing import List


def find_cfg(sibling_dirs: List[str] = None) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    if sibling_dirs is None:
        sibling_dirs = ['eLarcProfPy']
    candidates = [os.path.join(here, '..', 'config.ini')]
    for d in sibling_dirs:
        candidates.append(os.path.join(here, '..', '..', d, 'config.ini'))
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.isfile(p):
            return p
    return os.path.normpath(candidates[0])
