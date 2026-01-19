# Name: Tan Kerry
# Matric No: 22004835
# Repository: https://github.com/wenthingteo/FYP_DesignSensei

# Base image - Using Python 3.9 slim for Django backend
FROM python:3.9-slim

# Set environment variables
# Prevents Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies file first (for better Docker layer caching)
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY backend/ .

# Expose the port Django runs on
EXPOSE 8000

# Run command - Start Django development server
# Using 0.0.0.0 to allow external connections to the container
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
