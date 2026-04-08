FROM python:3.12-slim

WORKDIR /app

# shared lib
COPY kimvieware-shared /app/kimvieware-shared
WORKDIR /app/kimvieware-shared
RUN pip install -e .

# monitor service
WORKDIR /app/kimvieware-monitor
COPY kimvieware-monitor/requirements.txt .
RUN pip install -r requirements.txt

COPY kimvieware-monitor/ .

CMD ["python", "monitor_service.py"]