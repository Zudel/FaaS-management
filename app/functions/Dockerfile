FROM golang:latest
WORKDIR /app
COPY ./ ./
RUN go mod download
# Build
RUN CGO_ENABLED=0 GOOS=linux go build -o main
CMD ["./main"]
