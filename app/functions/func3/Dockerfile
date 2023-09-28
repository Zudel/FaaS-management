FROM golang:latest AS build
WORKDIR /app
COPY ./ /app
RUN go mod download 
# Build
RUN CGO_ENABLED=0 GOOS=linux go build -o main 

# Deploy the application binary into a lean image
FROM gcr.io/distroless/base-debian11 AS build-release-stage

WORKDIR /

COPY --from=build /app/main main

EXPOSE 8082

USER nonroot:nonroot

CMD ["./main"]