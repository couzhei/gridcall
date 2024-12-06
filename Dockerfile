# Base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Expose the port FastAPI will run on
EXPOSE 8000

# Start FastAPI
CMD ["python", "main.py"]
