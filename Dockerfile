# Use Python 3.13 slim as the base image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Create cache directory with proper permissions
RUN mkdir -p /.cache && chmod 777 /.cache

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory with proper permissions for write access
# This allows the container to create and modify files in the data folder
# The app can rebuild from scratch if the data folder is empty
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy Python files
COPY app.py .
COPY utils.py .

# Expose port 7860
EXPOSE 7860

# Run the app using Python module (doesn't require uvicorn binary)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]