# Name: Teo Wen Thing
# Matric No: 22004856
# Repository: https://github.com/wenthingteo/FYP_DesignSensei.git

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles

RUN python manage.py collectstatic --noinput || echo "Static files collection skipped"

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
