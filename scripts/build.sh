set -euo pipefail

export PYTHONPATH=.

# Scrape all festivals
python3 src/mutek-2025/scrape.py
python3 src/fantasia-2025/scrape.py
python3 src/theatre-de-verdure-2025/scrape.py
python3 src/shakespeare-2025/scrape.py
python3 src/nuits-d-afrique-2025/scrape.py
python3 src/fireworks-2025/scrape.py
python3 src/haiti-en-folie-2025/scrape.py

# Generate individual festival pages
python3 src/mutek-2025/generate.py
python3 src/fantasia-2025/generate.py
python3 src/theatre-de-verdure-2025/generate.py
python3 src/shakespeare-2025/generate.py
python3 src/nuits-d-afrique-2025/generate.py
python3 src/fireworks-2025/generate.py
python3 src/haiti-en-folie-2025/generate.py
rsync -a src/fringe-2025/ site/2025/fringe/

# Generate main combined page
python3 src/generate.py
