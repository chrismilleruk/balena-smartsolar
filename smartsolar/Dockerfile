FROM arm32v6/python:3-alpine

WORKDIR /usr/src/app

# Install system dependencies
RUN apk add --no-cache \
    bluez \
    bluez-dev \
    gcc \
    musl-dev \
    linux-headers

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python3", "main.py"] 