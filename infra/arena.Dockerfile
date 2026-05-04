FROM golang:1.24-alpine AS builder
WORKDIR /build
COPY arena/go.mod arena/go.sum ./
RUN go mod download
COPY arena/ .
RUN CGO_ENABLED=0 go build -o /arena-server ./cmd/server.go

FROM alpine:3.19
RUN apk add --no-cache docker-cli
COPY --from=builder /arena-server /usr/local/bin/arena-server
EXPOSE 8080
CMD ["arena-server"]
