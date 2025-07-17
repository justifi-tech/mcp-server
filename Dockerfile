# Use Python 3.12 slim image for smaller size and security patches
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Set Python environment variables to prevent cache files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv for fast package management
RUN pip install uv

# Development stage with auto-restart capability
FROM base AS development

# Copy pyproject.toml and source code for dependency installation
COPY pyproject.toml .
COPY justifi_mcp/ ./justifi_mcp/
COPY python/ ./python/
COPY modelcontextprotocol/ ./modelcontextprotocol/
COPY main.py .

# Install dev dependencies (includes all dependencies)
RUN uv pip install --system -e ".[dev]"

# Copy remaining application code (will be overridden by volume mount in development)
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Default command with auto-restart using watchmedo
CMD ["watchmedo", "auto-restart", "--directory", "/app", "--patterns", "*.py", "--recursive", "--", "python", "main.py"]

# Production stage (minimal and secure)
FROM base AS production

# Copy pyproject.toml and source code for dependency installation
COPY pyproject.toml .
COPY justifi_mcp/ ./justifi_mcp/
COPY python/ ./python/
COPY modelcontextprotocol/ ./modelcontextprotocol/
COPY main.py .

# Install production dependencies only
RUN uv pip install --system .

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Change ownership of application files to non-root user
RUN chown -R mcpuser:mcpuser /app

# Set environment variables
ENV PYTHONPATH=/app

# Switch to non-root user
USER mcpuser

# Health check will be added to main.py instead

# Default command runs the MCP server via stdio
CMD ["python", "main.py"] 