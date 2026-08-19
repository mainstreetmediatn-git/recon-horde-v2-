#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
if [[ ! -f .env && -f .env.example ]]; then cp .env.example .env; fi
echo 'Horde environment ready. Review .env before enabling tool execution.'
