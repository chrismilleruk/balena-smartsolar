FROM arm32v6/python:3-alpine

WORKDIR /usr/src/app

# Install all dependencies (build and runtime)
RUN apk add --no-cache \
    bluez \
    bluez-dev \
    dbus \
    dbus-dev \
    gcc \
    musl-dev \
    linux-headers

# Copy requirements first
COPY requirements.txt .

# Install Python packages with wheel caching
# First, try to install from cache, then build any missing wheels
RUN mkdir -p /wheel-cache && \
    pip install --no-cache-dir --find-links /wheel-cache -r requirements.txt || \
    (pip wheel --wheel-dir /wheel-cache -r requirements.txt && \
     pip install --no-cache-dir --find-links /wheel-cache -r requirements.txt)

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x start.sh debug_system.sh debug_bluetooth.py debug_victron_reader.py

# Run the application
CMD ["./start.sh"] 