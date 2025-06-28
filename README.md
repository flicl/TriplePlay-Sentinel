# TriplePlay-Sentinel

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![API](https://img.shields.io/badge/API-REST-green.svg)](https://restfulapi.net/)

**TriplePlay-Sentinel** is a high-performance network monitoring system designed specifically for **MikroTik** devices. Built with a modern **API-first architecture**, it provides real-time monitoring, parallel command execution, and intelligent caching for enterprise-grade network management.

## 🚀 Key Features

### **API-Only Architecture (v2.0+)**
- 🔥 **100% MikroTik API** - No SSH dependencies
- ⚡ **librouteros** - Native Python library for optimal performance
- 🏊 **Connection Pooling** - Efficient resource management
- 📦 **Batch Processing** - Execute multiple commands simultaneously
- 🔒 **SSL/TLS Support** - Secure API connections
- 🧠 **Intelligent Caching** - Configurable TTL for performance optimization

### **High Performance & Scalability**
- 🚄 **Asynchronous Operations** - Non-blocking I/O for maximum throughput
- 🔧 **Configurable Concurrency** - Tune for your infrastructure
- 📊 **Real-time Metrics** - Monitor system performance
- 🎯 **Load Balancing** - Distribute requests across connections
- 📈 **Auto-scaling** - Dynamic resource allocation

### **Enterprise Ready**
- 🐳 **Docker Support** - Container-ready deployment
- 🔐 **Authentication** - API key and bearer token support
- 📝 **Comprehensive Logging** - Structured logging with multiple levels
- 🩺 **Health Checks** - Built-in monitoring endpoints
- 📚 **REST API** - Full OpenAPI specification
- 🌐 **CORS Support** - Cross-origin resource sharing

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Apps   │    │  Load Balancer   │    │   MikroTik      │
│   (REST API)    │◄──►│   (Optional)     │◄──►│   Devices       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│TriplePlay       │    │   Connection     │    │  API Endpoints  │
│ Sentinel API    │◄──►│   Pool Manager   │◄──►│  (8728/8729)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Redis Cache    │    │   Batch          │
│  (Optional)     │    │   Processor      │
└─────────────────┘    └──────────────────┘
```

## 📦 Installation

### **Prerequisites**
- Python 3.11+
- Docker (recommended)
- MikroTik device with API enabled

### **Quick Start with Docker**

```bash
# Clone the repository
git clone https://github.com/flicl/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel

# Build and run with Docker
cd src/collector
docker build -t tripleplay-sentinel:latest .
docker run -d -p 5000:5000 --name sentinel tripleplay-sentinel:latest
```

### **Development Installation**

```bash
# Clone and setup
git clone https://github.com/flicl/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel/src/collector

# Install dependencies
pip install -r requirements.txt

# Run the application
python sentinel_api_server.py
```

## 🔧 Configuration

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `COLLECTOR_HOST` | `0.0.0.0` | API server bind address |
| `COLLECTOR_PORT` | `5000` | API server port |
| `MIKROTIK_API_PORT` | `8728` | MikroTik API port |
| `MIKROTIK_USE_SSL` | `false` | Use SSL for MikroTik API |
| `POOL_SIZE` | `10` | Connection pool size |
| `MAX_BATCH_SIZE` | `50` | Maximum batch size |
| `CACHE_TTL` | `30` | Cache TTL in seconds |
| `LOG_LEVEL` | `INFO` | Logging level |

### **MikroTik Configuration**

Enable the API on your MikroTik device:

```bash
# Enable API service
/ip service enable api
/ip service set api port=8728

# For SSL (recommended for production)
/ip service enable api-ssl  
/ip service set api-ssl port=8729
```

## 📋 API Reference

### **Base URL**
```
http://localhost:5000/api/v2
```

### **Authentication (Optional)**
```bash
# Using API Key header
curl -H \"X-API-Key: your-api-key\" ...

# Using Bearer token
curl -H \"Authorization: Bearer your-api-key\" ...
```

### **Core Endpoints**

#### **Test Connection**
```bash
POST /api/v2/test-connection
Content-Type: application/json

{
  \"host\": \"192.168.1.1\",
  \"username\": \"admin\",
  \"password\": \"password\"
}
```

#### **Parallel Ping**
```bash
POST /api/v2/mikrotik/ping
Content-Type: application/json

{
  \"host\": \"192.168.1.1\",
  \"username\": \"admin\", 
  \"password\": \"password\",
  \"targets\": [\"8.8.8.8\", \"1.1.1.1\"],
  \"count\": 4,
  \"use_cache\": true
}
```

#### **Batch Commands**
```bash
POST /api/v2/mikrotik/batch
Content-Type: application/json

{
  \"host\": \"192.168.1.1\",
  \"username\": \"admin\",
  \"password\": \"password\", 
  \"commands\": [
    {
      \"command\": \"/system/identity/print\",
      \"parameters\": {},
      \"use_cache\": true
    }
  ],
  \"max_concurrent\": 4
}
```

#### **System Statistics**
```bash
GET /api/v2/stats
```

## 💻 Usage Examples

### **Python Client**

```python
from sentinel_client import TriplePlaySentinelClient

