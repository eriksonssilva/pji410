FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY templates ./templates
COPY static ./static
COPY dataset ./dataset
ENV MSA_ROOT=/app MSA_DATASET=/app/dataset MSA_DB=/tmp/msa.sqlite
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "msa.app:app", "--host", "0.0.0.0", "--port", "8000"]
