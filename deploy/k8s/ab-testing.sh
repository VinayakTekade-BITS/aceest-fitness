#!/usr/bin/env bash
# A/B testing: variant A = the previous stable release (control), variant B = the new
# release. The nginx router splits new users 50/50 and keeps each user on one variant.
#   bash deploy/k8s/ab-testing.sh deploy <image>   B gets <image>; A gets the stable release
#   bash deploy/k8s/ab-testing.sh rollback         B goes back to its previous image
#   bash deploy/k8s/ab-testing.sh status
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

A=aceest-ab-a
B=aceest-ab-b
ROUTER=aceest-ab-router
PORT=30084

# apply_variants <image A> <image B>
apply_variants() {
    local out
    out=$(apply ab-testing.yaml A_IMAGE="$1" B_IMAGE="$2")
    if grep -q "configmap/$ROUTER configured" <<< "$out"; then
        kc rollout restart deployment/"$ROUTER" > /dev/null   # nginx reads its config at start
    fi
}

check() {
    local base variant got a=0 b=0 i jar first
    base=$(url "$PORT")
    for variant in a b; do
        smoke_test "$PORT" -H "X-Variant: $variant" || return 1   # each variant on its own
        got=$(header "$base/version" X-Variant -H "X-Variant: $variant")
        log "X-Variant: $variant -> variant '$got', version $(header "$base/version" X-App-Version -H "X-Variant: $variant")"
        if [ "$got" != "$variant" ]; then
            return 1
        fi
    done
    for i in $(seq 1 30); do
        case "$(header "$base/health" X-Variant)" in
            a) a=$((a + 1)) ;;
            b) b=$((b + 1)) ;;
        esac
    done
    log "30 new users were split: A $a, B $b"
    if [ "$a" -eq 0 ] || [ "$b" -eq 0 ]; then
        return 1
    fi
    jar=$(mktemp)
    first=$(header "$base/health" X-Variant -c "$jar" -b "$jar")
    for i in 1 2 3 4 5; do
        if [ "$(header "$base/health" X-Variant -c "$jar" -b "$jar")" != "$first" ]; then
            rm -f "$jar"
            log "A returning user changed variant - the cookie does not work"
            return 1
        fi
    done
    rm -f "$jar"
    log "A returning user stays on variant $first (cookie ab_variant=$first)"
}

deploy() {
    local image=$1 control
    ensure_namespace
    control=$(stable_image)
    control=${control:-$(image_of "$A")}
    control=${control:-$image}
    log "A/B test: variant A (control) = $control, variant B = $image"
    apply_variants "$control" "$image"
    if ! { wait_ready "$A" && wait_ready "$B" && wait_ready "$ROUTER" && check; }; then
        log "A/B deployment FAILED - variant B goes back to its previous image"
        undo "$B" "$image" || true
        return 1
    fi
    log "A/B test running on port $PORT"
}

rollback() {
    kc rollout undo deployment/"$B" > /dev/null
    wait_ready "$B"
    log "Variant B runs $(image_of "$B") again"
}

status() {
    kc get deployments -l strategy=ab-testing -o wide
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
