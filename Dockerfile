# Start from Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists, install Python3, pip, and clean up unnecessary files
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create necessary data directories
RUN mkdir -p data

# Expose port 8000 to the outside world
EXPOSE 8000

# Command to run the Flask application on port 8000
CMD ["python3", "start_for_docker.py"]
