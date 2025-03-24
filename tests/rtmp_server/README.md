# RTMP Test Server

A minimal RTMP server for testing the VoxBridge audio streaming functionality, with built-in debugging capabilities.

## Quick Start

1. Start the server:

```bash
cd tests/rtmp_server
docker-compose up -d
```

2. Check server status:

```bash
# Check status page
curl http://localhost:8080
```

3. Stream test audio:

```bash
python src/common/rtmp_sender.py data/sample_sermon.wav
```

## Troubleshooting Guide

### 1. Server Issues

Check server status:

```bash
# Check nginx process
docker-compose exec rtmp ps aux | grep nginx

# View error logs
docker-compose exec rtmp tail -f /var/log/nginx/error.log
```

### 2. Module Loading Issues

Verify RTMP module:

```bash
# Check module files
docker-compose exec rtmp ls -l /usr/lib/nginx/modules/

# Verify nginx configuration
docker-compose exec rtmp nginx -t

# Show nginx version and modules
docker-compose exec rtmp nginx -V
```

### 3. Connection Problems

Check network status:

```bash
# Verify ports
docker-compose exec rtmp netstat -tlpn | grep nginx

# Monitor RTMP traffic
docker-compose exec rtmp tcpdump -i any port 1935

# Test RTMP port
nc -zv localhost 1935
```

### 4. Streaming Issues

1. Verify stream settings:

   - URL: rtmp://localhost/live/test
   - Port: 1935
   - Protocol: RTMP

2. Monitor stream:

```bash
# Watch logs in real-time
docker-compose logs -f rtmp

# Check network traffic
docker-compose exec rtmp tcpdump -i any port 1935
```

### 5. Common Error Messages

1. "unknown directive rtmp":

   - Check module installation
   - Verify nginx.conf module loading
   - Restart container

2. "Connection refused":

   - Verify nginx is running
   - Check port availability
   - Review firewall settings

3. "Failed to connect":
   - Verify RTMP URL
   - Check network connectivity
   - Monitor error logs

## Status Page

Visit http://localhost:8080 for:

- Server status
- Stream information
- Real-time updates
