#!/usr/bin/env bash
# Rolling update: replace the app replicas behind nginx one at a time.
# Usage: bash deploy/rolling.sh <image>
set -euo pipefail

IMAGE="$1"
REPLICAS=(aceest-app-1 aceest-app-2 aceest-app-3)
NETWORK=aceest-net
LB=aceest-lb
LB_PORT=8000
STABLE=aceest-fitness:stable

# Point nginx at every replica except the ones passed as arguments, then reload it
update_lb() {
    local servers="" conf r
    for r in "${REPLICAS[@]}"; do
        if [[ " $* " != *" $r "* ]]; then
            servers+="    server $r:5000;"$'\n'
        fi
    done
    conf=$(mktemp)
    cat > "$conf" <<NGINX
upstream aceest {
$servers}

server {
    listen 80;

    location / {
        proxy_pass http://aceest;
        proxy_connect_timeout 2s;
        proxy_next_upstream error timeout http_502;
        add_header X-Upstream \$upstream_addr always;
    }
}
NGINX
    docker cp "$conf" "$LB":/etc/nginx/conf.d/default.conf
    rm -f "$conf"
    docker exec "$LB" nginx -t -q
    docker exec "$LB" nginx -s reload
    sleep 1    # let the old nginx workers finish their requests
}

start_replica() {
    docker rm -f "$1" > /dev/null 2>&1 || true
    docker run -d --name "$1" --network "$NETWORK" --restart unless-stopped \
        -v aceest-data:/app/data "$2" > /dev/null
}

wait_healthy() {
    local i
    for i in $(seq 1 15); do
        if docker exec "$1" python -c \
            "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" \
            > /dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    return 1
}

docker network inspect "$NETWORK" > /dev/null 2>&1 || docker network create "$NETWORK" > /dev/null
docker rm -f aceest-staging > /dev/null 2>&1 || true     # one-time migration from Recreate (Step 6)

if ! docker container inspect "$LB" > /dev/null 2>&1; then
    echo "First rollout: starting ${#REPLICAS[@]} replicas and the load balancer"
    for r in "${REPLICAS[@]}"; do
        start_replica "$r" "$IMAGE"
    done
    for r in "${REPLICAS[@]}"; do
        wait_healthy "$r" || { docker logs "$r"; exit 1; }
    done
    docker run -d --name "$LB" --network "$NETWORK" --restart unless-stopped \
        -p "$LB_PORT":80 nginx:alpine > /dev/null
    update_lb
    exit 0
fi

for r in "${REPLICAS[@]}"; do
    echo "Updating $r"
    update_lb "$r"                     # drain: stop sending traffic to this replica
    start_replica "$r" "$IMAGE"
    if ! wait_healthy "$r"; then
        echo "$r failed its health check - stopping the rollout"
        docker logs "$r" || true
        if docker image inspect "$STABLE" > /dev/null 2>&1; then
            start_replica "$r" "$STABLE"
            wait_healthy "$r" && update_lb || update_lb "$r"
        else
            update_lb "$r"             # keep the broken replica out of rotation
        fi
        exit 1
    fi
    update_lb                          # back into rotation
done
echo "Rolling update complete: all replicas run $IMAGE"
