#!/bin/bash
set -e

CERT_DIR="/etc/nginx/ssl"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

# Check if SSL is enabled
if [ "$SSL_ENABLED" = "true" ]; then
    echo "============================================"
    echo "SSL/HTTPS Mode Enabled"
    echo "============================================"
    
    # Check if certificates exist
    if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
        echo "Certificates not found. Generating self-signed certificate..."
        
        # Generate self-signed certificate
        openssl req -x509 -newkey rsa:2048 -nodes \
            -keyout "$KEY_FILE" \
            -out "$CERT_FILE" \
            -days 365 \
            -subj "/C=US/ST=State/L=City/O=FinancialAnalysisTool/CN=localhost"
        
        echo "Self-signed certificate generated!"
        echo "  Certificate: $CERT_FILE"
        echo "  Private Key: $KEY_FILE"
        echo ""
        echo "WARNING: Self-signed certificates will show browser warnings."
        echo "  For production, use proper certificates from a CA."
    else
        echo "Using existing SSL certificates."
    fi
    
    echo "============================================"
    echo "Starting NGINX with HTTPS..."
    echo "  HTTP:  http://<your-ip>:80 (redirects to HTTPS)"
    echo "  HTTPS: https://<your-ip>:443"
    echo "============================================"
    
    # Use SSL config
    cp /etc/nginx/nginx-ssl.conf /etc/nginx/nginx.conf
else
    echo "============================================"
    echo "HTTP Mode (SSL disabled)"
    echo "============================================"
    echo "Starting NGINX with HTTP only..."
    echo "  HTTP: http://<your-ip>:80"
    echo ""
    echo "To enable HTTPS, set SSL_ENABLED=true"
    echo "============================================"
    
    # Use HTTP-only config
    cp /etc/nginx/nginx-http.conf /etc/nginx/nginx.conf
fi

# Start nginx
exec nginx -g "daemon off;"
