#!/usr/bin/env bash
# Local installer for this repository.
# Does not clone other repos, does not git pull, and does not use sudo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true; shift ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

echo "SEEM Cognitive Microservice local bootstrap"
echo "Repo: $ROOT"
echo "Dry run: $DRY_RUN"

command -v python3 >/dev/null || { echo "Python 3 is required" >&2; exit 1; }
python3 - << 'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10+ required")
print(f"Python {sys.version.split()[0]} OK")
PY

if $DRY_RUN; then
    echo "Would create .venv, pip install -r requirements.txt, and copy config.json.example if needed."
    exit 0
fi

if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi
.venv/bin/pip install -r requirements.txt
if [[ ! -f config.json ]]; then
    cp config.json.example config.json
    echo "Wrote config.json from config.json.example (placeholder api_key, not a live credential)."
fi

echo
echo "Ready."
echo "  source .venv/bin/activate"
echo "  python seem.py init brian_new"
echo "  python seem.py do \"note a local route\""
echo "  python seem.py status"
echo "  pytest -q"
echo "systemd/seem-agent.service is a template only. This script does not install it."
