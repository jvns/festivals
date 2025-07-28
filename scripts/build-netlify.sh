set -euo pipefail
export PYTHONPATH=.
pip install -r requirements.txt
source scripts/generate.sh
