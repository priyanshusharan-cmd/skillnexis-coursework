# Build from deep-learning/week-4:  docker build -f api/Dockerfile -t cifar-api .   then  docker run -p 8000:8000 cifar-api
FROM python:3.12-slim
WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ api/
COPY models/cifar_int8_full.tflite models/
RUN useradd -m app && chown -R app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
