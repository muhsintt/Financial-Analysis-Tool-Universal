# Certificates Directory

Place your SSL certificates here:

- `cert.pem` - SSL certificate
- `key.pem` - Private key

If you enable SSL without providing certificates, self-signed certificates will be generated automatically.

## Using your own certificates

### Option 1: Let's Encrypt (recommended for production)
```bash
# Install certbot
apt install certbot

# Generate certificate
certbot certonly --standalone -d yourdomain.com

# Copy certificates
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/key.pem
```

### Option 2: Generate self-signed certificate manually
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout key.pem \
    -out cert.pem \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```
