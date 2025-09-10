FROM python:3.11-slim

# Ajustes básicos
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Instala dependencias primero (mejor caché)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY . .

# Expone el puerto (coincide con probes/HPA luego)
EXPOSE 8080

# Arranque con gunicorn (más robusto que flask dev server)
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app", "--workers", "2", "--threads", "4", "--timeout", "30"]