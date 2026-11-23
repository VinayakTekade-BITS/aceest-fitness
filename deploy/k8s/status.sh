#!/usr/bin/env bash
# One-page overview of every deployment strategy: URL, live color, images and readiness.
#   bash deploy/k8s/status.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

HOST_IP=${HOST_IP:-$(hostname -I 2> /dev/null | awk '{ print $1 }')}
HOST_IP=${HOST_IP:-localhost}

# row <strategy> <service> <node port> <notes>
row() {
    if kc get service "$2" > /dev/null 2>&1; then
        printf '%-22s %-28s %s\n' "$1" "http://$HOST_IP:$3" "$4"
    else
        printf '%-22s %-28s %s\n' "$1" "-" "not deployed yet"
    fi
}

echo "Stable release: $(stable_image)"
echo
printf '%-22s %-28s %s\n' STRATEGY URL NOTES
row "Rolling update" aceest-rolling 30081 "3 replicas, replaced one at a time"
row "Blue-green" aceest-bluegreen 30082 \
    "live color: $(kc get service aceest-bluegreen -o jsonpath='{.spec.selector.color}' 2> /dev/null || true)"
row "Blue-green (preview)" aceest-bluegreen-preview 30086 "the idle color"
row "Canary" aceest-canary 30083 "3 stable pods + 0-1 canary pod"
row "A/B testing" aceest-ab-router 30084 "header X-Variant: a|b, cookie ab_variant"
row "Shadow" aceest-shadow-router 30085 "answers from live, copies to shadow"
echo
kc get deployments -o custom-columns='DEPLOYMENT:.metadata.name,STRATEGY:.metadata.labels.strategy,READY:.status.readyReplicas,WANTED:.spec.replicas,IMAGE:.spec.template.spec.containers[0].image'
