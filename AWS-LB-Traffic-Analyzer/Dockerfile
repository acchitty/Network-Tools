FROM python:3.11-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpcap-dev \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir boto3

# Create app directory
WORKDIR /app

# Copy analyzer script
COPY aws-lb-traffic-analyzer.py /app/

# Create logs directory
RUN mkdir -p /logs

# Run as root (required for packet capture)
USER root

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Entry point
ENTRYPOINT ["python3", "/app/aws-lb-traffic-analyzer.py"]
CMD ["-i", "eth0", "-s", "10", "--enable-cloudwatch"]
