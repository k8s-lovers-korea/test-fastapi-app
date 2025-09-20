FROM python:3.11-slim

WORKDIR /app

# Install uv first
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies system-wide in container
RUN uv pip install --system .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]