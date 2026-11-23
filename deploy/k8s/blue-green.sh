#!/usr/bin/env bash
# Blue-green: deploy the new version to the idle color, test it through the preview Service,
# then switch the live Service to it. The previous version keeps running on the other color.
#   bash deploy/k8s/blue-green.sh deploy <image>
#   bash deploy/k8s/blue-green.sh switch <blue|green>   send live traffic to that color
#   bash deploy/k8s/blue-green.sh rollback              switch back to the other color
#   bash deploy/k8s/blue-green.sh status
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

SERVICE=aceest-bluegreen
PORT=30082
PREVIEW_PORT=30086

live_color() { kc get service "$SERVICE" -o jsonpath='{.spec.selector.color}' 2> /dev/null || true; }

other_color() {
    if [ "$1" = blue ]; then echo green; else echo blue; fi
}

# apply_colors <blue image> <green image> <live color>
apply_colors() {
    apply blue-green.yaml BLUE_IMAGE="$1" GREEN_IMAGE="$2" \
        LIVE_COLOR="$3" IDLE_COLOR="$(other_color "$3")" > /dev/null
}

# wait until the live Service answers from the given color (kube-proxy needs a moment)
wait_for_color() {
    local color=$1 i served_by
    for i in $(seq 1 15); do
        served_by=$(header "$(url "$PORT")/health" X-Served-By)
        if [[ $served_by == aceest-$color-* ]]; then
            return 0
        fi
        sleep 1
    done
    return 1
}

deploy() {
    local image=$1 live idle blue green
    ensure_namespace
    live=$(live_color)
    idle=$(other_color "${live:-green}")       # the first deploy goes to blue
    blue=$(image_of aceest-blue)
    green=$(image_of aceest-green)
    if [ "$idle" = blue ]; then blue=$image; else green=$image; fi
    log "Blue-green: live color is ${live:-none}, deploying $image to $idle"

    # 1. new version on the idle color; live traffic is not touched
    apply_colors "${blue:-$image}" "${green:-$image}" "${live:-$idle}"
    if ! { wait_ready aceest-blue && wait_ready aceest-green && smoke_test "$PREVIEW_PORT"; }; then
        log "$idle FAILED its checks - live traffic was NOT switched"
        if [ -n "$live" ]; then
            undo aceest-"$idle" "$image" || true
        fi
        return 1
    fi

    # 2. switch all live traffic at once
    apply_colors "${blue:-$image}" "${green:-$image}" "$idle"
    if ! { wait_for_color "$idle" && smoke_test "$PORT"; }; then
        log "Live check FAILED after the switch"
        if [ -n "$live" ]; then
            apply_colors "${blue:-$image}" "${green:-$image}" "$live"
            log "Switched back to $live"
        fi
        return 1
    fi
    log "Live traffic on port $PORT now goes to $idle ($image)"
    if [ -n "$live" ]; then
        log "$live keeps the previous version - rollback: bash deploy/k8s/blue-green.sh rollback"
    fi
}

switch_to() {
    local color=$1 ready
    ready=$(kc get deployment aceest-"$color" -o jsonpath='{.status.readyReplicas}' 2> /dev/null || true)
    if [ "${ready:-0}" -lt 1 ]; then
        log "aceest-$color has no ready pods - not switching"
        return 1
    fi
    apply_colors "$(image_of aceest-blue)" "$(image_of aceest-green)" "$color"
    wait_for_color "$color"
    log "Live traffic on port $PORT now goes to $color ($(image_of aceest-"$color"))"
}

rollback() {
    local live
    live=$(live_color)
    if [ -z "$live" ]; then
        log "Nothing deployed yet"
        return 1
    fi
    switch_to "$(other_color "$live")"
}

status() {
    log "Live color: $(live_color) (port $PORT); idle color on the preview port $PREVIEW_PORT"
    kc get deployments -l strategy=blue-green -o wide
}

case "${1:-}" in
    deploy) deploy "${2:?usage: $0 deploy <image>}" ;;
    switch)
        case "${2:-}" in
            blue | green) switch_to "$2" ;;
            *)
                echo "usage: $0 switch <blue|green>" >&2
                exit 2
                ;;
        esac
        ;;
    rollback) rollback ;;
    status) status ;;
    *)
        echo "usage: $0 deploy <image> | switch <blue|green> | rollback | status" >&2
        exit 2
        ;;
esac
