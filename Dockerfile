FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend code
COPY GigNova/backend /app/backend

# Install Python dependencies
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for local storage
RUN mkdir -p /root/.gignova

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "gignova.app:app", "--host", "0.0.0.0", "--port", "8000"]
