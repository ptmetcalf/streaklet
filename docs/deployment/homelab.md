# Homelab Integration

Deploy Streaklet in your homelab environment with reverse proxy, SSL, and monitoring.

## Overview

This guide covers:

- Reverse proxy configuration (nginx, Traefik, Caddy)
- SSL/TLS certificates
- Domain setup
- Integration with existing homelab stacks
- Monitoring and logging

## Prerequisites

- Docker and Docker Compose installed
- Domain name (or local DNS)
- Reverse proxy running (or ready to set up)

## Reverse Proxy Integration

### nginx Proxy Manager

Popular GUI-based reverse proxy for homelabs.

**1. Deploy Streaklet without port publishing:**

```yaml
# docker-compose.yml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    container_name: streaklet
    restart: unless-stopped
    networks:
      - proxy-network
    volumes:
      - ./data:/data
    environment:
      - APP_TIMEZONE=America/Chicago

networks:
  proxy-network:
    external: true
```

**2. Configure in nginx Proxy Manager:**

- **Domain Names**: `streaklet.yourdomain.com`
- **Scheme**: `http`
- **Forward Hostname**: `streaklet` (container name)
- **Forward Port**: `8080`
- **Cache Assets**: Enabled
- **Block Common Exploits**: Enabled
- **Websockets Support**: Enabled (for future features)
- **SSL**: Request Let's Encrypt certificate

### Traefik

Docker-native reverse proxy with automatic service discovery.

```yaml
# docker-compose.yml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    container_name: streaklet
    restart: unless-stopped
    networks:
      - traefik
    volumes:
      - ./data:/data
    environment:
      - APP_TIMEZONE=America/Chicago
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.streaklet.rule=Host(`streaklet.yourdomain.com`)"
      - "traefik.http.routers.streaklet.entrypoints=websecure"
      - "traefik.http.routers.streaklet.tls=true"
      - "traefik.http.routers.streaklet.tls.certresolver=letsencrypt"
      - "traefik.http.services.streaklet.loadbalancer.server.port=8080"

networks:
  traefik:
    external: true
```

### Caddy

Automatic HTTPS reverse proxy with simple configuration.

**Caddyfile:**
```
streaklet.yourdomain.com {
    reverse_proxy streaklet:8080
    encode gzip
}
```

**docker-compose.yml:**
```yaml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    container_name: streaklet
    restart: unless-stopped
    networks:
      - caddy
    volumes:
      - ./data:/data
    environment:
      - APP_TIMEZONE=America/Chicago

networks:
  caddy:
    external: true
```

### nginx (manual configuration)

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name streaklet.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name streaklet.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/streaklet.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/streaklet.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://streaklet:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # For PWA and service workers
        proxy_set_header Cache-Control "no-cache";

        # WebSocket support (future-proofing)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## DNS Configuration

### Internal DNS (Home Network Only)

**Option 1: Router DNS Override**
- Access router admin panel
- Add custom DNS entry: `streaklet.local` → `192.168.1.100`

**Option 2: Pi-hole**
```
# /etc/pihole/custom.list
192.168.1.100 streaklet.local
```

**Option 3: /etc/hosts (per-device)**
```
192.168.1.100 streaklet.local
```

### Public DNS (External Access)

Create an A record pointing to your public IP:
```
Type: A
Name: streaklet
Value: your.public.ip.address
TTL: 3600
```

Then set up port forwarding on your router: `443 → 192.168.1.100:443`

