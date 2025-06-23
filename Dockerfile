# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# Make the main script executable
RUN chmod +x main.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command runs the MCP server via stdio
CMD ["python", "main.py"] 