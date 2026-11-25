FROM python:3.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CARECONTEXT_DB=/app/.data/carecontext.sqlite3
COPY pyproject.toml README.md ./
COPY carecontext ./carecontext
RUN python -m pip install --no-cache-dir . \
    && useradd --uid 10001 --create-home carecontext && mkdir /app/.data && chown carecontext /app/.data
USER carecontext
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["carecontext", "serve", "--host", "0.0.0.0", "--port", "8000"]
