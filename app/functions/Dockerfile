FROM golang:latest
WORKDIR /app
COPY ./ ./
# Visualizza il contenuto della directory di lavoro del container
RUN ls -al
# Visualizza l'output del comando "go env" per ottenere informazioni sulla configurazione di Go nel container
RUN go env
RUN go mod download
# Build
RUN CGO_ENABLED=0 GOOS=linux go build -o main
CMD ["./main"]
