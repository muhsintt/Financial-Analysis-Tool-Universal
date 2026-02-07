FROM nginx:alpine

# Install openssl for certificate generation
RUN apk add --no-cache openssl bash

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl

# Copy nginx configurations
COPY nginx.conf /etc/nginx/nginx-ssl.conf
COPY nginx-http.conf /etc/nginx/nginx-http.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Fix line endings and make executable
RUN sed -i 's/\r$//' /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Expose ports
EXPOSE 80 443

ENTRYPOINT ["/docker-entrypoint.sh"]
