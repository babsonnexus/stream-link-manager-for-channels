# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download and install custom ffmpeg build
RUN wget https://github.com/yt-dlp/FFmpeg-Builds/releases/latest/download/ffmpeg_linux64.tar.xz -O /tmp/ffmpeg.tar.xz && \
    tar -xvf /tmp/ffmpeg.tar.xz -C /usr/local/bin --strip-components=1 && \
    rm /tmp/ffmpeg.tar.xz

# Test to ensure ffmpeg is installed and working
RUN ffmpeg -version

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Debugging step: Print the contents of requirements.txt
RUN cat requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV PORT=5000

# Run slm.py when the container launches
CMD ["python", "slm.py"]
