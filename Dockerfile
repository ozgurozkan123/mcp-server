FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

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
