# 🆘 Troubleshooting Guide

## Índice de Problemas

### 🌐 [Problemas de Rede](#problemas-de-rede)
- [Conectividade MikroTik](#conectividade-mikrotik)
- [Latência Alta](#latência-alta)
- [Perda de Pacotes](#perda-de-pacotes)
- [DNS Resolution](#dns-resolution)

### 🔌 [Problemas de API](#problemas-de-api)
- [Collector API não responde](#collector-api-não-responde)
- [RouterOS API falha](#routeros-api-falha)
- [Timeouts](#timeouts)
- [Autenticação](#autenticação)

### 🎯 [Problemas do Zabbix](#problemas-do-zabbix)
- [HTTP Agent Items](#http-agent-items)
- [JSONPath Errors](#jsonpath-errors)
- [Triggers não disparam](#triggers-não-disparam)
- [Performance Issues](#performance-issues)

### ⚡ [Problemas de Cache](#problemas-de-cache)
- [Cache Miss Alto](#cache-miss-alto)
- [Memória Alta](#memória-alta)
- [Dados Desatualizados](#dados-desatualizados)

### 🐳 [Problemas Docker](#problemas-docker)
- [Container não inicia](#container-não-inicia)
- [Networking Issues](#networking-issues)
- [Performance Container](#performance-container)

---

## 🌐 Problemas de Rede

### Conectividade MikroTik

#### **Sintoma**: Erro "Connection refused" ou "Timeout"
```json
{
  "status": "error",
  "error_code": "MIKROTIK_CONNECTION_FAILED",
  "error_message": "Failed to connect to MikroTik device"
}
```

#### **Diagnóstico**:
```bash
# 1. Teste conectividade básica
ping 192.168.1.1

# 2. Teste portas específicas
nmap -p 22,8728,8729 192.168.1.1

# 3. Teste SSH manual
ssh admin@192.168.1.1

# 4. Teste API manual
curl -X POST http://collector:5000/api/v1/debug/connection \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host": "192.168.1.1", "mikrotik_user": "admin"}'
```

#### **Soluções**:

##### ✅ **Verificar Serviços MikroTik**
```routeros
# No MikroTik, verificar serviços habilitados
/ip service print

# Habilitar SSH se necessário
/ip service enable ssh

# Habilitar API se necessário  
/ip service enable api

# Verificar configuração de firewall
/ip firewall filter print where chain=input
```

##### ✅ **Configurar Firewall**
```routeros
# Adicionar regra para permitir conexões do Collector
/ip firewall filter add chain=input action=accept \
  src-address=192.168.1.100/32 dst-port=22,8728 protocol=tcp \
  comment="Sentinel Collector Access"
```

##### ✅ **Verificar Credenciais**
```routeros
# Verificar usuário existe
/user print

# Verificar permissões do grupo
/user group print detail

# Criar usuário específico se necessário
/user group add name=monitoring policy=read,test
/user add name=sentinel-monitor group=monitoring password=secure_pass
```

---

### Latência Alta

#### **Sintoma**: Ping average > 100ms consistentemente
```json
{
  "results": {
    "avg_time_ms": 250.5,
    "max_time_ms": 450.2,
    "jitter_ms": 85.3
  }
}
```

#### **Diagnóstico**:
```bash
# 1. Teste direto do servidor
ping -c 10 8.8.8.8

# 2. Traceroute para identificar gargalos
traceroute 8.8.8.8

# 3. Teste diferentes targets
for target in 8.8.8.8 1.1.1.1 208.67.222.222; do
  echo "Testing $target:"
  ping -c 5 $target
done

# 4. Verificar carga do MikroTik
ssh admin@192.168.1.1 '/system resource print'
```

#### **Soluções**:

##### ✅ **Otimizar Route Table**
```routeros
# Verificar rotas
/ip route print

# Otimizar rota padrão se necessário
/ip route set [find dst-address=0.0.0.0/0] gateway=192.168.1.1
```

##### ✅ **Verificar Interface Status**
```routeros
# Verificar interfaces
/interface print stats

# Verificar erros
/interface monitor-traffic interface=ether1 once
```

##### ✅ **QoS Configuration**
```routeros
# Configurar QoS básico para testes de monitoramento
/queue simple add name=monitoring-priority \
  dst=sentinel-collector priority=1 max-limit=10M/10M
```

---

### Perda de Pacotes

#### **Sintoma**: packet_loss_percent > 0% consistente
```json
{
  "results": {
    "packets_sent": 4,
    "packets_received": 3,
    "packet_loss_percent": 25.0
  }
}
```

#### **Diagnóstico**:
```bash
# 1. Teste perda de pacotes do collector
mtr --report --report-cycles=100 8.8.8.8

# 2. Verificar interface errors
ssh admin@192.168.1.1 '/interface print stats'

# 3. Teste diferentes tamanhos de pacote
for size in 64 128 256 512 1024 1472; do
  echo "Testing packet size $size:"
  ping -c 10 -s $size 8.8.8.8
done
```

#### **Soluções**:

##### ✅ **Verificar MTU**
```routeros
# Verificar MTU das interfaces
/interface print detail

# Ajustar MTU se necessário
/interface set ether1 mtu=1500
```

##### ✅ **Verificar Buffer Sizes**
```routeros
# Verificar drops em interfaces
/interface print stats

# Ajustar buffer sizes se necessário
/interface set ether1 tx-ring-size=1024 rx-ring-size=1024
```

---

## 🔌 Problemas de API

### Collector API não responde

#### **Sintoma**: HTTP 502/503 ou timeout no Zabbix
```
HTTP/1.1 503 Service Unavailable
Connection: close
```

#### **Diagnóstico**:
```bash
# 1. Verificar status do container
docker ps | grep sentinel
docker logs sentinel-collector

# 2. Teste direto da API
curl -v http://localhost:5000/api/v1/health

# 3. Verificar recursos do sistema
docker stats sentinel-collector

# 4. Verificar logs detalhados
docker logs --tail=100 -f sentinel-collector
```

#### **Soluções**:

##### ✅ **Restart Container**
```bash
# Restart graceful
docker-compose restart collector

# Rebuild se necessário
docker-compose down
docker-compose up --build -d
```

##### ✅ **Verificar Resources**
```yaml
# docker-compose.yml - adicionar limits
services:
  collector:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
```

##### ✅ **Debug Mode**
```bash
# Executar em modo debug
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up
```

---

### RouterOS API falha

#### **Sintoma**: Erro específico da API RouterOS
```json
{
  "status": "error",
  "error_code": "MIKROTIK_COMMAND_FAILED", 
  "error_message": "Command execution failed",
  "details": {
    "command": "/ping",
    "mikrotik_error": "invalid command name"
  }
}
```

#### **Diagnóstico**:
```bash
# 1. Teste comando manual via SSH
ssh admin@192.168.1.1
> /ping 8.8.8.8 count=1

# 2. Verificar versão RouterOS
ssh admin@192.168.1.1 '/system package update print'

# 3. Teste API diretamente
python3 -c "
import librouteros
conn = librouteros.connect('192.168.1.1', username='admin', password='pass')
print(list(conn('/ping', address='8.8.8.8', count='1')))
"
```

#### **Soluções**:

##### ✅ **Verificar Compatibilidade de Comando**
```python
# Versões antigas podem ter sintaxe diferente
COMMAND_MAP = {
    'v6': '/ping address=8.8.8.8 count=4',
    'v7': '/ping 8.8.8.8 count=4'
}
```

##### ✅ **Fallback para SSH**
```python
# Implementar fallback automático para SSH
if routeros_api_fails:
    use_ssh_connection()
```

---

## 🎯 Problemas do Zabbix

### HTTP Agent Items

#### **Sintoma**: Item fica "Not supported" no Zabbix
```
Item not supported: HTTP agent error: Connection refused
```

#### **Diagnóstico**:
```bash
# 1. Teste manual do HTTP Agent
curl -X POST "http://collector:5000/api/v1/tests/ping" \
  -H "Authorization: Bearer API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host":"192.168.1.1","target":"8.8.8.8"}'

# 2. Verificar logs do Zabbix
tail -f /var/log/zabbix/zabbix_server.log | grep -i "http agent"

# 3. Teste DNS resolution
nslookup collector
```

#### **Soluções**:

##### ✅ **Verificar URL do Collector**
```bash
# No Zabbix, verificar macro {$SENTINEL_URL}
# Deve ser acessível do Zabbix Server

# Teste de conectividade do Zabbix Server
docker exec zabbix-server curl http://collector:5000/api/v1/health
```

##### ✅ **Verificar Headers**
```yaml
# Item configuration
Headers:
  Authorization: Bearer {$SENTINEL_API_KEY}
  Content-Type: application/json
  User-Agent: Zabbix
```

##### ✅ **Timeout Configuration**
```yaml
# Aumentar timeout se necessário
Timeout: 30s
Update interval: 60s
```

---

### JSONPath Errors

#### **Sintoma**: Dependent items falham com erro JSONPath
```
JSONPath error: No data matches expression
```

#### **Diagnóstico**:
```bash
# 1. Verificar resposta real da API
curl -s http://collector:5000/api/v1/tests/ping \
  -H "Authorization: Bearer API_KEY" \
  -d '{"mikrotik_host":"192.168.1.1","target":"8.8.8.8"}' | jq .

# 2. Testar JSONPath expressions
echo '{"results":{"avg_time_ms":15.5}}' | jq '.results.avg_time_ms'
```

#### **Soluções**:

##### ✅ **Verificar Response Format**
```json
// Response esperada
{
  "status": "success",
  "results": {
    "avg_time_ms": 15.5,
    "packet_loss_percent": 0
  }
}

// JSONPath correto
$.results.avg_time_ms
$.results.packet_loss_percent
```

##### ✅ **Error Handling no JSONPath**
```yaml
# Preprocessing steps
1. JSONPath: $.results.avg_time_ms
   Custom on fail: Discard value

2. Check for error:
   Pattern: $.status
   Custom on fail: Set error to "API Error"
```

---

## ⚡ Problemas de Cache

### Cache Miss Alto

#### **Sintoma**: Hit rate < 50%
```json
{
  "hit_rate": 0.35,
  "hit_count": 350,
  "miss_count": 650
}
```

#### **Diagnóstico**:
```bash
# 1. Verificar métricas de cache
curl http://collector:5000/api/v1/cache/metrics | jq .

# 2. Verificar TTL configuration
grep -i cache /app/config/.env

# 3. Verificar padrão de requisições
tail -f /var/log/collector/requests.log | grep -E "(GET|POST)"
```

#### **Soluções**:

##### ✅ **Ajustar TTL**
```bash
# Aumentar TTL para testes menos críticos
CACHE_PING_TTL=60
CACHE_TCP_TTL=120  
CACHE_TRACEROUTE_TTL=300
```

##### ✅ **Otimizar Cache Keys**
```python
# Normalizar parâmetros para melhor cache hit
def normalize_cache_params(params):
    # Remove timestamp, credentials
    return {k: v for k, v in params.items() 
            if k not in ['timestamp', 'mikrotik_password']}
```

---

### Memória Alta

#### **Sintoma**: Uso de memória > 100MB
```json
{
  "memory_usage_mb": 150.5,
  "entries": {
    "total": 1500,
    "expired": 300
  }
}
```

#### **Soluções**:

##### ✅ **Reduzir Max Entries**
```bash
CACHE_MAX_ENTRIES=500
CACHE_CLEANUP_INTERVAL=180
```

##### ✅ **Enable Compression**
```bash
CACHE_COMPRESSION_ENABLED=true
CACHE_COMPRESSION_LEVEL=6
```

---

## 🐳 Problemas Docker

### Container não inicia

#### **Diagnóstico**:
```bash
# 1. Verificar logs de startup
docker-compose logs collector

# 2. Verificar dependencies
docker-compose ps

# 3. Verificar health checks
docker inspect sentinel-collector | jq '.[0].State.Health'
```

#### **Soluções**:

##### ✅ **Check Dependencies**
```yaml
# docker-compose.yml
services:
  collector:
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 📊 Ferramentas de Debug

### Debug Scripts
```bash
#!/bin/bash
# debug-collector.sh

echo "=== Collector Debug Information ==="

echo "1. Container Status:"
docker ps | grep sentinel

echo "2. Health Check:"
curl -s http://localhost:5000/api/v1/health | jq .

echo "3. Cache Metrics:"
curl -s http://localhost:5000/api/v1/cache/metrics | jq .

echo "4. Recent Logs:"
docker logs --tail=20 sentinel-collector

echo "5. Resource Usage:"
docker stats --no-stream sentinel-collector

echo "6. Network Connectivity:"
docker exec sentinel-collector ping -c 3 192.168.1.1
```

### Health Check Endpoint
```python
@app.route('/api/v1/debug/full', methods=['GET'])
def full_debug():
    """Debug completo do sistema"""
    
    return jsonify({
        'timestamp': time.time(),
        'system': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
            'disk_usage': psutil.disk_usage('/').percent
        },
        'cache': cache_manager.get_metrics(),
        'connections': {
            'active_mikrotik': len(connection_pool.active_connections),
            'pool_size': connection_pool.max_size
        },
        'recent_errors': error_tracker.get_recent_errors(),
        'performance': {
            'avg_response_time_ms': performance_monitor.avg_response_time,
            'requests_per_minute': performance_monitor.requests_per_minute
        }
    })
```

---

**🚨 Emergency Procedures**: Para problemas críticos, execute o [Emergency Recovery Guide](troubleshooting/emergency_recovery.md)
