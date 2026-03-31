FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      fastapi==0.115.0 \
      pydantic==2.8.2 \
      sqlalchemy==2.0.35 \
      uvicorn==0.30.6 \
      pyjwt==2.9.0 \
      google-auth==2.35.0 \
      httpx==0.27.2

COPY app /app/app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
