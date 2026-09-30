# Minimal sandbox image: python interpreter + the generic runner. Nothing else.
FROM python:3.10-slim
RUN useradd -r -u 65534 -o sandbox 2>/dev/null || true
WORKDIR /sandbox
COPY runner.py /sandbox/runner.py
USER 65534:65534
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "/sandbox/runner.py"]
