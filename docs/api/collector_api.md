# 🔌 TriplePlay-Sentinel Collector API Reference

<div align="center">

![API Version](https://img.shields.io/badge/API%20Version-v1.0-blue.svg)
![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)

**RESTful API for Network Monitoring via MikroTik Devices**

[Quick Start](#-quick-start) • [Authentication](#-authentication) • [Endpoints](#-endpoints) • [Zabbix Integration](#-zabbix-integration) • [SDKs](#-sdks)

</div>

---

## 📋 Overview

The TriplePlay-Sentinel Collector API provides HTTP endpoints for executing network connectivity tests on MikroTik devices. Designed specifically for **Zabbix HTTP Agent integration** and monitoring systems.

### 🏗️ Architecture Pattern

```
┌─────────────────┐    HTTP Agent    ┌──────────────────┐    SSH/API    ┌─────────────────┐
│   Zabbix Server │ ◄──────────────► │ Collector API    │ ◄────────────► │ MikroTik Device │
│                 │   REST Calls     │                  │   RouterOS     │                 │
└─────────────────┘                  └──────────────────┘                └─────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │ Redis Cache      │
                                     └──────────────────┘
```

### ✨ Key Features

- **🎯 Purpose-Built**: Optimized for Zabbix HTTP Agent (PULL architecture)
- **⚡ High Performance**: Redis-powered intelligent caching
- **🔒 Secure**: API key authentication and input validation
- **📊 Observable**: Comprehensive metrics and health endpoints
- **🔄 Reliable**: Automatic retries and connection pooling
- **📝 Well-Documented**: OpenAPI specification included

---

## 🚀 Quick Start

### Base URL
```
http://your-collector-host:5000/api
```

### Simple Health Check
```bash
curl http://localhost:5000/api/health
```

### Basic Test Request
```bash
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "admin",
    "mikrotik_password": "password",
    "target": "8.8.8.8",
    "test_type": "ping"
  }'
```

---

## 🔐 Authentication

### API Key Authentication (Production)
```http
Authorization: Bearer YOUR_API_KEY
```

### Configuration
```bash
# Enable authentication
ENABLE_AUTH=true
API_KEY=your-secure-api-key-here

# Generate secure API key
openssl rand -hex 32
```

### Usage Example
```bash
curl -X POST http://localhost:5000/api/test \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host": "192.168.1.1", ...}'
```

---

## 📍 Endpoints

### 🏥 Health & Status

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "timestamp": "2025-06-23T10:30:00Z",
  "uptime_seconds": 86400,
  "components": {
    "redis": "connected",
    "ssh_pool": "active"
  },
  "cache": {
    "status": "active",
    "entries": 145,
    "hit_rate_percent": 78.5,
    "memory_usage_mb": 45.2
  },
  "performance": {
    "requests_per_minute": 120,
    "average_response_time_ms": 245,
    "active_connections": 8
  }
}
```

#### System Statistics
```http
GET /api/stats
```

**Response:**
```json
{
  "uptime_seconds": 86400,
  "total_requests": 145230,
  "successful_requests": 142180,
  "failed_requests": 3050,
  "cache": {
    "total_entries": 145,
    "hit_count": 98765,
    "miss_count": 25432,
    "hit_rate_percent": 79.5,
    "evictions": 234
  },
  "connections": {
    "active_mikrotik_connections": 8,
    "pool_size": 20,
    "failed_connections_24h": 12,
    "average_connection_time_ms": 156
  },
  "tests": {
    "ping_tests_24h": 8540,
    "traceroute_tests_24h": 1240,
    "failed_tests_24h": 89,
    "average_test_duration_ms": 2340
  }
}
```

### 🧪 Network Tests

#### Ping Test
Execute ICMP ping test through MikroTik device.

```http
POST /api/test
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "mikrotik_host": "192.168.1.1",
  "mikrotik_user": "admin",
  "mikrotik_password": "password",
  "mikrotik_port": 22,
  "target": "8.8.8.8",
  "test_type": "ping",
  "count": 4,
  "size": 64,
  "interval": 1
}
```

**Response:**
```json
{
  "status": "success",
  "test_type": "ping",
  "timestamp": "2025-06-23T10:30:00Z",
  "execution_time_seconds": 4.15,
  "cache_hit": false,
  "cache_ttl": 30,
  "mikrotik_host": "192.168.1.1",
  "target": "8.8.8.8",
  "results": {
    "ping_stats": {
      "packets_sent": 4,
      "packets_received": 4,
      "packet_loss_percent": 0.0,
      "rtt_min_ms": 8.1,
      "rtt_avg_ms": 9.2,
      "rtt_max_ms": 10.5,
      "rtt_stddev_ms": 1.1,
      "jitter_ms": 1.2
    },
    "availability_percent": 100.0,
    "quality_score": 95.8
  },
  "metadata": {
    "mikrotik_version": "7.1.5",
    "test_duration_ms": 4150,
    "cache_key": "ping_192.168.1.1_8.8.8.8_4_64",
    "request_id": "req_1234567890"
  }
}
```

#### Traceroute Test
Execute traceroute analysis through MikroTik device.

```http
POST /api/test
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "mikrotik_host": "192.168.1.1",
  "mikrotik_user": "admin",
  "mikrotik_password": "password",
  "target": "8.8.8.8",
  "test_type": "traceroute",
  "count": 3,
  "max_hops": 15,
  "timeout": 5
}
```

**Response:**
```json
{
  "status": "success",
  "test_type": "traceroute",
  "timestamp": "2025-06-23T10:30:00Z",
  "execution_time_seconds": 7.43,
  "cache_hit": false,
  "mikrotik_host": "192.168.1.1",
  "target": "8.8.8.8",
  "results": {
    "traceroute_stats": {
      "hop_count": 10,
      "reached_target": true,
      "total_time_ms": 7430,
      "status": "completed"
    },
    "hops": [
      {
        "hop": 1,
        "address": "192.168.1.1",
        "hostname": "gateway.local",
        "loss_percent": 0.0,
        "sent_count": 3,
        "last_time_ms": 1.2,
        "avg_time_ms": 1.1,
        "best_time_ms": 1.0,
        "worst_time_ms": 1.3,
        "status": "responded"
      },
      {
        "hop": 2,
        "address": "10.0.0.1",
        "hostname": "isp-router.com",
        "loss_percent": 0.0,
        "sent_count": 3,
        "last_time_ms": 15.4,
        "avg_time_ms": 14.8,
        "best_time_ms": 14.2,
        "worst_time_ms": 15.4,
        "status": "responded"
      }
    ]
  },
  "metadata": {
    "request_id": "req_1234567891",
    "cache_key": "traceroute_192.168.1.1_8.8.8.8_3"
  }
}
```

#### Connection Test
Test SSH connectivity to MikroTik device.

```http
POST /api/connection-test
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "mikrotik_host": "192.168.1.1",
  "mikrotik_user": "admin",
  "mikrotik_password": "password",
  "mikrotik_port": 22,
  "timeout": 10
}
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2025-06-23T10:30:00Z",
  "connection_test": {
    "ssh_connection_successful": true,
    "connection_time_ms": 156,
    "authentication_successful": true,
    "device_info": {
      "identity": "MikroTik-Router",
      "version": "7.1.5 (stable)",
      "architecture": "arm64",
      "uptime": "2w3d4h15m"
    }
  },
  "metadata": {
    "test_duration_ms": 1890,
    "request_id": "req_1234567892"
  }
}
```

### 🗂️ Cache Management

#### Cache Status
```http
GET /api/cache/status
```

#### Clear All Cache
```http
DELETE /api/cache
```

#### Cache Entry Operations
```http
GET /api/cache/{cache_key}
DELETE /api/cache/{cache_key}
```

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "status": "error",
  "error": {
    "code": "MIKROTIK_CONNECTION_FAILED",
    "message": "Failed to establish SSH connection to MikroTik device",
    "category": "connection",
    "retryable": true
  },
  "timestamp": "2025-06-23T10:30:00Z",
  "request_id": "req_1234567893",
  "details": {
    "mikrotik_host": "192.168.1.1",
    "connection_timeout": true,
    "retry_count": 3,
    "last_error": "Connection timed out after 30 seconds"
  }
}
```

