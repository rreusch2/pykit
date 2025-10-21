FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the chatkit package
RUN pip install -e .

# Expose default port (Railway sets PORT env var at runtime)
EXPOSE 8080

# Use Python bootstrap that reads PORT env and starts Uvicorn
CMD ["python", "start.py"]
