# TriplePlay-Sentinel

<div align="center">

![Version](https# Clone repository
git clone https://github.com/flicl/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy system
docker-compose up --build -d

# Verify deployment
curl http://localhost:5000/api/healths.io/badge/version-2.1.0-blue.svg)
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

## 📡 API Reference

### Core Endpoints

#### Health Check
```http
GET /api/health
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

---

## 📊 Monitoring & Dashboards

### Web Dashboard
Access the built-in monitoring dashboard at:
**http://localhost:5000/dashboard**

### Zabbix Integration

1. **Import Template**: `templates/zabbix/tripleplay-sentinel-template.yml`
2. **Configure Host**: Add your MikroTik credentials in macros
3. **Monitor**: Start collecting network performance data

---

## 📚 Documentation

### Complete Documentation Structure

```
docs/
├── api/                    # API Documentation
├── architecture/           # System Architecture
├── guides/                # Installation & Setup Guides
├── docker/                # Docker-specific documentation
├── zabbix/                # Zabbix Integration
├── security/              # Security Guidelines
├── troubleshooting/       # Common Issues & Solutions
├── changelog/             # Version History
├── releases/              # Release Notes
├── project-management/    # Project Documentation
└── contributing/          # Development Guidelines
```

### 🔗 Quick Links
- [Quick Start Guide](docs/guides/quick_start.md)
- [Docker Setup](docs/guides/docker_setup.md)
- [MikroTik Configuration](docs/guides/mikrotik_setup.md)
- [API Reference](docs/api/collector_api.md)
- [Troubleshooting](docs/troubleshooting/README.md)

---

## 🧪 Testing

```bash
# Run all tests
./run_tests.sh

# Health check
curl http://localhost:5000/api/health

# Manual API test
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "admin",
    "mikrotik_password": "password",
    "target": "8.8.8.8",
    "test_type": "ping"
  }' \
  http://localhost:5000/api/test
```

---

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](docs/contributing/CONTRIBUTING.md).

### Development Setup
```bash
# Fork and clone
git clone https://github.com/flicl/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r src/collector/requirements.txt

# Run tests before committing
./run_tests.sh
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **📖 Documentation**: Check the [docs/](docs/) directory first
- **🐛 Bug Reports**: Open an issue on GitHub
- **💡 Feature Requests**: Submit via GitHub issues
- **❓ Questions**: Use GitHub Discussions

---

## 🏷️ Version History

- **v2.1.0** (Current) - Production Ready Release
- **v2.0.0** - Enhanced Performance & Security
- **v1.0.0** - Initial Release

For detailed changelog, see [docs/changelog/CHANGELOG.md](docs/changelog/CHANGELOG.md)

---

<div align="center">

**TriplePlay-Sentinel** - Enterprise Network Monitoring Made Simple

Made with ❤️ by the TriplePlay Development Team

</div>