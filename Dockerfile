FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7070

CMD ["gunicorn", "--preload", "--bind", "0.0.0.0:7070", "--workers", "4", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:app"]