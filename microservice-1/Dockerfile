FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py ./

EXPOSE 8080
# Gunicorn: 2 workers, 2 threads; ajusta segun CPU
CMD ["gunicorn", "-w", "2", "--threads", "2", "-b", "0.0.0.0:8080", "wsgi:app"]