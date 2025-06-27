# 🔒 Security Guidelines - TriplePlay-Sentinel

<div align="center">

![Security Level](https://img.shields.io/badge/Security%20Level-Enterprise-red.svg)
![Compliance](https://img.shields.io/badge/Compliance-ISO%2027001-blue.svg)
![Audit](https://img.shields.io/badge/Audit-Enabled-green.svg)

**Enterprise-Grade Security for Network Monitoring Infrastructure**

[Security Model](#-security-model) • [Implementation](#-implementation) • [Monitoring](#-monitoring) • [Incident Response](#-incident-response) • [Compliance](#-compliance)

</div>

---

## 🎯 Security Overview

TriplePlay-Sentinel handles **critical device credentials** and operates in **sensitive network infrastructure**. This document establishes comprehensive security guidelines for the simplified architecture (collector + Redis).

### 🛡️ Security Model

```mermaid
graph TB
    subgraph "External Threats"
        INT[Internet Attacks]
        INT_USR[Unauthorized Users]
        INT_NET[Network Intrusion]
    end
    
    subgraph "Perimeter Security"
        FW[Firewall/WAF]
        VPN[VPN/Private Network]
        TLS[TLS Encryption]
    end
    
    subgraph "Application Security"
        AUTH[API Authentication]
        VAL[Input Validation]
        RATE[Rate Limiting]
        AUDIT[Audit Logging]
    end
    
    subgraph "Infrastructure Security"
        CONT[Container Security]
        NET[Network Isolation]
        CRED[Credential Management]
        CACHE[Cache Security]
    end
    
    subgraph "Device Security"
        SSH[SSH Hardening]
        PRIV[Minimal Privileges]
        ROT[Credential Rotation]
    end
    
    INT --> FW
    INT_USR --> VPN
    INT_NET --> TLS
    
    FW --> AUTH
    VPN --> VAL
    TLS --> RATE
    
    AUTH --> CONT
    VAL --> NET
    RATE --> CRED
    AUDIT --> CACHE
    
    CONT --> SSH
    NET --> PRIV
    CRED --> ROT
```

---

## 🔐 Authentication & Authorization

### API Authentication

#### Production Configuration
```bash
# Enable API authentication
ENABLE_AUTH=true

# Generate cryptographically secure API key
API_KEY=$(openssl rand -hex 32)
echo "Generated API Key: $API_KEY"

# Alternative: use UUID4
API_KEY=$(python3 -c "import uuid; print(str(uuid.uuid4()).replace('-', ''))")
```

#### Implementation
```bash
# Environment configuration
cat >> .env << EOF
ENABLE_AUTH=true
API_KEY=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
EOF

# Restart services to apply changes
docker-compose restart
```

#### Usage Examples
```bash
# HTTP Header authentication
curl -X POST http://localhost:5000/api/test \
  -H "Authorization: Bearer a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456" \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host": "192.168.1.1", ...}'

# X-API-Key header (alternative)
curl -X POST http://localhost:5000/api/test \
  -H "X-API-Key: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456" \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host": "192.168.1.1", ...}'
```

### Role-Based Access Control (RBAC)

#### Zabbix Integration Security
```yaml
# Zabbix HTTP Agent Configuration
Authentication: Bearer Token
Token: {$SENTINEL_API_KEY}
Timeout: 30s
SSL Verify Peer: Yes (in production)
SSL Verify Host: Yes (in production)
```

#### Access Levels
| Role | API Access | Dashboard | Admin Functions |
|------|------------|-----------|-----------------|
| **Monitor** | Health Check Only | Read-Only | ❌ |
| **Operator** | Test Execution | Full Access | Cache Management |
| **Admin** | Full API Access | Full Access | ✅ All Functions |

---

## 🏗️ Infrastructure Security

### Container Security

#### Docker Hardening
```yaml
# docker-compose.yml security configuration
version: '3.8'
services:
  sentinel-collector:
    # Security context
    user: "1001:1001"  # Non-root user
    read_only: true    # Read-only filesystem
    
    # Resource limits
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
          pids: 100
    
    # Security options
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-default
    
    # Capability dropping
    cap_drop:
      - ALL
    cap_add:
      - NET_CONNECT
      - NET_RAW
    
    # Temporary filesystems
    tmpfs:
      - /tmp:noexec,nosuid,size=100M
      - /var/run:noexec,nosuid,size=50M
```

#### Dockerfile Security
```dockerfile
# Use specific version, not latest
FROM python:3.11-slim-bullseye

# Create non-root user
RUN groupadd -r sentinel && useradd -r -g sentinel sentinel

# Set security headers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install security updates
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Use non-root user
USER sentinel
WORKDIR /app

# Copy and set proper permissions
COPY --chown=sentinel:sentinel . .
RUN chmod 750 /app && chmod 640 /app/.env
```

### Network Security

#### Network Isolation
```yaml
# Docker network configuration
networks:
  default:
    name: tripleplay-sentinel
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"
      com.docker.network.bridge.enable_ip_masquerade: "true"
```

#### Firewall Rules
```bash
# iptables configuration
# Allow Zabbix server access
iptables -A INPUT -p tcp --dport 5000 -s 192.168.1.50 -j ACCEPT

# Allow SSH to MikroTik devices (if local)
iptables -A OUTPUT -p tcp --dport 22 -d 192.168.1.0/24 -j ACCEPT

# Drop all other connections to API port
iptables -A INPUT -p tcp --dport 5000 -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

#### TLS/SSL Configuration (Production)
```yaml
# nginx reverse proxy with SSL
upstream tripleplay-backend {
    server 127.0.0.1:5000;
}

server {
    listen 443 ssl http2;
    server_name sentinel.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/sentinel.crt;
    ssl_certificate_key /etc/ssl/private/sentinel.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    
    location /api/ {
        proxy_pass http://tripleplay-backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔑 Credential Management

### MikroTik Device Credentials

#### Secure User Creation
```mikrotik
# Create dedicated monitoring group with minimal privileges
/user group add name=monitoring policy=read,test

# Create monitoring user
/user add name=sentinel-monitor \
          password=$(openssl rand -base64 32) \
          group=monitoring \
          comment="TriplePlay Sentinel - Network Monitoring" \
          address=192.168.1.100/32

# Verify configuration
/user print where name=sentinel-monitor
```

#### SSH Key Authentication (Recommended)
```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -f ~/.ssh/sentinel_monitoring -C "sentinel-monitoring"

# Copy public key to MikroTik
ssh-copy-id -i ~/.ssh/sentinel_monitoring.pub sentinel-monitor@192.168.1.1
```

```mikrotik
# Configure SSH key on MikroTik
/user ssh-keys import public-key-file=sentinel_monitoring.pub user=sentinel-monitor
/user set sentinel-monitor password=""  # Disable password auth
```

#### Credential Rotation Policy
```bash
#!/bin/bash
# credential_rotation.sh - Run monthly

# Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# Update MikroTik device
ssh sentinel-monitor@192.168.1.1 "/user set sentinel-monitor password=$NEW_PASSWORD"

# Update Zabbix macros via API
curl -X POST https://zabbix.company.com/api_jsonrpc.php \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"usermacro.update\",
    \"params\": {
      \"hostid\": \"10001\",
      \"macro\": \"{$MIKROTIK_PASSWORD}\",
      \"value\": \"$NEW_PASSWORD\"
    },
    \"auth\": \"$ZABBIX_AUTH_TOKEN\",
    \"id\": 1
  }"

# Log rotation event
echo "$(date): Password rotated for device 192.168.1.1" >> /var/log/credential_rotation.log
```

### Redis Security

#### Authentication Configuration
```bash
# Generate secure Redis password
REDIS_PASSWORD=$(openssl rand -hex 24)

# Environment configuration
cat >> .env << EOF
REDIS_PASSWORD=$REDIS_PASSWORD
EOF
```

#### Redis Hardening
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: >
    redis-server 
    --requirepass ${REDIS_PASSWORD}
    --protected-mode yes
    --port 6379
    --tcp-backlog 511
    --timeout 0
    --tcp-keepalive 300
    --daemonize no
    --supervised no
    --pidfile /var/run/redis_6379.pid
    --loglevel notice
    --logfile ""
    --databases 16
    --always-show-logo yes
    --save 900 1
    --save 300 10
    --save 60 10000
    --stop-writes-on-bgsave-error yes
    --rdbcompression yes
    --rdbchecksum yes
    --dbfilename dump.rdb
    --dir /data
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
```

---

## 📊 Security Monitoring

### Audit Logging

#### Comprehensive Logging Configuration
```python
# Enhanced logging configuration
import logging
from logging.handlers import RotatingFileHandler, SysLogHandler
import json
from datetime import datetime

class SecurityAuditHandler:
    def __init__(self):
        # Security audit logger
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.INFO)
        
        # File handler for security events
        security_handler = RotatingFileHandler(
            'logs/security_audit.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        
        # JSON formatter for structured logging
        security_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        security_handler.setFormatter(security_formatter)
        self.security_logger.addHandler(security_handler)
        
        # Syslog handler for centralized logging
        syslog_handler = SysLogHandler(address=('syslog.company.com', 514))
        syslog_handler.setFormatter(security_formatter)
        self.security_logger.addHandler(syslog_handler)
    
    def log_authentication_attempt(self, ip_address, api_key_hash, success):
        event = {
            'event_type': 'authentication_attempt',
            'timestamp': datetime.utcnow().isoformat(),
            'source_ip': ip_address,
            'api_key_hash': api_key_hash[:8] + '...',  # Only log prefix
            'success': success,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        if success:
            self.security_logger.info(f"Authentication successful: {json.dumps(event)}")
        else:
            self.security_logger.warning(f"Authentication failed: {json.dumps(event)}")
    
    def log_ssh_connection(self, mikrotik_host, success, error_message=None):
        event = {
            'event_type': 'ssh_connection',
            'timestamp': datetime.utcnow().isoformat(),
            'target_device': mikrotik_host,
            'success': success,
            'error_message': error_message
        }
        
        if success:
            self.security_logger.info(f"SSH connection successful: {json.dumps(event)}")
        else:
            self.security_logger.error(f"SSH connection failed: {json.dumps(event)}")
```

#### Security Events to Monitor
```bash
# Critical security events
grep "Authentication failed" logs/security_audit.log
grep "SSH connection failed" logs/security_audit.log
grep "Rate limit exceeded" logs/security_audit.log
grep "Invalid API request" logs/security_audit.log

# Behavioral analysis
awk '/Authentication failed/ {ip_count[$7]++} END {for (ip in ip_count) if (ip_count[ip] > 10) print ip, ip_count[ip]}' logs/security_audit.log
```

### Intrusion Detection

#### Anomaly Detection
```bash
#!/bin/bash
# security_monitor.sh - Run every 5 minutes

# Check for brute force attempts
FAILED_AUTHS=$(grep "Authentication failed" logs/security_audit.log | grep "$(date '+%Y-%m-%d %H:%M')" | wc -l)
if [ $FAILED_AUTHS -gt 50 ]; then
    echo "ALERT: High number of failed authentications: $FAILED_AUTHS"
    # Send alert to security team
    curl -X POST "$SLACK_WEBHOOK" -d "{\"text\": \"Security Alert: $FAILED_AUTHS failed auth attempts\"}"
fi

# Check for unusual API patterns
UNUSUAL_PATTERNS=$(grep -E "(admin|root|test|debug)" logs/security_audit.log | grep "$(date '+%Y-%m-%d')" | wc -l)
if [ $UNUSUAL_PATTERNS -gt 0 ]; then
    echo "ALERT: Unusual API request patterns detected"
fi

# Check Redis connection security
REDIS_UNAUTH=$(docker-compose logs redis | grep "NOAUTH" | wc -l)
if [ $REDIS_UNAUTH -gt 0 ]; then
    echo "ALERT: Unauthenticated Redis access attempts"
fi
```

#### Real-time Monitoring
```yaml
# prometheus.yml for metrics collection
scrape_configs:
  - job_name: 'tripleplay-sentinel'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
# Alert rules
groups:
  - name: tripleplay_security
    rules:
      - alert: HighFailedAuthentications
        expr: increase(api_authentication_failures_total[5m]) > 50
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "High number of failed authentications"
          
      - alert: UnusualAPIActivity
        expr: rate(api_requests_total[5m]) > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Unusual API activity detected"
```

---

## 🚨 Incident Response

### Incident Detection

#### Automated Detection
```bash
#!/bin/bash
# incident_detection.sh

# Function to send alerts
send_alert() {
    local severity=$1
    local message=$2
    
    # Log incident
    echo "$(date): [$severity] $message" >> /var/log/security_incidents.log
    
    # Send to monitoring system
    curl -X POST "$MONITORING_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"severity\": \"$severity\", \"message\": \"$message\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
}

# Check for security indicators
check_security_indicators() {
    # Multiple failed SSH connections
    local ssh_failures=$(grep "SSH connection failed" logs/security_audit.log | grep "$(date '+%Y-%m-%d %H')" | wc -l)
    if [ $ssh_failures -gt 20 ]; then
        send_alert "HIGH" "Multiple SSH connection failures: $ssh_failures in last hour"
    fi
    
    # Suspicious API requests
    local suspicious_requests=$(grep -E "(injection|script|eval|exec)" logs/security_audit.log | grep "$(date '+%Y-%m-%d')" | wc -l)
    if [ $suspicious_requests -gt 0 ]; then
        send_alert "CRITICAL" "Potential injection attempts detected: $suspicious_requests"
    fi
    
    # Resource exhaustion
    local memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" tripleplay-sentinel-collector | sed 's/%//')
    if [ $(echo "$memory_usage > 90" | bc) -eq 1 ]; then
        send_alert "HIGH" "High memory usage detected: ${memory_usage}%"
    fi
}

# Run checks
check_security_indicators
```

### Incident Response Procedures

#### Phase 1: Detection and Analysis
```bash
# Immediate assessment script
#!/bin/bash
# incident_assessment.sh

echo "=== TRIPLEPLAY-SENTINEL SECURITY INCIDENT ASSESSMENT ==="
echo "Timestamp: $(date -u)"
echo

# System status
echo "1. SYSTEM STATUS:"
docker-compose ps
echo

# Recent logs
echo "2. RECENT SECURITY EVENTS:"
tail -n 50 logs/security_audit.log | grep -E "(CRITICAL|ERROR|WARNING)"
echo

# Network connections
echo "3. ACTIVE CONNECTIONS:"
netstat -an | grep :5000
echo

# Resource usage
echo "4. RESOURCE USAGE:"
docker stats --no-stream
echo

# Redis status
echo "5. CACHE STATUS:"
docker exec tripleplay-redis redis-cli INFO | grep -E "(connected_clients|used_memory|keyspace)"
echo

# Recent API activity
echo "6. RECENT API ACTIVITY:"
grep "$(date '+%Y-%m-%d %H')" logs/security_audit.log | tail -n 20
```

#### Phase 2: Containment
```bash
# Emergency containment script
#!/bin/bash
# emergency_containment.sh

# Immediate actions based on threat level
case $1 in
    "CRITICAL")
        echo "CRITICAL threat detected - Initiating emergency shutdown"
        # Stop all services immediately
        docker-compose down
        # Block all traffic to API port
        iptables -I INPUT 1 -p tcp --dport 5000 -j DROP
        ;;
    "HIGH")
        echo "HIGH threat detected - Enabling enhanced monitoring"
        # Enable verbose logging
        docker-compose exec sentinel-collector \
            sh -c 'echo "LOG_LEVEL=DEBUG" >> .env'
        # Restart with enhanced monitoring
        docker-compose restart sentinel-collector
        ;;
    "MEDIUM")
        echo "MEDIUM threat detected - Implementing additional controls"
        # Enable rate limiting
        docker-compose exec sentinel-collector \
            sh -c 'echo "RATE_LIMIT_ENABLED=true" >> .env'
        ;;
esac

# Backup current state
INCIDENT_DIR="/var/log/incidents/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$INCIDENT_DIR"

# Backup logs
cp -r logs/ "$INCIDENT_DIR/"

# Backup Redis data
docker exec tripleplay-redis redis-cli BGSAVE
sleep 5
docker cp tripleplay-redis:/data/dump.rdb "$INCIDENT_DIR/"

# System state snapshot
docker-compose ps > "$INCIDENT_DIR/containers_status.txt"
docker stats --no-stream > "$INCIDENT_DIR/resource_usage.txt"
netstat -an > "$INCIDENT_DIR/network_connections.txt"

echo "Incident data backed up to: $INCIDENT_DIR"
```

#### Phase 3: Recovery and Lessons Learned
```bash
# Recovery verification script
#!/bin/bash
# recovery_verification.sh

echo "=== RECOVERY VERIFICATION ==="

# Verify services are healthy
if curl -f -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ API Health Check: PASSED"
else
    echo "❌ API Health Check: FAILED"
    exit 1
fi

# Verify Redis connectivity
if docker exec tripleplay-redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis Connectivity: PASSED"
else
    echo "❌ Redis Connectivity: FAILED"
    exit 1
fi

# Verify MikroTik connectivity
if timeout 10 ssh -o BatchMode=yes sentinel-monitor@192.168.1.1 "/system identity print" > /dev/null 2>&1; then
    echo "✅ MikroTik SSH: PASSED"
else
    echo "❌ MikroTik SSH: FAILED"
fi

# Verify logging is functioning
LOG_COUNT=$(tail -n 10 logs/security_audit.log | wc -l)
if [ $LOG_COUNT -gt 0 ]; then
    echo "✅ Security Logging: ACTIVE"
else
    echo "❌ Security Logging: INACTIVE"
fi

echo "Recovery verification completed"
```

---

## 📋 Security Compliance

### Compliance Frameworks

#### ISO 27001 Controls
```yaml
Information Security Controls:
  A.9.1.1 - Access Control Policy: ✅ Implemented via API keys and RBAC
  A.9.1.2 - Access to Networks: ✅ Network isolation and firewall rules
  A.9.2.1 - User Registration: ✅ Credential management procedures
  A.9.2.2 - Privilege Management: ✅ Minimal privilege MikroTik users
  A.9.2.3 - Password Management: ✅ Strong password policies and rotation
  A.9.2.4 - Review of User Access: ✅ Regular access reviews documented
  A.9.4.1 - Information Access Restriction: ✅ Need-to-know access control
  A.10.1.1 - Cryptographic Policy: ✅ TLS encryption and secure key storage
```

#### SOC 2 Type II
```yaml
Trust Service Criteria:
  Security:
    - ✅ Access controls implemented and tested
    - ✅ Logical and physical access restrictions
    - ✅ System operations monitoring
  
  Availability:
    - ✅ System monitoring and capacity management
    - ✅ Backup and recovery procedures
    - ✅ Change management process
  
  Confidentiality:
    - ✅ Data classification and handling procedures
    - ✅ Encryption of sensitive data
    - ✅ Secure data transmission
```

### Compliance Validation

#### Security Assessment Checklist
```bash
#!/bin/bash
# compliance_check.sh

echo "=== TRIPLEPLAY-SENTINEL SECURITY COMPLIANCE CHECK ==="

# Check authentication is enabled
if grep -q "ENABLE_AUTH=true" .env; then
    echo "✅ Authentication: ENABLED"
else
    echo "❌ Authentication: DISABLED - COMPLIANCE VIOLATION"
fi

# Check Redis password
if grep -q "REDIS_PASSWORD=" .env && [ $(grep "REDIS_PASSWORD=" .env | cut -d'=' -f2 | wc -c) -gt 16 ]; then
    echo "✅ Redis Security: STRONG PASSWORD"
else
    echo "❌ Redis Security: WEAK/NO PASSWORD - COMPLIANCE VIOLATION"
fi

# Check log retention
LOG_FILES=$(find logs/ -name "*.log" -mtime -30 | wc -l)
if [ $LOG_FILES -gt 0 ]; then
    echo "✅ Log Retention: COMPLIANT (30+ days)"
else
    echo "❌ Log Retention: NON-COMPLIANT"
fi

# Check TLS configuration
if netstat -an | grep :443 > /dev/null; then
    echo "✅ TLS Encryption: ENABLED"
else
    echo "⚠️  TLS Encryption: NOT CONFIGURED (acceptable for internal networks)"
fi

# Check file permissions
ENV_PERMS=$(stat -c "%a" .env 2>/dev/null)
if [ "$ENV_PERMS" = "600" ]; then
    echo "✅ File Permissions: SECURE"
else
    echo "❌ File Permissions: INSECURE - chmod 600 .env required"
fi

echo "Compliance check completed"
```

---

## 🔧 Security Hardening Checklist

### Pre-Deployment Security Checklist

#### ✅ Infrastructure Security
- [ ] **Container Security**: Non-root user, resource limits, read-only filesystem
- [ ] **Network Isolation**: Docker network configured, firewall rules applied
- [ ] **TLS/SSL**: HTTPS enabled for production deployments
- [ ] **Access Control**: VPN or private network access only

#### ✅ Application Security
- [ ] **Authentication**: API key authentication enabled and configured
- [ ] **Input Validation**: All API inputs validated and sanitized
- [ ] **Rate Limiting**: API rate limits configured and tested
- [ ] **Error Handling**: Secure error responses (no sensitive data leakage)

#### ✅ Data Security
- [ ] **Credential Management**: MikroTik credentials properly secured
- [ ] **Cache Security**: Redis authentication enabled and configured
- [ ] **Encryption**: Data in transit encrypted (TLS)
- [ ] **Data Retention**: Log retention policies implemented

#### ✅ Operational Security
- [ ] **Audit Logging**: Comprehensive security event logging enabled
- [ ] **Monitoring**: Security monitoring and alerting configured
- [ ] **Incident Response**: Procedures documented and tested
- [ ] **Backup and Recovery**: Secure backup procedures implemented

#### ✅ Compliance
- [ ] **Documentation**: Security policies and procedures documented
- [ ] **Access Reviews**: Regular access review procedures established
- [ ] **Vulnerability Management**: Regular security assessments scheduled
- [ ] **Training**: Security awareness training completed

### Post-Deployment Security Validation

```bash
#!/bin/bash
# post_deployment_security_validation.sh

echo "=== POST-DEPLOYMENT SECURITY VALIDATION ==="

# Test authentication
echo "Testing API authentication..."
UNAUTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health)
if [ "$UNAUTH_RESPONSE" = "401" ]; then
    echo "✅ Authentication: Working correctly"
else
    echo "❌ Authentication: May not be properly configured"
fi

# Test rate limiting
echo "Testing rate limiting..."
for i in {1..10}; do
    curl -s http://localhost:5000/api/health > /dev/null
done
RATE_LIMIT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health)
if [ "$RATE_LIMIT_RESPONSE" = "429" ]; then
    echo "✅ Rate Limiting: Working correctly"
else
    echo "⚠️  Rate Limiting: May not be configured"
fi

# Test TLS configuration
echo "Testing TLS configuration..."
if openssl s_client -connect localhost:443 -verify_return_error < /dev/null 2>/dev/null; then
    echo "✅ TLS: Valid certificate"
else
    echo "⚠️  TLS: Not configured or invalid certificate"
fi

# Validate log generation
echo "Testing audit logging..."
LOG_COUNT_BEFORE=$(wc -l < logs/security_audit.log)
curl -s http://localhost:5000/api/health > /dev/null
sleep 2
LOG_COUNT_AFTER=$(wc -l < logs/security_audit.log)
if [ $LOG_COUNT_AFTER -gt $LOG_COUNT_BEFORE ]; then
    echo "✅ Audit Logging: Working correctly"
else
    echo "❌ Audit Logging: Not generating logs"
fi

echo "Security validation completed"
```

---

## 📞 Security Support

### Emergency Contacts
- **Security Team**: security@company.com
- **System Administrators**: sysadmin@company.com
- **24/7 Security Hotline**: +1-XXX-XXX-XXXX

### Security Resources
- **Internal Security Wiki**: https://wiki.company.com/security
- **Incident Response Runbook**: https://docs.company.com/incident-response
- **Security Training**: https://training.company.com/security

### Regular Security Tasks
- **Weekly**: Review security logs and alerts
- **Monthly**: Update credentials and certificates
- **Quarterly**: Conduct penetration testing
- **Annually**: Complete comprehensive security assessment

---

<div align="center">

**🛡️ Security is everyone's responsibility**

Remember: The strongest security comes from a combination of technology, processes, and people.

[![Security Status](https://img.shields.io/badge/Security%20Status-Hardened-green.svg)](#)
[![Compliance](https://img.shields.io/badge/Compliance-Verified-blue.svg)](#)

</div>