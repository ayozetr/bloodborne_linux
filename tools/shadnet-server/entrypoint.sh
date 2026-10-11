#!/bin/sh
# shadNet keeps its files beside its executable (shadnet.cfg, db/, score_data/): it runs from the
# data volume, its executable copied there on every start (an updated image updates it), and the
# configuration and accounts stay.
set -eu
cd /data
cp /opt/shadnet/shadnet .
for file in worlds.cfg scoreboards.cfg; do
    [ -e "$file" ] || cp "/opt/shadnet/$file" .
done
if [ ! -e shadnet.cfg ]; then
    # The first start writes the default configuration; then what co-op needs (docs/SERVER.md).
    timeout 5 ./shadnet >/dev/null 2>&1 || true
    sed -i -e 's/^Host=.*/Host=0.0.0.0/' -e 's/^Matching2Enabled=.*/Matching2Enabled=true/' \
        -e 's/^StatsEnabled=.*/StatsEnabled=false/' shadnet.cfg
    echo "shadnet.cfg created in the data volume"
fi
# The address to listen on: the server's Tailscale address keeps it off the other networks
# (with --network host). shadNet keeps running without its listeners when the address is missing,
# as at boot before Tailscale is up: it starts once the address is there.
if [ -n "${SHADNET_HOST:-}" ]; then
    sed -i "s|^Host=.*|Host=${SHADNET_HOST}|" shadnet.cfg
    if [ "$SHADNET_HOST" != 0.0.0.0 ]; then
        until grep -qF " $SHADNET_HOST" /proc/net/fib_trie; do
            echo "Waiting for $SHADNET_HOST (Tailscale up?)"
            sleep 5
        done
    fi
fi
# The signup code for new accounts (shadnet-sample ... register): kept in shadnet.cfg.
if [ -n "${SHADNET_REGISTRATION_KEY:-}" ]; then
    sed -i "s|^RegistrationSecretKey=.*|RegistrationSecretKey=${SHADNET_REGISTRATION_KEY}|" shadnet.cfg
fi
if ! grep -q '^RegistrationSecretKey=..*' shadnet.cfg; then
    echo 'Warning: no SHADNET_REGISTRATION_KEY: anyone who reaches the server can create accounts' >&2
fi
exec ./shadnet "$@"
