# Stage 1: Build dependencies
FROM python:3.9-slim as builder
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.9-slim
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy scripts directly into /app
COPY . .

# Run command
CMD ["python", "main.py"]