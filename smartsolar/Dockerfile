FROM --platform=linux/arm/v6 python:3.9-slim-bullseye

WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bluetooth \
    bluez \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python3", "main.py"] 