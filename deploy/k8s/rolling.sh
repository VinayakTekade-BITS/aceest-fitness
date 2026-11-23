#!/usr/bin/env bash
# Rolling update: replace the 3 pods of aceest-rolling one at a time.
#   bash deploy/k8s/rolling.sh deploy <image>   roll out; roll back automatically if it fails
#   bash deploy/k8s/rolling.sh rollback         go back to the previous revision
#   bash deploy/k8s/rolling.sh status
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

DEPLOYMENT=aceest-rolling
PORT=30081

deploy() {
    local image=$1
    ensure_namespace
    log "Rolling update of $DEPLOYMENT to $image, one pod at a time"
    apply rolling.yaml IMAGE="$image" CHANGE_CAUSE="deploy $image"
    if wait_ready "$DEPLOYMENT" && smoke_test "$PORT"; then
        log "Rolling update complete: $image is live on port $PORT"
        return 0
    fi
    log "Rolling update FAILED - rolling back to the previous revision"
    undo "$DEPLOYMENT" "$image" || log "No previous revision to roll back to"
    return 1
}

rollback() {
    kc rollout undo deployment/"$DEPLOYMENT" > /dev/null
    wait_ready "$DEPLOYMENT"
    log "Rolled back: $DEPLOYMENT runs $(image_of "$DEPLOYMENT")"
}

status() {
    kc get deployment "$DEPLOYMENT" -o wide
    kc rollout history deployment/"$DEPLOYMENT"
}

case "${1:-}" in
    deploy) deploy "${2:?usage: $0 deploy <image>}" ;;
    rollback) rollback ;;
    status) status ;;
    *)
        echo "usage: $0 deploy <image> | rollback | status" >&2
        exit 2
        ;;
esac