### Error Codes Reference

| Code | Category | Description | Retryable |
|------|----------|-------------|-----------|
| `MIKROTIK_CONNECTION_FAILED` | connection | SSH connection failed | ✅ |
| `MIKROTIK_AUTH_FAILED` | authentication | Invalid credentials | ❌ |
| `MIKROTIK_COMMAND_FAILED` | execution | Command execution failed | ✅ |
| `INVALID_REQUEST` | validation | Invalid request parameters | ❌ |
| `CACHE_ERROR` | cache | Cache system error | ✅ |
| `RATE_LIMIT_EXCEEDED` | rate_limit | Rate limit exceeded | ✅ |
| `TIMEOUT_ERROR` | timeout | Request timeout | ✅ |
| `INTERNAL_ERROR` | system | Internal server error | ✅ |

### HTTP Status Codes

- **200 OK**: Successful request
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: Endpoint not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

---

## 🎯 Zabbix Integration

### HTTP Agent Configuration

#### Master Item Setup
```yaml
Name: TriplePlay Ping Test [{$TARGET}]
Type: HTTP agent
URL: {$COLLECTOR_URL}/api/test
Request type: POST
Request body type: JSON
Request body: |
  {
    "mikrotik_host": "{$MIKROTIK_HOST}",
    "mikrotik_user": "{$MIKROTIK_USER}",
    "mikrotik_password": "{$MIKROTIK_PASSWORD}",
    "target": "{$TARGET}",
    "test_type": "ping",
    "count": 4
  }

Headers: |
  Authorization: Bearer {$API_KEY}
  Content-Type: application/json

Update interval: 60s
Timeout: 30s
```

