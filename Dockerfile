FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CARECONTEXT_DB=/app/.data/carecontext.sqlite3
COPY pyproject.toml README.md requirements.lock ./
COPY carecontext ./carecontext
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps . \
    && useradd --uid 10001 --create-home carecontext && mkdir /app/.data && chown carecontext /app/.data
USER carecontext
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["carecontext", "serve", "--host", "0.0.0.0", "--port", "8000"]
