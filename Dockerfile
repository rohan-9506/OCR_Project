FROM python:3.10

# Install system packages: Tesseract, Poppler, libGL for OpenCV, and optional GLib
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy application files
COPY app/ /app/

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Run both Flask and worker
CMD ["sh", "-c", "python main.py & python worker.py"]
