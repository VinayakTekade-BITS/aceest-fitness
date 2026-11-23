#!/usr/bin/env bash
# The "stable release" is the image of the last build that passed every deploy stage.
# It is kept in the aceest-release ConfigMap; A/B testing (variant A) and shadow (live track)
# use it as their control version, and it is the version to go back to after a failure.
#   bash deploy/k8s/release.sh mark-stable <image>
#   bash deploy/k8s/release.sh show
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

case "${1:-}" in
    mark-stable)
        image=${2:?usage: $0 mark-stable <image>}
        ensure_namespace
        kc create configmap aceest-release \
            --from-literal=image="$image" \
            --from-literal=build="${BUILD_NUMBER:-manual}" \
            --from-literal=marked_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --dry-run=client -o yaml | kubectl apply -f - > /dev/null
        log "Stable release is now $image"
        ;;
    show)
        echo "Stable release: $(stable_image)"
        ;;
    *)
        echo "usage: $0 mark-stable <image> | show" >&2
        exit 2
        ;;
esac
