#!/usr/bin/env bash
# Start de Cyberweerbaarheid Monitor (macOS / Linux).
# De eerste keer worden de benodigde pakketten geïnstalleerd.
set -e
cd "$(dirname "$0")"

# Zoek een Python van minimaal 3.11. macOS levert zelf een oudere python3 mee,
# dus kijk eerst naar specifieke versies en de standaard installatiemappen.
PY=""
for kandidaat in python3.14 python3.13 python3.12 python3.11 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
    /opt/homebrew/bin/python3 /usr/local/bin/python3 python3 python; do
  if command -v "$kandidaat" >/dev/null 2>&1 && \
     "$kandidaat" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$kandidaat"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.11 of nieuwer is niet gevonden."
  command -v python3 >/dev/null 2>&1 && echo "Gevonden: $(python3 --version) - die is te oud."
  echo "Installeer Python via https://www.python.org/downloads/ en start dit script opnieuw."
  exit 1
fi
echo "Python gebruikt: $PY ($("$PY" --version))"

# Een eerder (met een te oude Python) aangemaakte omgeving opnieuw opbouwen
if [ -x .venv/bin/python ] && ! .venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
  echo "Oude omgeving gevonden, wordt opnieuw aangemaakt..."
  rm -rf .venv
fi

if [ ! -d .venv ]; then
  echo "Eerste keer: omgeving aanmaken en pakketten installeren..."
  "$PY" -m venv .venv
fi
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt

echo
echo "De app draait op http://127.0.0.1:5000  (stoppen met Ctrl+C)"
( sleep 2; (open http://127.0.0.1:5000 || xdg-open http://127.0.0.1:5000) >/dev/null 2>&1 ) &
exec .venv/bin/python run.py
