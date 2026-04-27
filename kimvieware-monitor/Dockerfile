FROM python:3.12-slim

WORKDIR /app

# Copier depuis le contexte (IMPORTANT: chemins relatifs au context docker-compose)
COPY ../kimvieware-shared /app/kimvieware-shared
COPY ../kimvieware-monitor /app/kimvieware-monitor

# Installer shared
WORKDIR /app/kimvieware-shared
RUN pip install -e .

# Installer monitor deps
WORKDIR /app/kimvieware-monitor
COPY ../kimvieware-monitor/requirements.txt .
RUN pip install -r requirements.txt

COPY ../kimvieware-monitor .

CMD ["python", "monitor_service.py"]
