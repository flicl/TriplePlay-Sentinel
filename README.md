# TriplePlay-Sentinel

<div align="center">

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Zabbix](https://img.shields.io/badge/zabbix-6.0+-orange.svg)

**Enterprise-Grade Network Monitoring System for MikroTik-Zabbix Integration**

[Quick Start](#-quick-start) • [Documentation](docs/) • [API Reference](docs/api/) • [Templates](templates/zabbix/) • [Support](#-support)

</div>

---

## 🛡️ Overview

TriplePlay-Sentinel is a specialized network monitoring system that enables Zabbix to execute connectivity tests through MikroTik devices via SSH. Built with a modern HTTP Agent (PULL) architecture for maximum compatibility and performance.

### 🎯 Key Features

- **🏓 ICMP Ping Tests** - Latency, jitter, packet loss monitoring
- **🛤️ Traceroute Analysis** - Network path analysis with hop counting  
- **⚡ Smart Caching** - Redis-powered intelligent caching with configurable TTL
- **🔗 SSH Connection Pooling** - Optimized connection reuse for performance
- **📊 Health Monitoring** - Comprehensive monitoring and statistics endpoints
- **🌐 Web Dashboard** - Real-time monitoring interface
- **🐳 Docker Ready** - Production-ready containerized deployment

### 🏗️ Architecture

```
┌─────────────────┐    HTTP Agent    ┌──────────────────┐    SSH    ┌─────────────────┐
│   Zabbix Server │ ◄──────────────► │ TriplePlay       │ ◄────────► │ MikroTik Router │
│                 │    (REST API)    │ Sentinel         │           │                 │
└─────────────────┘                  │ Collector        │           └─────────────────┘
                                     └──────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │ Redis Cache      │
                                     │                  │
                                     └──────────────────┘
```
## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.9+** (for local development)
- **SSH access** to MikroTik devices
- **Zabbix Server 6.0+** with HTTP Agent support

### 🐳 Docker Deployment (Recommended)

#### Option 1: Docker Compose (Easy)
```bash
# 1. Clone repository
git clone <repository-url>
cd TriplePlay-Sentinel

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Deploy system
docker-compose up --build -d

# 4. Verify deployment
curl http://localhost:5000/api/health
```

#### Option 2: Docker Build & Run (Manual)
```bash
# Use the helper script
./docker-helper.sh build
./docker-helper.sh run-with-redis

# Or follow the detailed guide
# See: docs/guides/docker_build_and_run.md
```

**✅ System is now running at http://localhost:5000**

### 🔧 Local Development

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r src/collector/requirements.txt

# 2. Start services
./start_local.sh

# 3. Run tests
./run_tests.sh
```

---

## 📋 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 1 core | 2+ cores |
| **RAM** | 512MB | 1GB+ |
| **Storage** | 2GB | 5GB+ |
| **Network** | 100Mbps | 1Gbps+ |

### Compatibility Matrix

| Software | Version | Status |
|----------|---------|--------|
| **Zabbix Server** | 6.0+ | ✅ Tested |
| **MikroTik RouterOS** | 6.40+ | ✅ Tested |
| **Python** | 3.9+ | ✅ Required |
| **Redis** | 6.0+ | ✅ Included |
| **Docker** | 20.0+ | ✅ Recommended |

---

## 🔧 Configuration

### Environment Variables

```bash
# Basic Configuration
COLLECTOR_HOST=0.0.0.0
COLLECTOR_PORT=5000
LOG_LEVEL=INFO

# Redis Cache
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PASSWORD=your_secure_password
CACHE_TTL=30

# SSH Configuration
SSH_TIMEOUT=30
SSH_MAX_RETRIES=3

# Performance Tuning
MAX_WORKERS=10
REQUEST_TIMEOUT=60
```

### MikroTik Setup

```mikrotik
# Create dedicated monitoring user
/user add name=sentinel-monitor password=secure_password group=read

# Enable SSH service
/ip service set ssh port=22 disabled=no

# Configure firewall (if needed)
/ip firewall filter add chain=input protocol=tcp dst-port=22 \
    src-address=zabbix-server-ip action=accept
```

---

## 📡 API Reference

### Core Endpoints

#### Health Check
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "uptime": 3600,
  "components": {
    "redis": "connected",
    "mikrotik": "available"
  }
}
```

#### Connectivity Test
```http
POST /api/test
Content-Type: application/json

{
  "mikrotik_host": "192.168.1.1",
  "mikrotik_user": "sentinel-monitor",
  "mikrotik_password": "secure_password",
  "target": "8.8.8.8",
  "test_type": "ping",
  "count": 4
}
```

#### Connection Test
```http
POST /api/connection-test
Content-Type: application/json

{
  "mikrotik_host": "192.168.1.1",
  "mikrotik_user": "sentinel-monitor",
  "mikrotik_password": "secure_password"
}
```

### Response Examples

#### Ping Test Response
```json
{
  "status": "success",
  "test_type": "ping",
  "target": "8.8.8.8",
  "results": {
    "ping_stats": {
      "packets_sent": 4,
      "packets_received": 4,
      "packet_loss_percent": 0.0,
      "rtt_min_ms": 8.1,
      "rtt_avg_ms": 9.2,
      "rtt_max_ms": 10.5,
      "jitter_ms": 1.2
    }
  },
  "execution_time_seconds": 4.15,
  "cache_hit": false
}
```

#### Traceroute Test Response
```json
{
  "status": "success",
  "test_type": "traceroute",
  "target": "8.8.8.8",
  "results": {
    "traceroute_stats": {
      "hop_count": 10,
      "reached_target": true,
      "hops": [
        {
          "hop": 1,
          "address": "192.168.1.1",
          "loss_percent": 0.0,
          "avg_time_ms": 1.2
        }
      ]
    }
  },
  "execution_time_seconds": 7.43,
  "cache_hit": false
}
```

---

## 📊 Monitoring & Dashboards

### Web Dashboard
Access the built-in monitoring dashboard at:
**http://localhost:5000/dashboard**

Features:
- Real-time system status
- Cache performance metrics  
- Connection statistics
- Manual connectivity testing
- Performance graphs

### Zabbix Integration

#### 1. Import Template
```bash
# Template location
templates/zabbix/tripleplay-sentinel-template.yml
```

#### 2. Configure Host
- **Host Name**: `TriplePlay-Monitor-Site1`
- **Templates**: `TriplePlay-Sentinel Monitoring`
- **Macros**: Configure collector URL and MikroTik credentials

#### 3. Key Macros
```yaml
{$COLLECTOR_URL} = http://192.168.1.100:5000
{$MIKROTIK_HOST} = 192.168.1.1
{$MIKROTIK_USER} = sentinel-monitor
{$MIKROTIK_PASSWORD} = secure_password
{$TARGET_DNS1} = 8.8.8.8
{$TARGET_DNS2} = 1.1.1.1
```

---

## 🧪 Testing

### Automated Test Suite
```bash
# Run all tests
./run_tests.sh

# Test specific functionality
python3 test_collector.py
python3 test_traceroute.py
```

### Manual Testing
```bash
# Health check
curl http://localhost:5000/api/health

# Test ping functionality
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "admin",
    "mikrotik_password": "password",
    "target": "8.8.8.8",
    "test_type": "ping"
  }' \
  http://localhost:5000/api/test

# Test traceroute functionality
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "admin", 
    "mikrotik_password": "password",
    "target": "8.8.8.8",
    "test_type": "traceroute"
  }' \
  http://localhost:5000/api/test
```---

## 🔍 Troubleshooting

### Common Issues

#### ❌ Collector Service Not Starting
```bash
# Check logs
docker-compose logs sentinel-collector

# Verify configuration
docker exec -it tripleplay-sentinel-collector cat /app/.env

# Restart service
docker-compose restart sentinel-collector
```

#### ❌ SSH Connection Failures
```bash
# Test SSH connectivity manually
ssh admin@192.168.1.1

# Check MikroTik SSH service
/ip service print where name=ssh

# Verify user permissions
/user print where name=sentinel-monitor
```

#### ❌ Zabbix Items Not Collecting Data
```bash
# Test API endpoint manually
curl -X POST http://collector:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host":"IP","mikrotik_user":"user","target":"8.8.8.8","test_type":"ping"}'

# Check Zabbix server logs
tail -f /var/log/zabbix/zabbix_server.log

# Verify template configuration
# Configuration → Hosts → [Host] → Items
```

#### ❌ High Memory Usage
```bash
# Monitor resource usage
docker stats

# Adjust cache settings
# Set CACHE_TTL=60 in .env
# Set MAX_CACHE_SIZE=500 in .env

# Restart with new settings
docker-compose restart
```

### Performance Optimization

#### Cache Tuning
```bash
# Monitor cache performance
curl http://localhost:5000/api/stats

# Adjust TTL based on your needs
CACHE_TTL=30    # Fast-changing networks
CACHE_TTL=300   # Stable networks
```

#### Connection Pooling
```bash
# Optimize SSH connections
SSH_TIMEOUT=30        # Increase for slow networks
MAX_WORKERS=10        # Adjust based on load
```

### Log Analysis
```bash
# Application logs
tail -f src/collector/logs/sentinel.log

# Docker logs
docker-compose logs -f sentinel-collector

# Redis logs
docker-compose logs -f redis
```

---

## 🔒 Security

### Security Best Practices

#### Network Security
- Use dedicated monitoring VLANs
- Implement firewall rules for SSH access
- Enable SSH key authentication when possible
- Regularly rotate monitoring credentials

#### Application Security
```bash
# Enable authentication
ENABLE_AUTH=true
API_KEY=your-secure-api-key

# Use HTTPS in production
# Configure reverse proxy with SSL certificates
```

#### MikroTik Security
```mikrotik
# Create minimal privilege user
/user group add name=monitoring policy=read,test

# Create dedicated user
/user add name=sentinel-monitor group=monitoring password=complex-password

# Restrict SSH access
/ip service set ssh address=zabbix-server-ip
```

### Audit and Compliance
- All API calls are logged with timestamps
- Failed authentication attempts are tracked
- System health metrics are monitored
- Regular security assessments recommended

---

## 📚 Documentation

### 📖 Complete Documentation
- **[API Documentation](docs/api/)** - Detailed API reference
- **[Architecture Guide](docs/architecture/)** - System design and components
- **[Installation Guides](docs/guides/)** - Step-by-step setup instructions
- **[Zabbix Integration](docs/zabbix/)** - Template configuration and setup
- **[Security Guidelines](docs/security/)** - Security best practices
- **[Troubleshooting](docs/troubleshooting/)** - Common issues and solutions

### 🔗 Quick Links
- [Quick Start Guide](docs/guides/quick_start.md)
- [Docker Setup](docs/guides/docker_setup.md)
- [MikroTik Configuration](docs/guides/mikrotik_setup.md)
- [Zabbix Template Guide](templates/zabbix/README.md)
- [API Reference](docs/api/collector_api.md)

---

## 🏆 Performance Metrics

### Benchmark Results
- **Ping Tests**: ~200ms average execution time
- **Traceroute Tests**: ~5-7 seconds average execution time
- **Cache Hit Rate**: 85-95% typical performance
- **Memory Usage**: ~600MB total system footprint
- **Concurrent Requests**: 50+ requests/second supported

### Scalability
- **Single Instance**: Up to 100 MikroTik devices
- **Horizontal Scaling**: Multiple collector instances supported
- **Redis Clustering**: Supported for high availability
- **Load Balancing**: Compatible with standard load balancers

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

### Development Setup
```bash
# Fork the repository
git clone https://github.com/yourusername/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel

# Create development environment
python3 -m venv venv
source venv/bin/activate
pip install -r src/collector/requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run tests before committing
./run_tests.sh
```

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for all public functions
- Include unit tests for new features

### Submitting Changes
1. Create a feature branch
2. Make your changes
3. Add/update tests
4. Update documentation
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

### Getting Help
- **📖 Documentation**: Check the [docs/](docs/) directory first
- **🐛 Bug Reports**: Open an issue on GitHub
- **💡 Feature Requests**: Submit via GitHub issues
- **❓ Questions**: Use GitHub Discussions

### Community
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Wiki**: Community-maintained documentation

### Professional Support
Enterprise support and custom development services available upon request.

---

## 🏷️ Version History

### v2.1.0 (Current) - 2025-06-23
- ✅ **Clean Template**: Removed all TCP references for clarity
- ✅ **Optimized Architecture**: Simplified to 2 services only
- ✅ **Enhanced Documentation**: Complete documentation overhaul
- ✅ **Production Ready**: Fully tested and validated

### v2.0.0 - 2025-06-20
- 🔧 **Traceroute Fix**: Complete parser rewrite
- ⚡ **Performance**: Redis cache implementation
- 🛡️ **Security**: Enhanced SSH connection handling
- 📊 **Monitoring**: Improved health checks and metrics

### v1.0.0 - 2025-06-15
- 🎉 **Initial Release**: Basic ping and traceroute functionality
- 🏗️ **Foundation**: Core architecture and API design

---

<div align="center">

**TriplePlay-Sentinel** - Enterprise Network Monitoring Made Simple

[![GitHub stars](https://img.shields.io/github/stars/username/TriplePlay-Sentinel?style=social)](https://github.com/username/TriplePlay-Sentinel)
[![Docker Pulls](https://img.shields.io/docker/pulls/username/tripleplay-sentinel)](https://hub.docker.com/r/username/tripleplay-sentinel)

Made with ❤️ by the TriplePlay Development Team

</div>