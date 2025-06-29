# TriplePlay-Sentinel Documentation

This directory contains the complete documentation for TriplePlay-Sentinel, an enterprise-grade network monitoring system designed for MikroTik-Zabbix integration.

## 📖 Documentation Overview

TriplePlay-Sentinel provides a comprehensive monitoring solution that enables Zabbix to perform network connectivity tests through MikroTik devices via **100% API architecture**. The system features intelligent caching, connection pooling, parallel batch processing, and eliminates SSH dependencies for maximum performance and security.

## 🗂️ Documentation Structure

### 📋 Quick Reference
- **[INDEX.md](INDEX.md)** - Complete documentation index with navigation
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - High-level project overview

### 🚀 Getting Started
- **[guides/](guides/)** - Installation and setup guides
  - Quick Start Guide
  - Docker Setup Instructions
  - MikroTik Configuration
  - Zabbix Integration

### 📡 Technical Documentation
- **[api/](api/)** - Complete API reference and integration guides
- **[architecture/](architecture/)** - System design and architecture documentation
- **[security/](security/)** - Security guidelines and best practices

### 🐳 Deployment
- **[docker/](docker/)** - Docker-specific documentation and improvements

### 🔧 Configuration
- **[zabbix/](zabbix/)** - Zabbix configuration and template documentation

### 🛠️ Support & Troubleshooting
- **[troubleshooting/](troubleshooting/)** - Common issues and solutions

### 📋 Project Information
- **[project-management/](project-management/)** - Project status and management documentation
- **[changelog/](changelog/)** - Version history and changes
- **[releases/](releases/)** - Release notes and version information
- **[contributing/](contributing/)** - Development and contribution guidelines

### 🧹 Archive
- **[cleanup-history/](cleanup-history/)** - Historical project cleanup documentation

## 🎯 Key Features Documented

- **ICMP Ping Testing** - Comprehensive latency and packet loss monitoring via API
- **Traceroute Analysis** - Network path analysis with detailed hop information
- **Smart Caching** - Redis-powered caching with configurable TTL
- **API Connection Pooling** - Optimized MikroTik device connections using librouteros
- **Batch Processing** - Parallel command execution for maximum performance
- **Health Monitoring** - System health checks and performance metrics
- **Web Dashboard** - Real-time monitoring interface
- **Docker Deployment** - Production-ready containerization
- **SSL/TLS Support** - Secure API connections (8728/8729)

## 🔗 Quick Navigation

### New Users
1. Start with [Quick Start Guide](guides/quick_start.md)
2. Review [System Architecture](architecture/system_architecture.md)
3. Follow [Docker Setup](guides/docker_setup.md)

### Developers
1. Check [Contributing Guidelines](contributing/CONTRIBUTING.md)
2. Review [API Documentation](api/collector_api.md)
3. Understand [Architecture](architecture/system_architecture.md)

### System Administrators
1. Review [Security Guidelines](security/security_guidelines.md)
2. Configure [Zabbix Integration](zabbix/ZABBIX_CONFIGURATION.md)
3. Check [Troubleshooting Guide](troubleshooting/README.md)

## 📞 Support

For questions or issues not covered in this documentation:
- Check the [troubleshooting guide](troubleshooting/README.md)
- Review [GitHub Issues](https://github.com/username/TriplePlay-Sentinel/issues)
- Consult the [main README](../README.md) for contact information

---

*This documentation is actively maintained and updated with each release. For the latest information, always refer to the most recent version.*