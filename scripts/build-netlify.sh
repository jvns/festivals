set -euo pipefail
export PYTHONPATH=.
pip install -r requirements.txt
source scripts/generate.sh
npm install --save-dev lightningcss-cli
find site -name '*.css' -exec lightningcss --targets '>= 0.25%' {} -o {} \;
