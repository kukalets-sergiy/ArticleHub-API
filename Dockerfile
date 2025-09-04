FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code
RUN apt-get update && apt-get install -y build-essential ca-certificates
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "articlehub_core.wsgi:application", "--bind", "0.0.0.0:8000"]
