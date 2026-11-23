#!/usr/bin/env bash
# Sends a request to every deployed strategy twice a second and prints the status codes, then
# a summary (also on Ctrl+C). Run it in a second terminal during a deployment.
#   bash deploy/k8s/watch.sh [path] [seconds]      default: /health for 120 seconds
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CHECK_PATH=${1:-/health}
DURATION=${2:-120}
declare -A SERVICES=([30081]=aceest-rolling [30082]=aceest-bluegreen [30083]=aceest-canary
    [30084]=aceest-ab-router [30085]=aceest-shadow-router)
declare -A NAMES=([30081]=rolling [30082]=blue-green [30083]=canary [30084]=ab-testing
    [30085]=shadow)
declare -A TOTAL=() FAILED=()
PORTS=()
existing=$(kc get services -o name 2> /dev/null || true)
for port in 30081 30082 30083 30084 30085; do
    if grep -qx "service/${SERVICES[$port]}" <<< "$existing"; then
        PORTS+=("$port")
    fi
done
IP=$(node_ip)

summary() {
    local port
    echo
    echo "Summary for $CHECK_PATH:"
    for port in "${PORTS[@]}"; do
        printf '  %-11s %5d requests, %4d not 200\n' "${NAMES[$port]}" "${TOTAL[$port]:-0}" \
            "${FAILED[$port]:-0}"
    done
}
trap 'summary; exit 0' INT

end=$((SECONDS + DURATION))
while [ "$SECONDS" -lt "$end" ]; do
    line=$(date +%T)
    for port in "${PORTS[@]}"; do
        code=$(curl -s -m 2 -o /dev/null -w '%{http_code}' "http://$IP:$port$CHECK_PATH" || true)
        line+="  ${NAMES[$port]}=$code"
        TOTAL[$port]=$((${TOTAL[$port]:-0} + 1))
        if [ "$code" != 200 ]; then
            FAILED[$port]=$((${FAILED[$port]:-0} + 1))
        fi
    done
    echo "$line"
    sleep 0.5
done
summary
