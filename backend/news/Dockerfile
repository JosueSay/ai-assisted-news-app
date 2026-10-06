FROM python:3.13-slim AS tools

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app/backend

COPY backend/news/requirements*.txt /tmp/news-requirements/
RUN pip install --no-cache-dir -r /tmp/news-requirements/requirements-dev.txt

COPY backend /app/backend

RUN chown -R nobody:nogroup /app
USER nobody

EXPOSE 8020

CMD ["python", "-m", "uvicorn", "news.api:app", "--host", "0.0.0.0", "--port", "8020"]
