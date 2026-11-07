# One image, two roles: the API (default) or the Streamlit UI (see docker-compose.yml).
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY api/ api/
COPY ui/ ui/
COPY models/cells.tflite models/cells.tflite
RUN useradd -m app && chown -R app /app
USER app
EXPOSE 8000 8501
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
