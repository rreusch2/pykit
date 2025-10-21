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

# Expose port (Railway will assign this dynamically)
EXPOSE $PORT

# Run startup check then start the application
CMD python startup_check.py && uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
