FROM python:3.11-slim

WORKDIR /app

# Install uv first
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .

# Install dependencies system-wide in container
RUN uv export --format requirements-txt --no-hashes --no-editable > requirements.txt && \
    uv pip install --system -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]