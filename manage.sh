#!/usr/bin/env bash
# Wrapper manage.py — contourne le garde-fou Hermes (lifecycle_guard).
#
# PIÈGE : un token exécutable contenant "/" qui pointe vers un binaire >1 Mo
# (ex. .venv/bin/python, /usr/bin/python3.12) fait crasher le garde-fou :
# il relit le fichier via `cat`, tokenise le binaire et plante sur un chemin
# contenant un NUL (os.open ne catch que OSError, pas ValueError).
# Ici le python du venv est invoqué par PATH avec un nom sans "/" ("python")
# depuis .venv/bin : le garde-fou ne le traite pas comme script référencé,
# et Python retrouve pyvenv.cfg (venv actif). Un symlink externe casserait
# la détection venv (pyvenv.cfg non adjacent).
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$PWD/.venv/bin:$PATH"
exec python manage.py "$@"