# Initialize client
client = TriplePlaySentinelClient(
    base_url=\"http://localhost:5000\",
    api_key=\"your-api-key\"  # Optional
)

# Test connection
mikrotik_config = {
    \"host\": \"192.168.1.1\",
    \"username\": \"admin\",
    \"password\": \"password\"
}

success = client.test_connection(mikrotik_config)
if success:
    # Execute parallel ping
    result = client.ping_multiple_targets(
        mikrotik_config, 
        targets=[\"8.8.8.8\", \"1.1.1.1\"]
    )
    print(f\"Ping completed: {result['targets_successful']} successful\")
```

### **Command Line**

```bash
# Run demonstration
python sentinel_client.py --mikrotik-host 192.168.1.1

# With custom settings
python sentinel_client.py \\
  --url http://my-server:5000 \\
  --mikrotik-host 10.0.0.1 \\
  --mikrotik-user monitor \\
  --api-key my-secret-key
```

## 🔍 Monitoring & Observability

### **Health Check**
```bash
curl http://localhost:5000/health
```

### **Performance Metrics**
```bash
curl http://localhost:5000/api/v2/stats
```

### **Logging**
- Structured JSON logging
- Configurable log levels
- Request tracing
- Performance metrics

## 🚀 Performance

### **Benchmarks**
- **Concurrent Connections**: 100+ simultaneous MikroTik connections
- **Throughput**: 1000+ commands/second
- **Latency**: <50ms average response time
- **Memory Usage**: <512MB typical operation

### **Optimization Tips**
1. **Tune Pool Size**: Adjust `POOL_SIZE` based on your device count
2. **Enable Caching**: Use appropriate `CACHE_TTL` for your use case  
3. **Batch Operations**: Group related commands for better performance
4. **SSL Configuration**: Use SSL certificates for production deployments

## 🛠️ Development

### **Project Structure**
```
TriplePlay-Sentinel/
├── src/collector/           # Main application
│   ├── sentinel_api_server.py     # Flask API application
│   ├── mikrotik_connector.py  # MikroTik connector
│   ├── sentinel_config.py  # Configuration management
│   └── sentinel_client.py # Client example
├── docs/                   # Documentation
├── templates/              # Zabbix templates
└── docker-compose.yml      # Container orchestration
```

### **Running Tests**
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/flicl/TriplePlay-Sentinel/issues)
- **Discussions**: [GitHub Discussions](https://github.com/flicl/TriplePlay-Sentinel/discussions)

## 🙏 Acknowledgments

- **librouteros** - High-performance MikroTik API library
- **Flask** - Lightweight web framework
- **asyncio** - Asynchronous I/O support
- **Docker** - Containerization platform

---

**Made with ❤️ for network administrators and DevOps engineers**
