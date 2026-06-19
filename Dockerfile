# Use the official lightweight Python 3.10 image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Hugging Face Spaces exposes port 7860 by default
ENV PORT=7860 

# Install system dependencies (required for Playwright)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and its specific system dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the necessary backend code into the container
COPY backend/ /app/backend/
COPY src/ /app/src/
COPY run_attack.py /app/

# Expose the Hugging Face default port
EXPOSE 7860

# Command to run the FastAPI application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
