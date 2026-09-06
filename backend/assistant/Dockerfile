FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./assistant

RUN chown -R nobody:nogroup /app
USER nobody

FROM base AS test

USER root
RUN pip install --no-cache-dir -r requirements-dev.txt
USER nobody

FROM base AS runtime

EXPOSE 8010

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/health')"

CMD ["uvicorn", "assistant.app:app", "--host", "0.0.0.0", "--port", "8010"]
