FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY pyproject.lock . # If you use a lock file; remove if not present
RUN pip install uv
RUN uv pip install --system

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]