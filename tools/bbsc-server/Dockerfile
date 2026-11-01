# BBSC's game server (scripts/bbsc_gameserver, CLS_AMG, GPL-2.0-or-later; on fhody125's
# NoDreamForHunter, MIT): messages, bloodstains, the server list and BBSC's relay, for seamless
# co-op next to a shadNet server (tools/shadnet-server). Python 3, nothing else. See docs/SERVER.md.
#
#   docker build -t bbport-bbsc-server tools/bbsc-server
#   docker run -d --name bbsc-server --restart unless-stopped --network host -v bbsc-data:/data \
#       -e BBSC_HOST=100.x.y.z -e BBSC_SHADNET=100.x.y.z bbport-bbsc-server
FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Only scripts/bbsc_gameserver/ of this repository, at this branch or revision.
ARG BBPORT_REF=main
RUN git clone --depth 1 --filter=blob:none --sparse --branch "$BBPORT_REF" \
        https://github.com/ayozetr/bloodborne_linux.git /src \
    && git -C /src sparse-checkout set scripts/bbsc_gameserver \
    && mkdir -p /opt/bbsc && cp -r /src/scripts/bbsc_gameserver /opt/bbsc/gameserver \
    && rm -rf /src
COPY entrypoint.sh /opt/bbsc/
RUN chmod 755 /opt/bbsc/entrypoint.sh
ENV LANG=C.UTF-8 PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 20443/tcp 20444/tcp 18671/tcp 3478/udp
ENTRYPOINT ["/opt/bbsc/entrypoint.sh"]
