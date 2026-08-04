# --- Stage 1: build the React dashboard ---
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: backend + built dashboard ---
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /backend/static ./static

RUN mkdir -p /app/data

# Stempel wersji: SHA commita + czas buildu wstrzykiwane przez deploy.sh
# (--build-arg), żeby apka mogła pokazać, JAKI kod realnie działa. Domyślne
# "dev" gdy budowane ręcznie bez argów.
ARG GIT_SHA=dev
ARG BUILD_TIME=
ENV GIT_SHA=$GIT_SHA
ENV BUILD_TIME=$BUILD_TIME

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
