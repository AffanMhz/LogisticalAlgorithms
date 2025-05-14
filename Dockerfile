# Start from Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists, install Python3, pip, Node.js, npm, and clean up unnecessary files
RUN apt-get update && \
    apt-get install -y python3 python3-pip curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory for backend
WORKDIR /app

# Copy requirements.txt file for backend
COPY requirements.txt .

# Install numpy separately with a higher timeout
RUN pip3 install --no-cache-dir --timeout=300 numpy==1.25.2

# Install Python dependencies (including numpy)
RUN pip3 install --no-cache-dir --timeout=100 -r requirements.txt

# Copy backend code
COPY . .

# Build the frontend
WORKDIR /app/frontend
RUN if [ -f package.json ]; then npm install --no-cache --legacy-peer-deps && npm run build || true; fi

# Move frontend build (if any) to a static directory for FastAPI
WORKDIR /app
RUN if [ -d frontend/build ]; then \
      mkdir -p /app/static && \
      cp -r frontend/build/* /app/static/; \
    fi

# Create necessary data directories
RUN mkdir -p /app/data

# Expose port 8000 to the outside world
EXPOSE 8000

# Command to run the FastAPI V2 backend (assuming fastapi_app_V2.py is the entrypoint)
CMD ["uvicorn", "fastapi_app_V2:app", "--host", "0.0.0.0", "--port", "8000"]
