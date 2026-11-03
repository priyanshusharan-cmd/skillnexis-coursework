# ---- build stage: install dependencies into a virtualenv
FROM python:3.12-slim AS build
WORKDIR /app
RUN python -m venv /venv
COPY requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- runtime stage: small image, non-root user
FROM python:3.12-slim
ENV PATH="/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BLOG_DB=/data/blog.db PORT=8000
RUN useradd --create-home --uid 10001 app && mkdir /data && chown app /data
COPY --from=build /venv /venv
WORKDIR /app
COPY blogly ./blogly
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=2)"
CMD ["sh", "-c", "uvicorn blogly.app:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
