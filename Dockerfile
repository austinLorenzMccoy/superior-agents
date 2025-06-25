FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend code
COPY GigNova/backend /app/backend

# Create a modified requirements file without problematic dependencies
WORKDIR /app/backend
RUN grep -v -E "py-solc-x==1.12.0|autogen-agentchat==0.2.0" requirements.txt > requirements_modified.txt && \
    echo "py-solc-x==1.0.1" >> requirements_modified.txt && \
    echo "autogen-agentchat==0.4.2" >> requirements_modified.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_modified.txt

# Create directory for local storage
RUN mkdir -p /root/.gignova

# Set environment variables
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "gignova.app:app", "--host", "0.0.0.0", "--port", "8000"]
