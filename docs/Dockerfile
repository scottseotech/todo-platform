FROM python:3.11-slim AS builder

WORKDIR /docs

# Install mkdocs and material theme
RUN pip install --no-cache-dir \
    mkdocs==1.5.3 \
    mkdocs-material==9.4.14 \
    pymdown-extensions==10.5

# Copy documentation files
COPY mkdocs.yml .
COPY nginx.conf .
COPY docs/ ./docs/

# Build the documentation
RUN mkdocs build

# Use nginx to serve the static files
FROM nginx:alpine

COPY --from=builder /docs/site /usr/share/nginx/html

# Copy nginx configuration from builder stage
COPY --from=builder /docs/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
