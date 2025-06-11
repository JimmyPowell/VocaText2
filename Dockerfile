# Stage 1: Build the frontend
# We use a standard Node image here as this stage is temporary and reliable.
FROM node:20-alpine AS builder

WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


# Stage 2: Create the final application from a clean Ubuntu base
# This is the most reliable approach to avoid base image issues.
FROM ubuntu:22.04

# Set non-interactive frontend to avoid prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install all system dependencies from scratch
# Includes python, pip, and our audio/build dependencies
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY backend/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the backend source code
COPY backend/ ./

# Copy the built frontend from the builder stage
COPY --from=builder /app/frontend/dist ./static

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using python3
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
