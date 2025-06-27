# 🚀 TriplePlay-Sentinel Quick Start Guide

<div align="center">

![Quick Start](https://img.shields.io/badge/Setup%20Time-15%20minutes-green.svg)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-green.svg)
![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)

**Get your network monitoring system running in 15 minutes**

[Prerequisites](#-prerequisites) • [Installation](#-installation) • [Configuration](#-configuration) • [Verification](#-verification) • [Next Steps](#-next-steps)

</div>

---

## 📋 Prerequisites

### 🖥️ System Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 1 core | 2+ cores | For concurrent testing |
| **RAM** | 512MB | 1GB+ | Includes Redis cache |
| **Storage** | 2GB | 5GB+ | For logs and cache |
| **Network** | 100Mbps | 1Gbps+ | SSH + HTTP traffic |

### 📦 Software Dependencies

#### Required
```bash
# Check Docker installation
docker --version          # >= 20.10.0
docker-compose --version  # >= 1.29.0

# Check network connectivity
ping 8.8.8.8              # Internet access
ssh admin@your-mikrotik    # MikroTik SSH access
```

#### Optional (for local development)
```bash
# Python development
python3 --version         # >= 3.9
pip3 --version

# Git for cloning
git --version
```

### 🌐 Network Access Requirements

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| **Zabbix Server** | Collector | 5000 | HTTP | API calls |
| **Collector** | MikroTik | 22 | SSH | Device commands |
| **Collector** | Redis | 6379 | TCP | Cache operations |
| **Admin** | Collector | 5000 | HTTP | Dashboard access |

### 🛡️ MikroTik Prerequisites

```mikrotik
# Enable SSH service
/ip service set ssh disabled=no port=22

# Create monitoring user
/user add name=sentinel-monitor password=SecurePassword123 group=read

# Optional: Restrict SSH access to monitoring server
/ip service set ssh address=your-zabbix-server-ip
```

---

## ⚡ Quick Installation

### Option 1: Docker Deployment (Recommended)

#### Step 1: Clone Repository
```bash
# Clone the repository
git clone https://github.com/username/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel

# Verify files
ls -la
```

#### Step 2: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your preferred editor)
nano .env
```

**Essential Settings:**
```bash
# Basic Configuration
COLLECTOR_HOST=0.0.0.0
COLLECTOR_PORT=5000
LOG_LEVEL=INFO

# Security (optional but recommended)
ENABLE_AUTH=false
API_KEY=

# Cache Configuration
CACHE_TTL=30
REDIS_PASSWORD=

# Performance Tuning
MAX_WORKERS=10
SSH_TIMEOUT=30
```

#### Step 3: Deploy System
```bash
# Build and start services
docker-compose up --build -d

# Check service status
docker-compose ps
```

**Expected Output:**
```
Name                        Command               State           Ports
-------------------------------------------------------------------------
tripleplay-sentinel-collector   /app/start.sh                    Up      0.0.0.0:5000->5000/tcp
tripleplay-redis                redis-server --appendonly yes   Up      6379/tcp
```

#### Step 4: Verify Installation
```bash
# Health check
curl http://localhost:5000/api/health

# Expected response
{
  "status": "healthy",
  "version": "2.1.0",
  "uptime_seconds": 30,
  "components": {
    "redis": "connected"
  }
}
```

### Option 2: Local Development Setup

#### Step 1: Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd src/collector
pip install -r requirements.txt
```

#### Step 2: Start Redis (Optional)
```bash
# Install Redis locally or use Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Or disable Redis in .env
echo "REDIS_ENABLED=false" >> .env
```

#### Step 3: Start Collector
```bash
# Start the application
python app.py

# Or use the start script
./start_local.sh
```

---

## 🔧 Configuration

### Basic Configuration

#### Environment Variables Overview
```bash
# Core Settings
COLLECTOR_HOST=0.0.0.0           # Listen on all interfaces
COLLECTOR_PORT=5000              # API port
LOG_LEVEL=INFO                   # Logging verbosity

# Cache Settings
REDIS_ENABLED=true               # Enable Redis cache
REDIS_HOST=redis                 # Redis hostname
CACHE_TTL=30                     # Cache TTL in seconds

# SSH Settings
SSH_TIMEOUT=30                   # SSH connection timeout
SSH_MAX_RETRIES=3               # Retry attempts

# Performance
MAX_WORKERS=10                   # Concurrent workers
REQUEST_TIMEOUT=60               # API request timeout
```

#### Security Configuration (Production)
```bash
# Enable API authentication
ENABLE_AUTH=true

# Generate secure API key
API_KEY=$(openssl rand -hex 32)
echo "API_KEY=${API_KEY}" >> .env

# Secure Redis
REDIS_PASSWORD=$(openssl rand -hex 16)
echo "REDIS_PASSWORD=${REDIS_PASSWORD}" >> .env
```

### MikroTik Device Setup

#### Create Monitoring User
```mikrotik
# Create user with minimal privileges
/user group add name=monitoring policy=read,test

# Create user
/user add name=sentinel-monitor \
          password=SecurePassword123 \
          group=monitoring \
          comment="TriplePlay Sentinel monitoring user"

# Verify user creation
/user print where name=sentinel-monitor
```

#### Configure SSH Access
```mikrotik
# Enable SSH service
/ip service enable ssh
/ip service set ssh port=22

# Optional: Restrict source IPs
/ip service set ssh address=192.168.1.100/32

# Test SSH connectivity
/system ssh-exec address=192.168.1.100 user=test-user command="/system identity print"
```

#### Firewall Configuration (if needed)
```mikrotik
# Allow SSH from monitoring server
/ip firewall filter add \
    chain=input \
    protocol=tcp \
    dst-port=22 \
    src-address=192.168.1.100 \
    action=accept \
    comment="TriplePlay Sentinel SSH access"
```

---

## ✅ System Verification

### Health Checks

#### 1. Service Status
```bash
# Check running containers
docker-compose ps

# Check service logs
docker-compose logs -f sentinel-collector
docker-compose logs redis
```

#### 2. API Connectivity
```bash
# Basic health check
curl -s http://localhost:5000/api/health | jq '.'

# Detailed stats
curl -s http://localhost:5000/api/stats | jq '.cache'
```

#### 3. MikroTik Connectivity Test
```bash
# Test SSH connection to MikroTik
curl -X POST http://localhost:5000/api/connection-test \
  -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "sentinel-monitor",
    "mikrotik_password": "SecurePassword123"
  }' | jq '.'
```

**Expected Response:**
```json
{
  "status": "success",
  "connection_test": {
    "ssh_connection_successful": true,
    "connection_time_ms": 156,
    "authentication_successful": true
  }
}
```

#### 4. Full Test Execution
```bash
# Execute ping test
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "sentinel-monitor",
    "mikrotik_password": "SecurePassword123",
    "target": "8.8.8.8",
    "test_type": "ping",
    "count": 4
  }' | jq '.results.ping_stats'
```

**Expected Response:**
```json
{
  "packets_sent": 4,
  "packets_received": 4,
  "packet_loss_percent": 0,
  "rtt_avg_ms": 12.5,
  "jitter_ms": 1.2
}
```

### Performance Verification

#### Load Testing
```bash
# Install Apache Bench (optional)
apt-get install apache2-utils

# Test API performance
ab -n 100 -c 10 -H "Content-Type: application/json" \
   -p test-payload.json \
   http://localhost:5000/api/test

# Monitor system resources
docker stats
```

#### Cache Performance
```bash
# Check cache hit rate
curl -s http://localhost:5000/api/stats | jq '.cache.hit_rate_percent'

# Should be > 0% after repeated tests
# Optimal range: 80-95%
```

---

## 📊 Web Dashboard

### Access Dashboard
```bash
# Open web dashboard
open http://localhost:5000/dashboard

# Or via curl
curl http://localhost:5000/dashboard
```

### Dashboard Features
- **🎯 System Status**: Real-time health monitoring
- **📈 Performance Metrics**: Cache hit rates, response times
- **🔧 Test Interface**: Manual test execution
- **📋 Statistics**: Historical data and trends
- **🔍 Diagnostics**: Connection status and troubleshooting

---

## 🎯 Zabbix Integration

### Quick Zabbix Setup

#### 1. Import Template
```bash
# Template location
templates/zabbix/tripleplay-sentinel-template.yml

# In Zabbix Web Interface:
# 1. Go to Configuration → Templates
# 2. Click Import
# 3. Select the YAML file
# 4. Click Import
```

#### 2. Create Host
```yaml
Host Configuration:
  Host name: TriplePlay-Monitor-Site1
  Visible name: TriplePlay Sentinel - Site 1
  Groups: TriplePlay-Sentinel
  Interfaces: None required (HTTP Agent)
  Templates: TriplePlay-Sentinel Monitoring
```

#### 3. Configure Macros
```yaml
Required Macros:
  {$COLLECTOR_URL}: http://192.168.1.100:5000
  {$MIKROTIK_HOST}: 192.168.1.1
  {$MIKROTIK_USER}: sentinel-monitor
  {$MIKROTIK_PASSWORD}: SecurePassword123
  {$TARGET_DNS1}: 8.8.8.8
  {$TARGET_DNS2}: 1.1.1.1
```

#### 4. Verify Data Collection
```bash
# Check latest data in Zabbix
# Monitoring → Latest data
# Filter by host: TriplePlay-Monitor-Site1

# Look for items like:
# - Ping Loss [8.8.8.8]
# - Ping RTT Average [8.8.8.8]
# - Network Quality Score [8.8.8.8]
```

---

## 🔍 Troubleshooting

### Common Issues

#### ❌ Container Won't Start
```bash
# Check logs
docker-compose logs sentinel-collector

# Common causes:
# - Port 5000 already in use
# - Invalid environment configuration
# - Missing Redis connection

# Solutions:
docker-compose down
docker-compose up --build
```

#### ❌ SSH Connection Fails
```bash
# Test SSH manually
ssh sentinel-monitor@192.168.1.1

# Check MikroTik configuration
/user print where name=sentinel-monitor
/ip service print where name=ssh

# Verify network connectivity
ping 192.168.1.1
telnet 192.168.1.1 22
```

#### ❌ API Returns Errors
```bash
# Check API health
curl http://localhost:5000/api/health

# Check application logs
docker-compose logs -f sentinel-collector

# Validate request format
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{"test": "invalid"}' -v
```

#### ❌ Zabbix Items Not Working
```bash
# Test Zabbix HTTP Agent manually
curl -X POST http://collector-ip:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "sentinel-monitor",
    "mikrotik_password": "password",
    "target": "8.8.8.8",
    "test_type": "ping"
  }'

# Check Zabbix server logs
tail -f /var/log/zabbix/zabbix_server.log | grep -i http

# Verify template import
# Configuration → Templates → TriplePlay-Sentinel Monitoring
```

### Performance Issues

#### Slow Response Times
```bash
# Check system resources
docker stats

# Optimize cache settings
echo "CACHE_TTL=60" >> .env
echo "MAX_WORKERS=20" >> .env

# Restart services
docker-compose restart
```

#### High Memory Usage
```bash
# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Optimize Redis
echo "REDIS_MAXMEMORY=256mb" >> .env
docker-compose restart redis
```

---

## 🎯 Next Steps

### 1. Production Deployment
- [ ] **Security**: Enable authentication and HTTPS
- [ ] **Monitoring**: Set up comprehensive health monitoring
- [ ] **Backup**: Configure Redis data persistence
- [ ] **Scaling**: Plan for multiple collector instances

### 2. Advanced Configuration
- [ ] **Performance Tuning**: Optimize cache and connection settings
- [ ] **Custom Dashboards**: Create specific monitoring views
- [ ] **Alerting**: Configure Zabbix triggers and notifications
- [ ] **Integration**: Connect with other monitoring systems

### 3. Operational Excellence
- [ ] **Documentation**: Document your specific configuration
- [ ] **Runbooks**: Create operational procedures
- [ ] **Training**: Train team members on the system
- [ ] **Maintenance**: Plan regular maintenance windows

---

## 📚 Additional Resources

### Documentation
- **[Complete Setup Guide](docker_setup.md)** - Detailed Docker configuration
- **[API Reference](../api/collector_api.md)** - Complete API documentation
- **[Security Guidelines](../security/security_guidelines.md)** - Security best practices
- **[Troubleshooting Guide](../troubleshooting/README.md)** - Detailed problem resolution

### Community & Support
- **[GitHub Issues](https://github.com/username/TriplePlay-Sentinel/issues)** - Bug reports and features
- **[GitHub Discussions](https://github.com/username/TriplePlay-Sentinel/discussions)** - Community support
- **[Contributing Guide](../../CONTRIBUTING.md)** - How to contribute

### External Resources
- **[Zabbix Documentation](https://www.zabbix.com/documentation/6.0)** - Official Zabbix docs
- **[MikroTik Wiki](https://wiki.mikrotik.com/)** - RouterOS documentation
- **[Docker Documentation](https://docs.docker.com/)** - Container management

---

<div align="center">

**🎉 Congratulations! Your TriplePlay-Sentinel system is now ready for network monitoring.**

[![System Status](https://img.shields.io/badge/System%20Status-Online-green.svg)](http://localhost:5000/api/health)
[![Dashboard](https://img.shields.io/badge/Dashboard-Available-blue.svg)](http://localhost:5000/dashboard)

**Need help?** Check our [troubleshooting guide](../troubleshooting/README.md) or [open an issue](https://github.com/username/TriplePlay-Sentinel/issues).

</div>