# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    wget \
    xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download and install custom ffmpeg build
RUN wget https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz -O /tmp/ffmpeg.tar.xz && \
    mkdir -p /tmp/ffmpeg && \
    tar -xvf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1 && \
    mv /tmp/ffmpeg/bin/ffmpeg /usr/local/bin/ffmpeg && \
    mv /tmp/ffmpeg/bin/ffprobe /usr/local/bin/ffprobe && \
    mkdir -p /usr/share/doc/ffmpeg && \
    mv /tmp/ffmpeg/doc/* /usr/share/doc/ffmpeg/ && \
    mkdir -p /usr/share/man/man1 && \
    mv /tmp/ffmpeg/man/man1/* /usr/share/man/man1/ && \
    mkdir -p /usr/share/licenses/ffmpeg && \
    mv /tmp/ffmpeg/LICENSE.txt /usr/share/licenses/ffmpeg/ && \
    rm -rf /tmp/ffmpeg /tmp/ffmpeg.tar.xz

# Add /usr/local/bin to PATH
ENV PATH="/usr/local/bin:${PATH}"

# Debugging step: Check if ffmpeg and ffprobe are in the correct location
RUN ls -l /usr/local/bin/ffmpeg && ls -l /usr/local/bin/ffprobe

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
