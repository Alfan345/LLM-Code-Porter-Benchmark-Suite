# Use official lightweight Python 13 base image to match local development environment
FROM python:3.13-slim

# Install system-level dependencies (build-essential for g++, curl/ca-certificates for Rust installation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Rust compiler (rustc) officially via rustup
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
# Register rustc binary to system PATH environment variable
ENV PATH="/root/.cargo/bin:${PATH}"

# Setup working directory inside the container
WORKDIR /app

# Copy dependency definition and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project source files to the working directory
COPY . .

# Set environment variable to stream Python outputs directly to container logs
ENV PYTHONUNBUFFERED=1

# Document that the container listens on port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Execute the wrapper entry point at the root directory
CMD ["python", "app.py"]