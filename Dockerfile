FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks and gcc for building psutil
RUN apt-get update && apt-get install -y curl gcc python3-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Build arguments for version information
ARG BUILD_NUMBER="dev"
ARG VERSION="1.0.0"
ARG BUILD_DATE=""

# Set environment variables for version info
ENV BUILD_NUMBER=${BUILD_NUMBER}
ENV VERSION=${VERSION}
ENV BUILD_DATE=${BUILD_DATE}

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/ ./src/
COPY config.yaml .

# Update version.py with build information
RUN if [ -f src/research_system/version.py ] && [ "$BUILD_NUMBER" != "dev" ]; then \
        sed -i "s/BUILD_NUMBER = \"[^\"]*\"/BUILD_NUMBER = \"$BUILD_NUMBER\"/" src/research_system/version.py && \
        sed -i "s/__version__ = \"[^\"]*\"/__version__ = \"$VERSION\"/" src/research_system/version.py && \
        if [ ! -z "$BUILD_DATE" ]; then \
            sed -i "s/BUILD_DATE = \"[^\"]*\"/BUILD_DATE = \"$BUILD_DATE\"/" src/research_system/version.py; \
        fi; \
    fi

# Display version information during build
RUN python -c "from src.research_system.version import get_version_info; print('Building version:', get_version_info())"

# Create data and log directories
RUN mkdir -p data logs && \
    chown -R appuser:appuser /app

EXPOSE 8181

# Switch to non-root user
USER appuser

# Set correct Python path
ENV PYTHONPATH=/app

# Add label with version info
LABEL org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      app.research-system.build-number="${BUILD_NUMBER}"

# Start FastAPI app with uvicorn
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8181"]