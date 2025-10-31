FROM python:3.11-slim

WORKDIR /docs

# Install mkdocs and material theme
RUN pip install --no-cache-dir \
    mkdocs==1.5.3 \
    mkdocs-material==9.4.14 \
    pymdown-extensions==10.5

# Copy documentation files
COPY mkdocs.yml .
COPY docs/ ./docs/

# Build the documentation
RUN mkdocs build

# Use nginx to serve the static files
FROM nginx:alpine

COPY --from=0 /docs/site /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
