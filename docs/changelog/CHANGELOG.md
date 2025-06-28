# Changelog

All notable changes to TriplePlay-Sentinel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Performance metrics endpoint
- Advanced caching strategies
- Bulk test execution support

### Changed
- Improved error handling for network timeouts
- Enhanced logging with structured format

### Security
- Updated dependencies to latest secure versions

## [2.1.0] - 2025-06-28

### 🧹 Major Cleanup & Documentation Overhaul

#### Added
- Complete project structure reorganization following industry standards
- Professional documentation structure with categorized organization
- Automated link checking system (`check_links.sh`)
- Centralized URL and link management system
- Contributing guidelines and development standards
- Enhanced API documentation with detailed examples
- Performance benchmarking and metrics
- Security best practices documentation
- Professional README with badges and clear structure
- Project management documentation tracking
- Comprehensive troubleshooting guides

#### Changed
- **BREAKING**: Simplified architecture to 2 services only (collector + Redis)
- **DOCUMENTATION**: Complete reorganization into logical categories
- **PROJECT STRUCTURE**: Professional layout with clean root directory
- **LINKS**: Standardized all GitHub URLs to official repository
- **API ENDPOINTS**: Corrected all endpoint references (removed incorrect v1 versioning)
- Unified Docker Compose configuration into single file
- Optimized cache implementation for better performance
- Enhanced error handling and validation
- Improved SSH connection pooling
- Professional onboarding experience for new contributors

#### Removed
- **TCP monitoring functionality** (not implemented in collector)
- **Unnecessary markdown files** from project root (moved to docs/)
- PostgreSQL dependency (simplified to Redis-only caching)
- Nginx proxy (simplified deployment)
- Prometheus/Grafana integration (Zabbix handles monitoring)
- Unnecessary debug tools and development containers
- Inconsistent URL variations throughout documentation

#### Fixed
- Zabbix template cleaned of all TCP references
- Documentation consistency issues across all files
- Broken internal links and navigation paths
- Incorrect API endpoint references throughout documentation
- GitHub repository URL standardization
- Relative path corrections in markdown files
- Professional project structure implementation
- Docker image optimization
- Memory usage optimization

#### Security
- Enhanced SSH connection security
- Improved credential handling
- Added security guidelines and best practices
- Updated dependency versions

### Technical Details
- **Memory Usage**: Reduced from ~2GB to ~600MB
- **Startup Time**: Improved from ~60s to ~10s
- **Services**: Reduced from 8+ to 2 essential services
- **Documentation**: 100% updated and consistent

## [2.0.0] - 2025-06-20

### 🔧 Major Traceroute Fix & Performance Improvements

#### Added
- Redis cache implementation for improved performance
- Enhanced SSH connection pooling
- Comprehensive health monitoring endpoints
- Web dashboard for real-time monitoring
- Performance metrics and statistics

#### Changed
- **BREAKING**: Complete traceroute parser rewrite
- Improved MikroTik command execution with proper count parameter
- Enhanced error handling and timeout management
- Optimized cache TTL and eviction policies

#### Fixed
- **Critical**: Traceroute infinite loop issue resolved
- SSH connection timeout handling
- Memory leak in connection pooling
- Parser accuracy for MikroTik RouterOS output format

#### Technical Improvements
- Command format: `/tool traceroute count=3 8.8.8.8` (was infinite loop)
- Parser handles MikroTik-specific output format correctly
- Eliminates duplicate hop entries in results
- Proper timeout configuration (30s default)

## [1.0.0] - 2025-06-15

### 🎉 Initial Release

#### Added
- Core TriplePlay-Sentinel collector application
- Basic ping test functionality via SSH to MikroTik devices
- Initial traceroute implementation
- Flask-based REST API
- Zabbix HTTP Agent integration
- Docker containerization
- Basic documentation and setup guides

#### Features
- ICMP ping tests with latency, jitter, and packet loss metrics
- Traceroute analysis (initial implementation)
- SSH connection management
- Basic caching mechanism
- Health check endpoints
- Configuration via environment variables

#### Supported Platforms
- MikroTik RouterOS 6.0+
- Zabbix Server 6.0+
- Python 3.9+
- Docker deployment

---

## Release Process

### Version Planning

#### v2.2.0 (Planned - Q3 2025)
- **Enhanced Monitoring**: Additional network quality metrics
- **Multi-threading**: Parallel test execution
- **API v2**: RESTful API with OpenAPI specification
- **Kubernetes**: Helm charts for K8s deployment

