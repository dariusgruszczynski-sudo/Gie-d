# Opcjonalny mikroserwis wykrywania akordów z audio (librosa + yt-dlp + ffmpeg).
# Cięższy obraz — budowany tylko, gdy włączysz nakładkę docker-compose.audio.yml.
FROM python:3.12-slim

# ffmpeg jest potrzebny librosie (dekodowanie audio) i yt-dlp.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY detect.py server.py ./

EXPOSE 8100
CMD ["python3", "server.py"]
