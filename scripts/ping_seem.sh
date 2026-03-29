#!/usr/bin/env bash
# scripts/ping_seem.sh - Raw TCP heartbeat using netcat

set -euo pipefail

API_KEY="your-secure-vsa-key-123"
TWIN="brian_new"
NTFY_TOPIC="brian_seem_alerts"
HEALTH_LOG="$HOME/seem_health.log"
DAEMON_PORT=5555

PAYLOAD=$(cat <<EOF
{
  "auth_token": "$API_KEY",
  "intent": "monitor security logs and critical system resources",
  "twin": "$TWIN"
}
EOF
)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pinging SEEM daemon on port $DAEMON_PORT..." >> "$HEALTH_LOG"

RESPONSE=$(echo "$PAYLOAD" | nc -q1 localhost $DAEMON_PORT) || {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Daemon unreachable" >> "$HEALTH_LOG"
    notify-send -u critical "SEEM ERROR" "Daemon unreachable"
    exit 1
}

STATUS=$(echo "$RESPONSE" | jq -r '.status // "UNKNOWN"' 2>/dev/null || echo "UNKNOWN")
FIDELITY=$(echo "$RESPONSE" | jq -r '.fidelity // "unknown"' 2>/dev/null || echo "unknown")
EFFECT=$(echo "$RESPONSE" | jq -r '.effect // "No effect reported"' 2>/dev/null || echo "No effect reported")

LOG_LINE="[$(date '+%Y-%m-%d %H:%M:%S')] SEEM $STATUS | Fidelity: $FIDELITY | $EFFECT"
echo "$LOG_LINE" >> "$HEALTH_LOG"

if [[ "$STATUS" == "SUCCESS" ]]; then
    true
elif [[ "$RESPONSE" == *"ALERT: SECURITY"* || "$RESPONSE" == *"CRITICAL"* ]]; then
    notify-send -u critical "SEEM SECURITY ALERT" "$EFFECT"
    curl -s -d "SEEM CRITICAL ALERT: $EFFECT (fidelity $FIDELITY)" "ntfy.sh/$NTFY_TOPIC" >/dev/null || true
    echo "$LOG_LINE – ALERT ESCALATED" >> "$HEALTH_LOG"
elif [[ "$FIDELITY" != "unknown" && $(echo "$FIDELITY < 0.96" | bc -l 2>/dev/null || echo 0) -eq 1 ]]; then
    notify-send -u normal "SEEM Warning" "Cognitive Drift Detected\nFidelity: $FIDELITY\n$EFFECT"
    echo "$LOG_LINE – DRIFT WARNING" >> "$HEALTH_LOG"
else
    notify-send -u normal "SEEM Failure" "Unexpected response:\n$RESPONSE"
    echo "$LOG_LINE – GENERIC FAILURE" >> "$HEALTH_LOG"
fi

exit 0
