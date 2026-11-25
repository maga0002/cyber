#!/usr/bin/env bash
# Start de Cyberweerbaarheid Monitor (macOS / Linux).
# De eerste keer worden de benodigde pakketten geïnstalleerd.
set -e
cd "$(dirname "$0")"

PY=python3
command -v $PY >/dev/null 2>&1 || PY=python
if ! command -v $PY >/dev/null 2>&1; then
  echo "Python is niet gevonden. Installeer Python 3.11 of nieuwer via https://www.python.org/downloads/"
  exit 1
fi
if ! $PY -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "Python 3.11 of nieuwer is nodig (gevonden: $($PY --version))."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Eerste keer: omgeving aanmaken en pakketten installeren..."
  $PY -m venv .venv
fi
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt

echo
echo "De app draait op http://127.0.0.1:5000  (stoppen met Ctrl+C)"
( sleep 2; (open http://127.0.0.1:5000 || xdg-open http://127.0.0.1:5000) >/dev/null 2>&1 ) &
exec .venv/bin/python run.py
