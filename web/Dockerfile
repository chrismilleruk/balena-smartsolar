FROM arm32v6/python:3-alpine

WORKDIR /app

# Install ca-certificates for HTTPS support
RUN apk add --no-cache ca-certificates

# Install required packages (all pure Python, no C extensions needed)
RUN pip install --no-cache-dir flask segno requests

# Copy application files
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"] 