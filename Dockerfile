# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set Python environment variables to prevent cache files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv for fast package management
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install --system -r requirements.txt

# Development stage with auto-restart capability
FROM base AS development

# Install watchdog for auto-restart functionality
RUN uv pip install --system watchdog

# Copy application code (will be overridden by volume mount in development)
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Default command with auto-restart using watchmedo
CMD ["watchmedo", "auto-restart", "--directory", "/app", "--patterns", "*.py", "--recursive", "--", "python", "main.py"]

# Production stage (minimal and secure)
FROM base AS production

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Copy only necessary application files with proper ownership
COPY --chown=mcpuser:mcpuser main.py .
COPY --chown=mcpuser:mcpuser tools/ ./tools/

# Create necessary directories with proper permissions
RUN mkdir -p /tmp && chown mcpuser:mcpuser /tmp

# Set environment variables
ENV PYTHONPATH=/app

# Switch to non-root user
USER mcpuser

# Health check will be added to main.py instead

# Default command runs the MCP server via stdio
CMD ["python", "main.py"] 