# Base image - start with a smaller image for efficiency
FROM ubuntu:slim

# Update and install essential dependencies
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    gcc libffi-dev musl-dev ffmpeg aria2 python3-pip \
    python3-venv  # Include python3-venv for virtual environment creation

# Clean up to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /venv

# Activate the virtual environment
ENV PATH="/venv/bin:$PATH"

# Work directory for your project
WORKDIR /app

# Copy your project files
COPY . /app/

# Install dependencies within the virtual environment
RUN pip3 install --no-cache-dir --upgrade --requirement Installer

# Execute your application 
CMD python3 modules/main.py 
