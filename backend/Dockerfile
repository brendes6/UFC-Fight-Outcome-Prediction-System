# Builder stage
FROM golang:1.25 AS builder
WORKDIR /app

# Install C++ dependencies for ONNX
RUN apt-get update && apt-get install -y gcc g++ libc6-dev

COPY go.mod go.sum ./
RUN go mod download
COPY . .

# Build the binary
RUN CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build -v -o server .

# Build final lean image
FROM debian:bookworm-slim
WORKDIR /root/

RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy everything from builder
COPY --from=builder /app/server .
COPY --from=builder /app/model.onnx .
COPY --from=builder /app/onnxruntime.so .
ENV LD_LIBRARY_PATH=/root/

# Expose port and run
EXPOSE 8080
CMD ["./server"]