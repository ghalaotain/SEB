FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

ARG INSTALL_AI=false

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ai.txt ./

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && if [ "$INSTALL_AI" = "true" ]; then \
        pip install -r requirements-ai.txt; \
    fi

COPY . .

RUN mkdir -p \
    /app/instance \
    /app/app/static/uploads/advertisements

EXPOSE 8000

CMD ["sh", "-c", "flask --app wsgi.py db upgrade && flask --app wsgi.py bootstrap-deployment && gunicorn --workers 1 --threads 4 --timeout 180 --bind 0.0.0.0:${PORT} wsgi:app"]
