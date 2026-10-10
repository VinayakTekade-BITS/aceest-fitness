#!/usr/bin/env bash
# Blue-green deployment: start the new version next to the live one, test it, then switch nginx.
# Usage: bash deploy/blue-green.sh deploy <image>
#        bash deploy/blue-green.sh switch <blue|green>     (manual switch / rollback)
set -euo pipefail

NETWORK=aceest-net
LB=aceest-lb
LB_PORT=8000
declare -A PORTS=([blue]=8001 [green]=8002)

active_color() {
    docker exec "$LB" cat /etc/nginx/conf.d/default.conf 2> /dev/null \
        | grep -o 'aceest-\(blue\|green\)' | head -1 | sed 's/aceest-//' || true
}

switch_to() {
    local color="$1" conf
    if [ "$(docker inspect -f '{{.State.Running}}' "aceest-$color" 2> /dev/null)" != true ]; then
        echo "aceest-$color is not running - cannot switch to it"
        exit 1
    fi
    conf=$(mktemp)
    cat > "$conf" <<NGINX
server {
    listen 80;

    location / {
        proxy_pass http://aceest-$color:5000;
        add_header X-Color $color always;
    }
}
NGINX
    docker cp "$conf" "$LB":/etc/nginx/conf.d/default.conf
    rm -f "$conf"
    docker exec "$LB" nginx -t -q
    docker exec "$LB" nginx -s reload
    echo "Live traffic on :$LB_PORT now goes to $color"
}

deploy() {
    local image="$1" live idle port i
    docker network inspect "$NETWORK" > /dev/null 2>&1 || docker network create "$NETWORK" > /dev/null
    # one-time migration from the earlier strategies (Steps 6 and 8)
    docker rm -f aceest-staging aceest-app-1 aceest-app-2 aceest-app-3 > /dev/null 2>&1 || true

    live=$(active_color)
    if [ "$live" = blue ]; then idle=green; else idle=blue; fi
    port=${PORTS[$idle]}
    echo "Live: ${live:-none} -> deploying $image to $idle (port $port)"

    docker rm -f "aceest-$idle" > /dev/null 2>&1 || true
    docker run -d --name "aceest-$idle" --network "$NETWORK" --restart unless-stopped \
        -p "$port":5000 -v aceest-data:/app/data "$image" > /dev/null

    for i in $(seq 1 15); do
        if curl -fs "http://localhost:$port/health" > /dev/null; then
            break
        fi
        if [ "$i" = 15 ]; then
            echo "$idle failed its smoke test - live traffic stays on ${live:-nothing}"
            docker logs "aceest-$idle" || true
            exit 1
        fi
        sleep 2
    done

    if ! docker container inspect "$LB" > /dev/null 2>&1; then
        docker run -d --name "$LB" --network "$NETWORK" --restart unless-stopped \
            -p "$LB_PORT":80 nginx:alpine > /dev/null
    fi
    switch_to "$idle"
    if [ -n "$live" ]; then
        echo "$live still runs the previous version - rollback: bash deploy/blue-green.sh switch $live"
    fi
}

case "${1:-}" in
    deploy)
        deploy "${2:?usage: deploy <image>}"
        ;;
    switch)
        case "${2:-}" in
            blue | green) switch_to "$2" ;;
            *) echo "usage: $0 switch <blue|green>"; exit 2 ;;
        esac
        ;;
    *)
        echo "usage: $0 deploy <image> | switch <blue|green>"
        exit 2
        ;;
esac
