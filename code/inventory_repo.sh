#!/usr/bin/env bash
# Inventaire des donnees de programmes et d'examens deja presentes dans le depot (lecture seule).
cd /workspaces/Curriculum
echo "== fichiers data (hors raw volumineux) =="
find data -maxdepth 3 -type f -not -path 'data/raw/oecd/*' -printf '%s\t%p\n' | sort -k2 | head -200
echo "== mots-cles programmes / pays / notions =="
grep -rIl -i -E 'curriculum|programme|notion|prerequis|prerequisite' --include='*.csv' --include='*.json' --include='*.md' --include='*.py' . 2>/dev/null | grep -v -E '^./(\.git|venv|\.venv)/' | head -60
echo "== colonnes des csv candidats =="
for f in $(find data -maxdepth 3 -name '*.csv' -not -path 'data/raw/oecd/*' | head -40); do echo "-- $f"; head -n 1 "$f" | cut -c1-300; wc -l < "$f"; done
