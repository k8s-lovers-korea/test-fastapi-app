FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
RUN pip install uv
RUN uv sync --frozen

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]