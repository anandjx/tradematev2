# Dockerfile (Refactored based on Locus reference)
FROM python:3.11-slim

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the port
EXPOSE 8080

# Command to run the application
# Using uvicorn directly as in Locus reference
CMD ["uvicorn", "app.frontend.backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
