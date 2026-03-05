FROM python:3.11-slim

# Install system dependencies including Java 21 for Burp Suite
USER root
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    gnupg \
    software-properties-common \
    fontconfig \
    libfreetype6 \
    libfontconfig1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Java 21 (required for Burp Suite)
RUN apt-get update && \
    apt-get install -y wget && \
    wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /etc/apt/trusted.gpg.d/adoptium.gpg && \
    echo "deb https://packages.adoptium.net/artifactory/deb $(. /etc/os-release && echo $VERSION_CODENAME) main" > /etc/apt/sources.list.d/adoptium.list && \
    apt-get update && \
    apt-get install -y temurin-21-jre && \
    rm -rf /var/lib/apt/lists/*

# Create directory for Burp Suite
RUN mkdir -p /opt/burpsuite

# Download Burp Suite Professional JAR file (x64 Linux version)
# Using JAR file for easier headless/CLI usage
RUN curl -L "https://portswigger.net/burp/releases/startdownload?product=pro&version=2026.2.3&type=Jar" \
    -o /opt/burpsuite/burpsuite_pro.jar && \
    chmod 644 /opt/burpsuite/burpsuite_pro.jar

# Create Burp Suite configuration directory and license file
RUN mkdir -p /root/.BurpSuite

# Create prefs.xml with license key configuration
RUN cat > /root/.BurpSuite/prefs.xml << 'PREFS_EOF'
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
<properties>
<comment>Burp Suite Preferences</comment>
<entry key="free.suite.alertsdisplayaliases">true</entry>
<entry key="free.suite.alertsdisplayaliasesaliases">[]</entry>
<entry key="free.suite.feedbackReportingEnabled">false</entry>
<entry key="eulasAccepted">11</entry>
<entry key="license">Ab+OPxMAFmvP3SGvKbSCgajDRxJeu7vElzEMOubjpaGvYAn2zh0uJq9gCfbOHS4mzSXsTMNw40Hm0TSLUxjLJMEboSlAb3podB+Qkd39djfiIL5RXoHhylLLhtiJrZoWNGDZeOQtHFCeNjqSAWM56XKF6tBnBSTTlOYo0ACamctE6ZsAjB/N/mpKbxt77w7haWtTmFPYkVdCHprK3aaVREqxNA6EslkULcZoh4uWoN9qySk6DVRlqUGiRl0k+68mgSnTQC2noB6W2aR0eoM5GueTXP++QGZix/1KLW4IMzMAAKLJOlrhUNUDWMIxrmRruFLLXa4lxqte/hp/9XbYHOIkx+ZFtjTBrru5K8CqW8D4LpKmOxMvrHp9xBwDo/EshQ1JK4tEj7lly/ngMQUIzFzOTK3ljfP8qit5CenA1N+4WngcDl4xsRLWky3EjS3FEVumQbWbh4LyE4puC2eYWBA3+SEywTMRYrBVPz6FosNI8wWnp7TxiBgW2JniPPnS89y8iwsRTu2M+0m/vINgR2fZIjQ+4VqUxyaROjmgN5jCt52rNabEFlWd5IXnFS8n+neQpNUIvsNosNrh6ti665JbTnvFZEjmSLxbO3mJu5a6g9MNZE8AVts6Ch/g80dP7uLPx4vTze2Tbdsortvqp4z9NsZZ3lyNPzDkfefCLxvvWFsRg4qmJOc8JyiHz5qHl4h2fatUlBW/168Iznm4/4EfqDB/+FRYdR0qK3i4FjJ3ATb+milL2v4f2F2IVVQ2FabdV3mde8Z4HFKWxlw9iBBrTwlzY3f/aBaHsUXy7HM=</entry>
</properties>
PREFS_EOF

# Create a script to run Burp Suite in headless mode
RUN cat > /opt/burpsuite/run_burp.sh << 'SCRIPT_EOF'
#!/bin/bash
# Run Burp Suite Professional in headless mode
# Usage: /opt/burpsuite/run_burp.sh [additional_args...]

BURP_JAR="/opt/burpsuite/burpsuite_pro.jar"
JAVA_OPTS="-Xmx2g -Djava.awt.headless=true"

java $JAVA_OPTS -jar "$BURP_JAR" "$@"
SCRIPT_EOF
RUN chmod +x /opt/burpsuite/run_burp.sh

# Set up environment for Burp Suite
ENV BURP_HOME=/opt/burpsuite
ENV BURP_JAR=/opt/burpsuite/burpsuite_pro.jar
ENV PATH="${BURP_HOME}:${PATH}"
ENV JAVA_HOME=/usr/lib/jvm/temurin-21-jre-amd64

# Set Burp license key as environment variable
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