**Security Warning:** Exposing Streaklet publicly requires additional security measures. See [Security Considerations](#security-considerations) below.

## SSL/TLS Certificates

### Let's Encrypt (Recommended)

**With nginx Proxy Manager:**
- Built-in Let's Encrypt support
- Auto-renewal
- GUI-based setup

**With Certbot:**
```bash
certbot certonly --standalone -d streaklet.yourdomain.com
```

**With Caddy:**
- Automatic HTTPS by default
- No manual certificate management needed

**With Traefik:**
- Configure cert resolver in Traefik config
- Automatic certificate issuance and renewal

### Self-Signed (Internal Use Only)

Generate self-signed certificate:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout streaklet.key \
  -out streaklet.crt \
  -subj "/CN=streaklet.local"
```

**Note:** Browsers will show security warnings. Only use for internal testing.

## Network Configuration

### Internal Access Only

**Docker Compose with no port publishing:**
```yaml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    # No ports: section
    networks:
      - internal
    volumes:
      - ./data:/data

networks:
  internal:
    internal: true  # No external access
```

Access only through reverse proxy on the same network.

### Tailscale/Wireguard

Secure remote access via VPN:

**1. Install Tailscale on server**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

**2. Deploy Streaklet on internal network**
```yaml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    ports:
      - "8080:8080"  # Only accessible via Tailscale
    volumes:
      - ./data:/data
```

**3. Access via Tailscale IP**
```
http://100.x.x.x:8080
```

## Monitoring

### Health Checks

Streaklet provides a health endpoint: `GET /health`

**Monitor with Uptime Kuma:**
```
Monitor Type: HTTP(s)
URL: https://streaklet.yourdomain.com/health
Interval: 60 seconds
```

**Monitor with Healthchecks.io:**
```bash
# Add to crontab
*/5 * * * * curl -fsS https://streaklet.yourdomain.com/health | curl -fsS --retry 3 https://hc-ping.com/your-check-uuid > /dev/null
```

### Logging

**View logs:**
```bash
docker compose logs -f streaklet
```

**Send logs to external system (Loki, Graylog, etc.):**
```yaml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Integration with Promtail (for Loki):**
```yaml
services:
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

### Metrics

Streaklet doesn't expose Prometheus metrics yet, but you can monitor:
- Container health (Docker metrics)
- HTTP response times (via reverse proxy)
- Database size: `ls -lh ./data/app.db`

## Security Considerations

### Authentication

**Important:** Streaklet has no built-in authentication. It's designed for trusted networks.

**For public access, add authentication at the reverse proxy level:**

**nginx with HTTP Basic Auth:**
```nginx
location / {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://streaklet:8080;
}
```

Generate password file:
```bash
htpasswd -c /etc/nginx/.htpasswd username
```

**Traefik with Authelia:**
```yaml
labels:
  - "traefik.http.routers.streaklet.middlewares=authelia@docker"
```

**nginx Proxy Manager with Access List:**
- Create Access List with credentials
- Apply to Streaklet proxy host

### Firewall

Block direct access to port 8080:
```bash
# Allow only from reverse proxy
iptables -A INPUT -p tcp --dport 8080 -s 172.18.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP
```

### Docker Security

Run with additional security:
```yaml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
```

## Backup Strategies

### Automated Backups with Restic

```bash
# Install Restic
apt install restic

# Initialize repository
restic init --repo /mnt/backup/streaklet

# Backup script
#!/bin/bash
docker compose -f /opt/streaklet/docker-compose.yml stop
restic backup /opt/streaklet/data --repo /mnt/backup/streaklet
docker compose -f /opt/streaklet/docker-compose.yml start

# Add to crontab (daily at 3 AM)
0 3 * * * /opt/scripts/backup-streaklet.sh
```

### Backup to NAS

```yaml
services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    volumes:
      - /mnt/nas/streaklet:/data  # Direct NAS mount
```

Or use scheduled copy:
```bash
# Backup to NAS via cron
0 2 * * * rsync -avz /opt/streaklet/data/ /mnt/nas/streaklet-backup/
```

## Complete Homelab Example

**docker-compose.yml with Traefik, monitoring, and backups:**

```yaml
version: '3.8'

services:
  streaklet:
    image: ghcr.io/ptmetcalf/streaklet:latest
    container_name: streaklet
    restart: unless-stopped
    networks:
      - traefik
    volumes:
      - ./data:/data
    environment:
      - APP_TIMEZONE=America/Chicago
      - FITBIT_CLIENT_ID=${FITBIT_CLIENT_ID}
      - FITBIT_CLIENT_SECRET=${FITBIT_CLIENT_SECRET}
      - APP_SECRET_KEY=${APP_SECRET_KEY}
    labels:
      # Traefik
      - "traefik.enable=true"
      - "traefik.http.routers.streaklet.rule=Host(`streaklet.home.arpa`)"
      - "traefik.http.routers.streaklet.entrypoints=websecure"
      - "traefik.http.routers.streaklet.tls=true"
      - "traefik.http.services.streaklet.loadbalancer.server.port=8080"
      # Authelia auth
      - "traefik.http.routers.streaklet.middlewares=authelia@docker"
      # Metadata
      - "com.centurylinklabs.watchtower.enable=true"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

networks:
  traefik:
    external: true
```

## Troubleshooting

### Can't access through reverse proxy

1. Check container is running: `docker ps`
2. Verify network: `docker network inspect traefik`
3. Test direct access: `curl http://container-ip:8080/health`
4. Check reverse proxy logs

### SSL certificate issues

1. Verify DNS resolves: `nslookup streaklet.yourdomain.com`
2. Check port 80/443 are open: `telnet your-ip 443`
3. Review certificate logs in reverse proxy
4. Ensure firewall allows HTTP-01 challenge (Let's Encrypt)

### Performance issues

1. Check resource usage: `docker stats streaklet`
2. Monitor reverse proxy overhead
3. Enable caching in reverse proxy
4. Consider adding Redis cache (future feature)

## Next Steps

- [Configuration Guide](../getting-started/configuration.md) - Environment variables
- [Backup & Restore](../features/backup.md) - Data protection
- [Docker Compose](docker-compose.md) - Deployment details
