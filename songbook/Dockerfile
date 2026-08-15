# Śpiewnik — obraz backendu (czysty Node.js, zero zależności npm).
FROM node:20-slim
WORKDIR /app

COPY server ./server
COPY public ./public
RUN mkdir -p /app/data

ENV PORT=8080
ENV SONGBOOK_DATA_DIR=/app/data
# SONGBOOK_TOKEN ustawiany przez compose (z .env serwera) — pusty = dostęp otwarty.

# Stempel wersji (SHA + czas buildu) wstrzykiwany przez deploy.sh — pozwala
# sprawdzić z zewnątrz (GET /api/health), jaki kod realnie działa.
ARG GIT_SHA=dev
ARG BUILD_TIME=
ENV GIT_SHA=$GIT_SHA
ENV BUILD_TIME=$BUILD_TIME

EXPOSE 8080
CMD ["node", "server/server.js"]