#### Dependent Items (JSONPath Extraction)
```yaml
# Packet Loss Percentage
Name: Ping Packet Loss [{$TARGET}]
Type: Dependent item
Master item: TriplePlay Ping Test [{$TARGET}]
Preprocessing: 
  - JSONPath: $.results.ping_stats.packet_loss_percent
  - Custom multiplier: 1
Value type: Numeric (float)
Units: %

# Average Round Trip Time
Name: Ping RTT Average [{$TARGET}]
Type: Dependent item
Master item: TriplePlay Ping Test [{$TARGET}]
Preprocessing:
  - JSONPath: $.results.ping_stats.rtt_avg_ms
Value type: Numeric (float)
Units: ms

# Jitter
Name: Ping Jitter [{$TARGET}]
Type: Dependent item
Master item: TriplePlay Ping Test [{$TARGET}]
Preprocessing:
  - JSONPath: $.results.ping_stats.jitter_ms
Value type: Numeric (float)
Units: ms

# Network Quality Score
Name: Network Quality Score [{$TARGET}]
Type: Dependent item
Master item: TriplePlay Ping Test [{$TARGET}]
Preprocessing:
  - JSONPath: $.results.quality_score
Value type: Numeric (float)
Units: score

# Cache Hit Indicator
Name: Cache Hit [{$TARGET}]
Type: Dependent item
Master item: TriplePlay Ping Test [{$TARGET}]
Preprocessing:
  - JSONPath: $.cache_hit
  - Boolean to decimal
Value type: Numeric (unsigned)
```

### Macros Configuration
```yaml
# Collector Configuration
{$COLLECTOR_URL} = http://192.168.1.100:5000
{$API_KEY} = your-api-key-here

# MikroTik Device Configuration
{$MIKROTIK_HOST} = 192.168.1.1
{$MIKROTIK_USER} = sentinel-monitor
{$MIKROTIK_PASSWORD} = secure-password

# Test Targets
{$TARGET_DNS1} = 8.8.8.8
{$TARGET_DNS2} = 1.1.1.1
{$TARGET_GATEWAY} = 192.168.1.1
{$TARGET_ISP} = your-isp-gateway

# Thresholds
{$PING_LOSS_WARN} = 10
{$PING_LOSS_HIGH} = 25
{$PING_RTT_WARN} = 100
{$PING_RTT_HIGH} = 200
{$NETWORK_QUALITY_MIN} = 70
```

