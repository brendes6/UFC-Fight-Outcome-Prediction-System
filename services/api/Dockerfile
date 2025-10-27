# First stage with builder
FROM python:3.9-slim as builder

# Set the working directory
WORKDIR /app

# Copy and install dependencies first for caching
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code and data files
COPY . .

# Second stage
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the entire project from the builder stage
COPY --from=builder /app/services/ /app/services/

# Install the necessary packages for this image
COPY --from=builder /app/services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run our FastAPI app on the specified port
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8080"]