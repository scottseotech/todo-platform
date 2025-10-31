FROM python:3.11-slim AS builder

WORKDIR /docs

RUN pip install --no-cache-dir \
    mkdocs==1.5.3 \
    mkdocs-material==9.4.14 \
    pymdown-extensions==10.5

COPY mkdocs.yml .
COPY nginx.conf .
COPY docs/ ./docs/

RUN mkdocs build

# Final stage

FROM nginx:alpine

COPY --from=builder /docs/site /usr/share/nginx/html

COPY --from=builder /docs/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
