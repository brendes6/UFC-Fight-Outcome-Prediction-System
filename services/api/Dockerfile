# Stage 1: The builder stage for dependencies
FROM python:3.9-slim as builder

# Set the working directory
WORKDIR /app

# Copy and install dependencies first for caching
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code and data files
COPY . .

# Stage 2: The final production image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the entire project from the builder stage
# This ensures all files are in the right relative locations
COPY --from=builder /app/services/ /app/services/

# Install the necessary packages for this image
COPY --from=builder /app/services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# This sets the Python path and runs the script
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8080"]