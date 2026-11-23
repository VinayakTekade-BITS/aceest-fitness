#!/usr/bin/env bash
# Helpers shared by the deployment scripts in this folder. Sourced, not run directly.
set -euo pipefail

NS=aceest
K8S_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../k8s" && pwd)"
ROLLOUT_TIMEOUT=${ROLLOUT_TIMEOUT:-180s}

log() { echo "[$(date +%H:%M:%S)] $*"; }

kc() { kubectl -n "$NS" "$@"; }

# render <template> KEY=VALUE... : print k8s/<template> with every __KEY__ replaced by VALUE
render() {
    local template="$K8S_DIR/$1" args=() pair
    shift
    for pair in "$@"; do
        args+=(-e "s|__${pair%%=*}__|${pair#*=}|g")
    done
    sed "${args[@]}" "$template"
}

# apply <template> KEY=VALUE... : render the template and apply it
apply() { render "$@" | kubectl apply -f -; }

ensure_namespace() { kubectl apply -f "$K8S_DIR/namespace.yaml" > /dev/null; }

# image of a deployment's container; empty if the deployment does not exist yet
image_of() {
    kc get deployment "$1" -o jsonpath='{.spec.template.spec.containers[0].image}' 2> /dev/null || true
}

# the image of the last build that passed every deploy stage (see release.sh)
stable_image() {
    kc get configmap aceest-release -o jsonpath='{.data.image}' 2> /dev/null || true
}

wait_ready() { kc rollout status deployment/"$1" --timeout="$ROLLOUT_TIMEOUT"; }

# undo <deployment> <failed image> : go back to the previous revision, then delete the failed
# revision, so that a later manual rollback cannot bring the failed image back
undo() {
    local rs
    kc rollout undo deployment/"$1" > /dev/null || return 1
    wait_ready "$1" || return 1
    for rs in $(kc get replicasets -o jsonpath='{range .items[*]}{.metadata.name} {.metadata.ownerReferences[0].name} {.spec.replicas} {.spec.template.spec.containers[0].image}{"\n"}{end}' \
        | awk -v d="$1" -v i="$2" '$2 == d && $3 == 0 && $4 == i { print $1 }'); do
        kc delete replicaset "$rs" > /dev/null
    done
    log "$1 is back on $(image_of "$1")"
}

node_ip() {
    kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}'
}

url() { echo "http://$(node_ip):$1"; }

# smoke_test <node port> [curl args] : /health, /ready and /programs answer 200
# (each path is retried for ~20 s, in case pods are still starting)
smoke_test() {
    local base path i code
    base=$(url "$1")
    shift
    for path in /health /ready /programs; do
        for i in $(seq 1 10); do
            code=$(curl -s -m 3 -o /dev/null -w '%{http_code}' "$@" "$base$path" || true)
            if [ "$code" = 200 ]; then
                break
            fi
            if [ "$i" = 10 ]; then
                log "Smoke test FAILED: $base$path answered $code $*"
                return 1
            fi
            sleep 2
        done
    done
    log "Smoke test passed: $base $*"
}

# request <url> [curl args] : one request; prints "<status> <X-Served-By> <X-App-Version>"
request() {
    local target=$1
    shift
    { curl -s -m 3 -D - -o /dev/null "$@" "$target" || true; } | tr -d '\r' | awk -F': ' '
        NR == 1 { split($0, status, " "); code = status[2] }
        tolower($1) == "x-served-by" { by = $2 }
        tolower($1) == "x-app-version" { version = $2 }
        END { print (code == "" ? "000" : code), (by == "" ? "-" : by), (version == "" ? "-" : version) }'
}

# header <url> <name> [curl args] : value of one response header
header() {
    local target=$1 name=$2
    shift 2
    { curl -s -m 3 -D - -o /dev/null "$@" "$target" || true; } | tr -d '\r' \
        | awk -F': ' -v name="$name" 'tolower($1) == tolower(name) { print $2 }'
}
