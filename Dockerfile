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

# Production stage (minimal)
FROM base as production

# Copy only necessary application files
COPY main.py .
COPY tools/ ./tools/
COPY .env* ./

# Make the main script executable
RUN chmod +x main.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command runs the MCP server via stdio
CMD ["python", "main.py"] 