### Trigger Examples
```yaml
# High Packet Loss
Expression: last(/Template/ping.loss[{$TARGET_DNS1}])>{$PING_LOSS_HIGH}
Severity: High
Description: "High packet loss detected: {ITEM.LASTVALUE}%"

# Moderate Packet Loss
Expression: last(/Template/ping.loss[{$TARGET_DNS1}])>{$PING_LOSS_WARN}
Severity: Warning  
Description: "Moderate packet loss detected: {ITEM.LASTVALUE}%"

# High Latency
Expression: last(/Template/ping.rtt_avg[{$TARGET_DNS1}])>{$PING_RTT_HIGH}
Severity: High
Description: "High latency detected: {ITEM.LASTVALUE}ms"

# Low Network Quality
Expression: last(/Template/network.quality[{$TARGET_DNS1}])<{$NETWORK_QUALITY_MIN}
Severity: Warning
Description: "Network quality degraded: {ITEM.LASTVALUE} score"

# Collector Unhealthy
Expression: last(/Template/collector.health)<>1
Severity: Disaster
Description: "TriplePlay Collector is unhealthy"
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Basic Configuration
COLLECTOR_HOST=0.0.0.0
COLLECTOR_PORT=5000
LOG_LEVEL=INFO

# Authentication
ENABLE_AUTH=true
API_KEY=your-secure-api-key

# Cache Configuration
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PASSWORD=secure-redis-password
CACHE_TTL=30
MAX_CACHE_SIZE=1000

# MikroTik Connection
SSH_TIMEOUT=30
SSH_MAX_RETRIES=3
MAX_WORKERS=10

# Performance
REQUEST_TIMEOUT=60
HEALTH_CHECK_INTERVAL=60
METRICS_ENABLED=true

# Rate Limiting
RATE_LIMIT_PER_IP=100
RATE_LIMIT_PER_API_KEY=1000
RATE_LIMIT_GLOBAL=5000
```

### Rate Limiting
```yaml
Default Limits:
  Per IP: 100 requests/minute
  Per API Key: 1000 requests/minute
  Global: 5000 requests/minute

Headers in Response:
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 995
  X-RateLimit-Reset: 1635724800
```

---

## 📊 Performance & Monitoring

### Performance Metrics
- **Average Response Time**: 200-500ms (depending on test type)
- **Cache Hit Rate**: 85-95% typical
- **Concurrent Requests**: 50+ requests/second
- **Memory Usage**: ~600MB total system

### Monitoring Endpoints
```bash
# Prometheus-compatible metrics
GET /metrics

# Health check with dependencies
GET /api/health?deep=true

# Performance statistics
GET /api/stats?period=24h
```

### Caching Strategy
```yaml
Cache Key Format: {test_type}_{mikrotik_host}_{target}_{params_hash}
TTL: 30 seconds (configurable)
Memory Limit: 1000 entries (configurable)
Eviction Policy: LRU (Least Recently Used)
```

---

## 🛡️ Security

### Security Best Practices
- Use HTTPS in production with proper certificates
- Implement strong API key rotation policy
- Use dedicated monitoring credentials for MikroTik
- Enable rate limiting and monitoring
- Validate all input parameters

### Input Validation
- IP address format validation
- Parameter range checking
- SQL injection prevention
- Command injection prevention

---

## 📚 SDK & Libraries

### Python SDK Example
```python
import requests

class TriplePlayClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def ping_test(self, mikrotik_host, user, password, target):
        payload = {
            'mikrotik_host': mikrotik_host,
            'mikrotik_user': user,
            'mikrotik_password': password,
            'target': target,
            'test_type': 'ping'
        }
        response = requests.post(
            f'{self.base_url}/api/test',
            json=payload,
            headers=self.headers
        )
        return response.json()

# Usage
client = TriplePlayClient('http://localhost:5000', 'your-api-key')
result = client.ping_test('192.168.1.1', 'admin', 'password', '8.8.8.8')
print(f"Packet loss: {result['results']['ping_stats']['packet_loss_percent']}%")
```

### Bash/cURL Examples
```bash
#!/bin/bash

API_URL="http://localhost:5000/api"
API_KEY="your-api-key"

# Ping test function
ping_test() {
    local mikrotik_host=$1
    local target=$2
    
    curl -s -X POST "${API_URL}/test" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{
            \"mikrotik_host\": \"${mikrotik_host}\",
            \"mikrotik_user\": \"admin\",
            \"mikrotik_password\": \"password\",
            \"target\": \"${target}\",
            \"test_type\": \"ping\"
        }" | jq '.results.ping_stats.packet_loss_percent'
}

# Usage
loss=$(ping_test "192.168.1.1" "8.8.8.8")
echo "Packet loss: ${loss}%"
```

---

## 📋 API Changelog

### v1.0 (Current - 2025-06-23)
- ✅ Production-ready API
- ✅ Ping and traceroute tests
- ✅ Connection testing
- ✅ Redis caching
- ✅ Health monitoring
- ✅ Rate limiting
- ✅ Authentication

### Planned v1.1 (Q3 2025)
- 🔄 Bulk test execution
- 🔄 WebSocket support for real-time monitoring
- 🔄 Advanced filtering and querying
- 🔄 Test scheduling capabilities

---

For more information, see the [complete documentation](../../README.md) and [Zabbix integration guide](../zabbix/ZABBIX_CONFIGURATION.md).