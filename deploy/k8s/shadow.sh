#!/usr/bin/env bash
# Shadow deployment: the live track (the previous stable release) answers users; every request
# is also mirrored to the shadow track (the new release), whose answers are discarded.
# The new release passes if it handled every mirrored request without a server error.
#   bash deploy/k8s/shadow.sh deploy <image>   shadow gets <image>; live gets the stable release
#   bash deploy/k8s/shadow.sh analyse          send test traffic and compare
#   bash deploy/k8s/shadow.sh stop             scale the shadow track to 0
#   bash deploy/k8s/shadow.sh status
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

LIVE=aceest-shadow-live
SHADOW=aceest-shadow
ROUTER=aceest-shadow-router
PORT=30085
REQUESTS=${SHADOW_REQUESTS:-30}

# apply_tracks <live image> <shadow image> <shadow replicas>
apply_tracks() {
    local out
    out=$(apply shadow.yaml LIVE_IMAGE="$1" SHADOW_IMAGE="$2" SHADOW_REPLICAS="$3")
    if grep -q "configmap/$ROUTER configured" <<< "$out"; then
        kc rollout restart deployment/"$ROUTER" > /dev/null   # nginx reads its config at start
    fi
}

analyse() {
    local base run i code paths live_errors=0 mirrored shadow_errors lines
    base=$(url "$PORT")
    smoke_test "$PORT" || return 1
    run="shadow-check-$(date +%s)"
    paths=(/programs /programs/FL /version)
    log "Shadow analysis: $REQUESTS requests to $base (tagged ?check=$run-N)"
    for i in $(seq 1 "$REQUESTS"); do
        code=$(curl -s -m 3 -o /dev/null -w '%{http_code}' "$base${paths[$((i % 3))]}?check=$run-$i" || true)
        if [ "$code" != 200 ]; then
            live_errors=$((live_errors + 1))
        fi
    done
    sleep 2
    # gunicorn access log: ... "GET /programs?check=... HTTP/1.0" <status> ...
    lines=$(kc logs deployment/"$SHADOW" --since=10m 2> /dev/null | grep "check=$run-" || true)
    mirrored=$(printf '%s\n' "$lines" | grep -c "check=$run-" || true)
    shadow_errors=$(printf '%s\n' "$lines" | awk '$9 >= 500' | wc -l)
    log "Users got $REQUESTS answers from the live track ($live_errors errors);" \
        "the shadow received $mirrored copies ($shadow_errors server errors)"
    if [ "$live_errors" -gt 0 ] || [ "$mirrored" -lt "$REQUESTS" ] || [ "$shadow_errors" -gt 0 ]; then
        log "Shadow analysis FAILED"
        return 1
    fi
    log "Shadow analysis passed"
}

deploy() {
    local image=$1 live
    ensure_namespace
    live=$(stable_image)
    live=${live:-$(image_of "$LIVE")}
    live=${live:-$image}
    log "Shadow: live track = $live, shadow track = $image"
    apply_tracks "$live" "$image" 1
    if ! { wait_ready "$LIVE" && wait_ready "$SHADOW" && wait_ready "$ROUTER" && analyse; }; then
        log "Shadow test FAILED - users only ever saw the live track; stopping the shadow"
        stop
        return 1
    fi
    log "Shadow running on port $PORT: $image receives a copy of all traffic"
}

stop() {
    apply_tracks "$(image_of "$LIVE")" "$(image_of "$SHADOW")" 0
    log "Shadow track stopped"
}

status() {
    kc get deployments -l strategy=shadow -o wide
}

case "${1:-}" in
    deploy) deploy "${2:?usage: $0 deploy <image>}" ;;
    analyse) analyse ;;
    stop) stop ;;
    status) status ;;
    *)
        echo "usage: $0 deploy <image> | analyse | stop | status" >&2
        exit 2
        ;;
esac
