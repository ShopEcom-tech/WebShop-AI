# Rust Gateway Dockerfile
FROM rust:1.75-alpine as builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache musl-dev pkgconfig openssl-dev

# Copy source
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Build release
RUN cargo build --release

# Runtime image
FROM alpine:3.19

RUN apk add --no-cache ca-certificates libgcc

WORKDIR /app

COPY --from=builder /app/target/release/webshop-ai-gateway /app/gateway

ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

CMD ["/app/gateway"]
