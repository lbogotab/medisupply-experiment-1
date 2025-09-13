FROM python:3.11-slim

WORKDIR /app

COPY main.py .
COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "main.py"]
