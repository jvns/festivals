set -euo pipefail
export PYTHONPATH=.
pip3 install .
# TODO: put this back when we start having content for 2026
# bash scripts/generate.sh

mkdir -p site
mv archive/2025 site/2025
mv archive/index.html site/index.html

npm install --save-dev lightningcss-cli
find site -name '*.css' -exec lightningcss --targets '>= 0.25%' {} -o {} \;
