#!/usr/bin/env bash
# Optional TCP heartbeat for a daemon you already started.
# Requires python3. Uses nc if present. Does not call ntfy unless SEEM_NTFY_TOPIC is set.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_KEY="your-secure-vsa-key-123"
DAEMON_PORT=5555
TWIN="brian_new"
if [[ -f config.json ]]; then
    eval "$(python3 - << 'PY'
import json
cfg = json.load(open("config.json"))
print(f"API_KEY={json.dumps(str(cfg.get('api_key', '')))}")
print(f"DAEMON_PORT={int(cfg.get('daemon_port', 5555))}")
PY
)"
fi

PAYLOAD=$(API_KEY="$API_KEY" TWIN="$TWIN" python3 - << 'PY'
import json, os
print(json.dumps({
    "auth_token": os.environ["API_KEY"],
    "intent": "monitor security logs and critical system resources",
    "twin": os.environ["TWIN"],
}))
PY
)

if ! command -v nc >/dev/null; then
    echo "nc is not installed; use the README socket example instead" >&2
    exit 1
fi

RESPONSE=$(printf '%s' "$PAYLOAD" | nc -q1 127.0.0.1 "$DAEMON_PORT") || {
    echo "ERROR: Daemon unreachable on 127.0.0.1:$DAEMON_PORT" >&2
    exit 1
}
echo "$RESPONSE"
if [[ -n "${SEEM_NTFY_TOPIC:-}" ]]; then
    echo "SEEM_NTFY_TOPIC is set; this script does not post externally." >&2
fi
exit 0
