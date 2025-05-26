#!/bin/bash
# Test Telegraf configuration locally

echo "Testing Telegraf configuration..."

# Detect OS
OS=$(uname -s)
ARCH=$(uname -m)

# Download Telegraf binary if not present
if [ ! -f "./telegraf" ]; then
    echo "Downloading Telegraf binary..."
    
    if [ "$OS" = "Darwin" ]; then
        # macOS
        if [ "$ARCH" = "arm64" ]; then
            URL="https://dl.influxdata.com/telegraf/releases/telegraf-1.31.0_darwin_arm64.tar.gz"
        else
            URL="https://dl.influxdata.com/telegraf/releases/telegraf-1.31.0_darwin_amd64.tar.gz"
        fi
    else
        # Linux
        URL="https://dl.influxdata.com/telegraf/releases/telegraf-1.31.0_linux_amd64.tar.gz"
    fi
    
    curl -sL "$URL" -o telegraf.tar.gz
    tar xf telegraf.tar.gz
    cp telegraf*/usr/bin/telegraf ./telegraf
    rm -rf telegraf-1.31.0* telegraf.tar.gz
    chmod +x ./telegraf
fi

# Test the configuration
echo "Validating configuration..."
./telegraf --config ../telegraf.conf --test

# Show available input/output plugins
echo -e "\nAvailable input plugins:"
./telegraf --input-list | grep -E "(tail|file)"

echo -e "\nAvailable processor plugins:"
./telegraf --processor-list | grep -E "(json|parser)"

echo -e "\nAvailable output plugins:"
./telegraf --output-list | grep influx 