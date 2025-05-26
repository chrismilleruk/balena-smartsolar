# Use ARM v6 compatible base image
FROM arm32v6/alpine:3.18

# Install runtime dependencies
RUN apk add --no-cache ca-certificates wget

# Download Telegraf ARM binary (armel = ARM v6)
# Check https://portal.influxdata.com/downloads/ for latest version
RUN wget -q https://dl.influxdata.com/telegraf/releases/telegraf-1.31.0_linux_armel.tar.gz && \
    tar xf telegraf-1.31.0_linux_armel.tar.gz && \
    cp telegraf-1.31.0/usr/bin/telegraf /usr/bin/telegraf && \
    rm -rf telegraf-1.31.0* && \
    chmod +x /usr/bin/telegraf

# Create telegraf user
RUN addgroup -S telegraf && adduser -S telegraf -G telegraf

# Create directories for persistent state
RUN mkdir -p /var/lib/telegraf/buffer \
    && mkdir -p /var/lib/telegraf/tail_state \
    && mkdir -p /var/lib/telegraf/file_state \
    && chown -R telegraf:telegraf /var/lib/telegraf

# Copy configuration and start script
COPY telegraf.conf /etc/telegraf/telegraf.conf
COPY start-telegraf.sh /usr/local/bin/start-telegraf.sh
RUN chmod +x /usr/local/bin/start-telegraf.sh

# Use telegraf user
USER telegraf

ENTRYPOINT ["/usr/local/bin/start-telegraf.sh"] 