# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install --system -r requirements.txt

# Development stage with linting tools
FROM base as development

# Copy application code
COPY . .

# Make the main script executable
RUN chmod +x main.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command for development (can be overridden)
CMD ["python", "main.py"]

# Production stage (minimal and secure)
FROM base as production

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Copy only necessary application files with proper ownership
COPY --chown=mcpuser:mcpuser main.py .
COPY --chown=mcpuser:mcpuser tools/ ./tools/

# Don't copy .env files - they should be provided at runtime
# COPY .env* ./

# Create necessary directories with proper permissions
RUN mkdir -p /tmp && chown mcpuser:mcpuser /tmp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER mcpuser

# Health check will be added to main.py instead

# Default command runs the MCP server via stdio
CMD ["python", "main.py"] 