#### v2.3.0 (Planned - Q4 2025)
- **High Availability**: Multi-instance deployment support
- **Advanced Caching**: Distributed cache with clustering
- **Monitoring Extensions**: Custom metric plugins
- **Enterprise Features**: RBAC and audit logging

### Compatibility Matrix

| Version | Zabbix | MikroTik RouterOS | Python | Status |
|---------|--------|-------------------|--------|--------|
| 2.1.0   | 6.0+   | 6.40+            | 3.9+   | ✅ Current |
| 2.0.0   | 6.0+   | 6.40+            | 3.9+   | 🔄 Supported |
| 1.0.0   | 6.0+   | 6.0+             | 3.8+   | ❌ EOL |

### Migration Guides

#### Upgrading from v2.0.0 to v2.1.0

**⚠️ Breaking Changes:**
- TCP monitoring items removed from Zabbix template
- Docker Compose file structure simplified
- Some environment variables renamed

**Migration Steps:**

1. **Backup Current Setup**
   ```bash
   # Backup configuration
   cp .env .env.backup
   cp docker-compose.yml docker-compose.yml.backup
   
   # Export Zabbix configuration
   # Configuration → Templates → Export
   ```

2. **Update Configuration**
   ```bash
   # Update environment file
   # Compare .env with new .env.example
   # Remove obsolete TCP-related variables
   
   # Update Docker Compose
   cp docker-compose.yml.new docker-compose.yml
   ```

3. **Update Zabbix Template**
   ```bash
   # Import new template version 2.1.0
   # Configuration → Templates → Import
   # Select: Update existing + Add missing
   ```

4. **Clean Legacy Items**
   ```bash
   # Remove TCP-related items manually if they persist
   # Configuration → Hosts → [Your Host] → Items
   # Filter: "tcp" and delete orphaned items
   ```

5. **Restart Services**
   ```bash
   docker-compose down
   docker-compose up --build -d
   ```

6. **Verify Upgrade**
   ```bash
   # Test health check
   curl http://localhost:5000/api/health
   
   # Check Zabbix items are collecting
   # Monitoring → Latest data
   ```

#### Upgrading from v1.0.0 to v2.1.0

**⚠️ Major Breaking Changes:**
- Complete architecture redesign
- New caching system (Redis required)
- API response format changes
- New Zabbix template required

**Migration Steps:**

1. **Fresh Installation Recommended**
   ```bash
   # Clean installation is recommended for v1.0.0 → v2.1.0
   # Export any custom configurations first
   ```

2. **Data Migration**
   ```bash
   # Export Zabbix historical data if needed
   # No automatic migration path available
   ```

3. **Configuration Update**
   ```bash
   # Create new configuration based on v2.1.0 template
   # Manual reconfiguration of all settings required
   ```

### Deprecation Policy

#### Current Deprecations
- **Python 3.8**: Support ends with v2.1.0 (use Python 3.9+)
- **Legacy API formats**: Will be removed in v3.0.0
- **Environment variable format**: Old format deprecated in v2.2.0

#### Future Deprecations (v3.0.0)
- **Zabbix 5.x**: Support will end
- **MikroTik RouterOS 6.x**: Minimum version will be 7.0
- **Legacy Docker images**: Alpine-based images only

### Security Updates

#### CVE Tracking
- All dependencies are monitored for security vulnerabilities
- Security patches are released as patch versions
- Critical security issues receive immediate hotfix releases

#### Security Release Process
1. **Vulnerability Assessment**: 24-48 hours
2. **Patch Development**: 1-3 business days
3. **Testing**: 1-2 business days
4. **Release**: Same day as testing completion
5. **Notification**: Security advisory published

---

## Community & Support

### Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for details on our development process and how to submit pull requests.

### Reporting Issues
- **Bugs**: Use GitHub Issues with bug template
- **Security Issues**: Email security@tripleplay-sentinel.com
- **Feature Requests**: Use GitHub Issues with feature template

### Release Notes Distribution
- **GitHub Releases**: Detailed technical notes
- **Documentation Site**: User-friendly summaries  
- **Docker Hub**: Container-specific updates
- **Zabbix Share**: Template updates and compatibility notes

---

For older releases and detailed technical changes, see our [GitHub Releases](https://github.com/username/TriplePlay-Sentinel/releases) page.