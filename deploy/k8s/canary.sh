#!/usr/bin/env bash
# Canary release: start 1 canary pod next to the 3 stable pods (about 25 % of the traffic),
# check it with real requests, then promote it to the stable track - or abort.
#   bash deploy/k8s/canary.sh deploy <image>   start + analyse + promote (abort on failure)
#   bash deploy/k8s/canary.sh start <image>    only start the canary (for a manual demo)
#   bash deploy/k8s/canary.sh analyse          send test traffic and check the canary
#   bash deploy/k8s/canary.sh promote          the stable track takes the canary's image
#   bash deploy/k8s/canary.sh abort            remove the canary; stable is untouched
#   bash deploy/k8s/canary.sh status
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

STABLE=aceest-canary-stable
CANARY=aceest-canary
PORT=30083
SAMPLES=${CANARY_SAMPLES:-60}

# apply_tracks <stable image> <canary image> <canary replicas>
apply_tracks() {
    apply canary.yaml STABLE_IMAGE="$1" CANARY_IMAGE="$2" CANARY_REPLICAS="$3" > /dev/null
}

start() {
    local image=$1 stable
    ensure_namespace
    stable=$(image_of "$STABLE")
    log "Canary: stable track runs ${stable:-nothing yet}; starting 1 canary pod with $image"
    apply_tracks "${stable:-$image}" "$image" 1
    wait_ready "$STABLE" && wait_ready "$CANARY"
}

analyse() {
    local base i code served_by version stable=0 canary=0 errors=0 restarts
    base=$(url "$PORT")
    log "Canary analysis: $SAMPLES requests to $base"
    for i in $(seq 1 "$SAMPLES"); do
        read -r code served_by version <<< "$(request "$base/programs")"
        if [ "$code" != 200 ]; then
            errors=$((errors + 1))
        fi
        case "$served_by" in
            "$STABLE"-*) stable=$((stable + 1)) ;;
            "$CANARY"-*) canary=$((canary + 1)) ;;
        esac
        sleep 0.2
    done
    restarts=$(kc get pods -l strategy=canary,track=canary \
        -o jsonpath='{range .items[*]}{.status.containerStatuses[0].restartCount}{"\n"}{end}' \
        | awk '{ total += $1 } END { print total + 0 }')
    log "Stable answered $stable, canary answered $canary, errors $errors, canary restarts $restarts"
    if [ "$errors" -gt 0 ] || [ "$canary" -eq 0 ] || [ "$restarts" -gt 0 ]; then
        log "Canary analysis FAILED"
        return 1
    fi
    log "Canary analysis passed"
}

promote() {
    local image
    image=$(image_of "$CANARY")
    log "Promoting $image to the stable track"
    apply_tracks "$image" "$image" 0
    if ! wait_ready "$STABLE"; then
        log "Promotion FAILED - rolling the stable track back"
        undo "$STABLE" "$image" || true
        return 1
    fi
    log "Canary promoted: all traffic on port $PORT goes to $image"
}

abort() {
    log "Aborting the canary - the stable track keeps $(image_of "$STABLE")"
    apply_tracks "$(image_of "$STABLE")" "$(image_of "$CANARY")" 0
}

deploy() {
    if start "$1" && analyse; then
        promote
    else
        abort
        return 1
    fi
}

status() {
    kc get deployments -l strategy=canary -o wide
}

case "${1:-}" in
    deploy) deploy "${2:?usage: $0 deploy <image>}" ;;
    start) start "${2:?usage: $0 start <image>}" ;;
    analyse) analyse ;;
    promote) promote ;;
    abort) abort ;;
    status) status ;;
    *)
        echo "usage: $0 deploy <image> | start <image> | analyse | promote | abort | status" >&2
        exit 2
        ;;
esac
