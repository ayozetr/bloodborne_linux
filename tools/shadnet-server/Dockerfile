# A private shadNet server for Bloodborne co-op: Wozzardman/shadnet-p2p (GPL-2.0-or-later), the
# shadNet server with its UDP port (STUN) and the Bloodborne summon broker. Debian 13 for Qt 6.8:
# shadnet-p2p does not build with older Qt (Ubuntu 24.04 has 6.4). See docs/SERVER.md.
#
#   docker build -t bbport-shadnet tools/shadnet-server
#   docker run -d --name shadnet --restart unless-stopped -v shadnet-data:/data \
#       -e SHADNET_REGISTRATION_KEY=<your signup code> \
#       -p <address>:31313:31313/tcp -p <address>:31314:31314/udp -p <address>:31315:31315/tcp \
#       bbport-shadnet
FROM debian:trixie AS build
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git cmake \
        ninja-build build-essential qt6-base-dev qt6-httpserver-dev qt6-websockets-dev \
    && rm -rf /var/lib/apt/lists/*
# The revision these instructions were tested with.
ARG SHADNET_REF=5a849a192fd4450593c57b10697316ac324c856e
RUN git clone https://github.com/Wozzardman/shadnet-p2p.git /src && cd /src \
    && git checkout "$SHADNET_REF" && git submodule update --init --recursive
WORKDIR /src
RUN cmake -G Ninja -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build \
    && cmake -G Ninja -S clientsample -B clientsample/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build clientsample/build
RUN mkdir -p /opt/shadnet && cp build/shadnet build/worlds.cfg build/scoreboards.cfg \
        clientsample/build/shadnet-sample /opt/shadnet/

FROM debian:trixie
RUN apt-get update && apt-get install -y --no-install-recommends libqt6core6t64 libqt6network6 \
        libqt6sql6 libqt6sql6-sqlite libqt6concurrent6 libqt6httpserver6 libqt6websockets6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/shadnet /opt/shadnet
COPY entrypoint.sh /opt/shadnet/
RUN chmod 755 /opt/shadnet/entrypoint.sh
ENV LANG=C.UTF-8 PATH=/opt/shadnet:$PATH
VOLUME /data
EXPOSE 31313/tcp 31314/udp 31315/tcp
ENTRYPOINT ["/opt/shadnet/entrypoint.sh"]
