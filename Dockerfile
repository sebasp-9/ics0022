FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/app

WORKDIR /app

COPY pyproject.toml .
COPY pwvault/ pwvault/
RUN pip install --no-cache-dir .

RUN useradd --create-home --user-group --uid 10001 app \
    && mkdir -p /home/app/.pwvault \
    && chown app:app /home/app/.pwvault \
    && chmod 700 /home/app/.pwvault

USER app
ENTRYPOINT ["pwvault"]
