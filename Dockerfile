FROM python:3.11-slim

# Install system dependencies including Java for Burp Suite
USER root
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    openjdk-17-jre-headless \
    fontconfig \
    libfreetype6 \
    libfontconfig1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create directory for Burp Suite
RUN mkdir -p /opt/burpsuite

# Download and install Burp Suite Professional (x64 Linux version)
# Using the official PortSwigger download URL
RUN curl -L "https://portswigger.net/burp/releases/startdownload?product=pro&version=2026.2.3&type=linux" \
    -o /tmp/burpsuite_pro.sh && \
    chmod +x /tmp/burpsuite_pro.sh && \
    /tmp/burpsuite_pro.sh -q -dir /opt/burpsuite && \
    rm /tmp/burpsuite_pro.sh

# Create Burp Suite license file
# The license key is provided as an environment variable for security
# But we also create a default config with the provided key
RUN mkdir -p /root/.BurpSuite
COPY <<EOF /root/.BurpSuite/license.key
Ab+OPxMAFmvP3SGvKbSCgajDRxJeu7vElzEMOubjpaGvYAn2zh0uJq9gCfbOHS4mzSXsTMNw40Hm0TSLUxjLJMEboSlAb3podB+Qkd39djfiIL5RXoHhylLLhtiJrZoWNGDZeOQtHFCeNjqSAWM56XKF6tBnBSTTlOYo0ACamctE6ZsAjB/N/mpKbxt77w7haWtTmFPYkVdCHprK3aaVREqxNA6EslkULcZoh4uWoN9qySk6DVRlqUGiRl0k+68mgSnTQC2noB6W2aR0eoM5GueTXP++QGZix/1KLW4IMzMAAKLJOlrhUNUDWMIxrmRruFLLXa4lxqte/hp/9XbYHOIkx+ZFtjTBrru5K8CqW8D4LpKmOxMvrHp9xBwDo/EshQ1JK4tEj7lly/ngMQUIzFzOTK3ljfP8qit5CenA1N+4WngcDl4xsRLWky3EjS3FEVumQbWbh4LyE4puC2eYWBA3+SEywTMRYrBVPz6FosNI8wWnp7TxiBgW2JniPPnS89y8iwsRTu2M+0m/vINgR2fZIjQ+4VqUwyaROjmgN5jCt52rNabEFlWd5IXnFS8n+neQpNUIvsNosNrh6ti665JbTnvFZEjmSLxbO3mJu5a6g9MNZE8AVts6Ch/g80dP7uLPx4vTze2Tbdsortvqp4z9NsZZ3lyNPzDkfefCLxvvWFsRg4qmJOc8JyiHz5qHl4h2fatUlBW/168Iznm4/4EfqDB/+FRYdR0qK3i4FjJ3ATb+milL2v4f2F2IVVQ2FabdV3mde8Z4HFKWxlw9iBBrTwlzY3f/aBaHsUXy7HM=
EOF

# Set up environment for Burp Suite
ENV BURP_HOME=/opt/burpsuite
ENV PATH="${BURP_HOME}:${PATH}"
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Set Burp license key as environment variable (alternative method)
ENV BURP_LICENSE_KEY="Ab+OPxMAFmvP3SGvKbSCgajDRxJeu7vElzEMOubjpaGvYAn2zh0uJq9gCfbOHS4mzSXsTMNw40Hm0TSLUxjLJMEboSlAb3podB+Qkd39djfiIL5RXoHhylLLhtiJrZoWNGDZeOQtHFCeNjqSAWM56XKF6tBnBSTTlOYo0ACamctE6ZsAjB/N/mpKbxt77w7haWtTmFPYkVdCHprK3aaVREqxNA6EslkULcZoh4uWoN9qySk6DVRlqUGiRl0k+68mgSnTQC2noB6W2aR0eoM5GueTXP++QGZix/1KLW4IMzMAAKLJOlrhUNUDWMIxrmRruFLLXa4lxqte/hp/9XbYHOIkx+ZFtjTBrru5K8CqW8D4LpKmOxMvrHp9xBwDo/EshQ1JK4tEj7lly/ngMQUIzFzOTK3ljfP8qit5CenA1N+4WngcDl4xsRLWky3EjS3FEVumQbWbh4LyE4puC2eYWBA3+SEywTMRYrBVPz6FosNI8wWnp7TxiBgW2JniPPnS89y8iwsRTu2M+0m/vINgR2fZIjQ+4VqUwyaROjmgN5jCt52rNabEFlWd5IXnFS8n+neQpNUIvsNosNrh6ti665JbTnvFZEjmSLxbO3mJu5a6g9MNZE8AVts6Ch/g80dP7uLPx4vTze2Tbdsortvqp4z9NsZZ3lyNPzDkfefCLxvvWFsRg4qmJOc8JyiHz5qHl4h2fatUlBW/168Iznm4/4EfqDB/+FRYdR0qK3i4FjJ3ATb+milL2v4f2F2IVVQ2FabdV3mde8Z4HFKWxlw9iBBrTwlzY3f/aBaHsUXy7HM="

WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Render sets PORT automatically
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8000

# Run the MCP server
CMD ["python", "server.py"]
