#!/bin/sh
# BBSC's game server: listens on BBSC_HOST (the server's Tailscale address keeps it off the other
# networks, with --network host) and talks to the shadNet server at BBSC_SHADNET (the same
# address when both run on this computer). Messages, bloodstains and logs live in /data.
set -eu
: "${BBSC_HOST:?set BBSC_HOST to the address the players reach this server at}"
shadnet=${BBSC_SHADNET:-$BBSC_HOST}
if [ "$BBSC_HOST" != 0.0.0.0 ]; then
    until grep -qF " $BBSC_HOST" /proc/net/fib_trie; do
        echo "Waiting for $BBSC_HOST (Tailscale up?)"
        sleep 5
    done
fi
set -- --shadnet "$shadnet" --host "$BBSC_HOST" --data /data/online-data.json \
    --log-dir /data/logs --no-playlog "$@"
# BBSC_BBHOST=0: without its bbhost-compatible service (TCP 18671, UDP 3478 STUN and relay). The
# relay on UDP 3478 is the one BBSC's online module falls back to: keep it for BBSC players.
[ "${BBSC_BBHOST:-1}" = 0 ] && set -- "$@" --no-bbhost
exec python3 /opt/bbsc/gameserver/bbsc_gameserver.py "$@"
