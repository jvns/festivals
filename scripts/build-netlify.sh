set -euo pipefail
export PYTHONPATH=.
pip3 install .
bash scripts/generate.sh
npm install --save-dev lightningcss-cli
find site -name '*.css' -exec lightningcss --targets '>= 0.25%' {} -o {} \;
