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

# Copy configuration
COPY telegraf.conf /etc/telegraf/telegraf.conf

# Use telegraf user
USER telegraf

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD telegraf --test || exit 1

ENTRYPOINT ["/usr/bin/telegraf"] 