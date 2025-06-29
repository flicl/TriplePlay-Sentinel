# 🆘 TriplePlay-Sentinel Troubleshooting Guide (API-Only)

Guia de solução de problemas para TriplePlay-Sentinel v2.0+ com arquitetura 100% API MikroTik.

## 📋 Problemas Comuns

### 🌐 Conectividade MikroTik API

#### ❌ Problema: "Connection refused" na API
```bash
# 1. Verificar se a API está habilitada
curl -k https://192.168.1.1:8729/rest/system/identity

# 2. Testar porta HTTP se HTTPS falhar
curl http://192.168.1.1:8728/rest/system/identity

# 3. Verificar portas no MikroTik
/ip service print
```

**Solução:**
```bash
# Habilitar API no MikroTik
/ip service enable api
/ip service enable api-ssl

# Definir porta (opcional - use padrão)
/ip service set api port=8728
/ip service set api-ssl port=8729
```

#### ❌ Problema: Timeout na API
```json
{
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "port": 8729,
    "timeout": 60
}
```

**Solução:**
- Aumentar timeout no request
- Verificar latência da rede
- Verificar carga do MikroTik

### 🔑 Autenticação API

#### ❌ Problema: "Login failed"
```bash
# Testar credenciais via API REST
curl -u admin:password -k https://192.168.1.1:8729/rest/system/identity
```

**Solução:**
- Verificar usuário/senha
- Verificar permissões do usuário
- Criar usuário específico para API:

```bash
# No MikroTik
/user add name=api-user password=strong-password group=full
```

### ⚡ Performance e Cache

#### ❌ Problema: Resposta lenta
**Diagnóstico:**
```bash
# Verificar estatísticas da aplicação
curl http://localhost:5000/health

# Verificar pool de conexões
curl http://localhost:5000/api/v2/stats
```

**Solução:**
- Aumentar `MAX_CONNECTIONS_PER_HOST`
- Habilitar cache inteligente
- Usar batch processing

#### ❌ Problema: Cache miss alto
**Configuração recomendada:**
```yaml
environment:
  - CACHE_TTL=30
  - ENABLE_SMART_CACHE=true
  - MAX_CACHE_SIZE=1000
```

### 🐳 Docker Issues

#### ❌ Problema: Container não inicia
```bash
# Verificar logs detalhados
docker logs tripleplay-sentinel-app --tail 50

# Verificar configuração
docker inspect tripleplay-sentinel-app
```

**Soluções comuns:**
1. **Porta em uso:**
   ```bash
   # Usar porta alternativa
   docker run -p 5001:5000 tripleplay-sentinel:latest
   ```

2. **Permissões de rede:**
   ```bash
   # Verificar redes Docker
   docker network ls
   docker network inspect app_network
   ```

### 📊 Monitoramento e Debug

#### ✅ Health Check
```bash
# Verificar saúde da aplicação
curl http://localhost:5000/health
```

#### ✅ Test Conectividade
```bash
# Teste básico de ping
curl -X POST http://localhost:5000/api/v2/mikrotik/ping \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "port": 8729,
    "targets": ["8.8.8.8"]
  }'
```

#### ✅ Debug Mode
```bash
# Executar com debug
docker run -e FLASK_DEBUG=true tripleplay-sentinel:latest
```

## 🔧 Configurações Recomendadas

### Performance Máxima
```yaml
environment:
  - MAX_CONCURRENT_HOSTS=100
  - MAX_CONNECTIONS_PER_HOST=20
  - MAX_CONCURRENT_COMMANDS=50
  - CACHE_TTL=60
  - ENABLE_SMART_CACHE=true
```

### Ambientes com Limitações
```yaml
environment:
  - MAX_CONCURRENT_HOSTS=10
  - MAX_CONNECTIONS_PER_HOST=5
  - MAX_CONCURRENT_COMMANDS=10
  - MIKROTIK_API_TIMEOUT=60
```

## 🆘 Support

### Verificar Versão
```bash
curl http://localhost:5000/health | jq .version
```

### Logs Importantes
```bash
# Container logs
docker logs tripleplay-sentinel-app --tail 100

# Application logs
docker exec tripleplay-sentinel-app tail -f /app/sentinel-api.log
```

### Coleta de Diagnóstico
```bash
#!/bin/bash
echo "=== TriplePlay-Sentinel Diagnostic ==="
echo "Version: $(curl -s http://localhost:5000/health | jq -r .version)"
echo "Status: $(curl -s http://localhost:5000/health | jq -r .status)"
echo "Performance: $(curl -s http://localhost:5000/health | jq .performance)"
echo "Docker: $(docker --version)"
echo "Networks: $(docker network ls)"
```

## 📚 Links Úteis

- [Guia Docker Manual](../guides/docker_run_manual.md)
- [Configuração MikroTik](../guides/mikrotik_setup.md)
- [API Reference](../api/collector_api.md)
- [Sistema Architecture](../architecture/system_architecture.md)

---
**Nota:** Esta versão é otimizada para arquitetura API-only (v2.0+). Para versões antigas com SSH, consulte documentação legacy.
