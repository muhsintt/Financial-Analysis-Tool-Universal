#!/bin/bash
set -e

# Generate self-signed certificate if SSL is enabled and no certs exist
if [ "$SSL_ENABLED" = "true" ]; then
    CERT_FILE="${SSL_CERT_FILE:-/app/certs/cert.pem}"
    KEY_FILE="${SSL_KEY_FILE:-/app/certs/key.pem}"
    CERT_DIR=$(dirname "$CERT_FILE")
    
    # Ensure certs directory exists
    mkdir -p "$CERT_DIR" 2>/dev/null || true
    
    if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
        echo "============================================"
        echo "SSL enabled but certificates not found."
        echo "Generating self-signed certificate..."
        echo "============================================"
        
        # Generate self-signed certificate
        if openssl req -x509 -newkey rsa:2048 -nodes \
            -keyout "$KEY_FILE" \
            -out "$CERT_FILE" \
            -days 365 \
            -subj "/C=US/ST=State/L=City/O=FinancialAnalysisTool/CN=localhost" 2>/dev/null; then
            echo "Self-signed certificate generated successfully!"
            echo "  Certificate: $CERT_FILE"
            echo "  Private Key: $KEY_FILE"
            echo "  Valid for: 365 days"
            echo ""
            echo "WARNING: Self-signed certificates will show browser warnings."
            echo "  For production, use proper certificates from a CA."
            echo "============================================"
        else
            echo "Failed to generate self-signed certificate!"
            echo "  Check that the certs directory is writable."
            echo "  Falling back to HTTP only..."
            echo "============================================"
            exec gunicorn \
                --bind 0.0.0.0:5000 \
                --workers 2 \
                --threads 4 \
                run:app
        fi
    else
        echo "============================================"
        echo "Using existing SSL certificates:"
        echo "  Certificate: $CERT_FILE"
        echo "  Private Key: $KEY_FILE"
        echo "============================================"
    fi
    
    echo "Starting server with HTTPS on port 5443..."
    echo "Access the application at: https://<your-ip>:5443"
    echo "============================================"
    exec gunicorn \
        --bind 0.0.0.0:5443 \
        --workers 2 \
        --threads 4 \
        --certfile "$CERT_FILE" \
        --keyfile "$KEY_FILE" \
        run:app
else
    echo "============================================"
    echo "Starting server with HTTP on port 5000..."
    echo "Access the application at: http://<your-ip>:5000"
    echo "(Set SSL_ENABLED=true for HTTPS)"
    echo "============================================"
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 2 \
        --threads 4 \
        run:app
fi
