# 🐳 Docker Setup Simples - TriplePlay-Sentinel

## 🎯 Arquitetura Minimal

O TriplePlay-Sentinel utiliza uma arquitetura **ultra-simplificada** com apenas 2 serviços essenciais:

### ✅ Serviços Ativos

#### 1. 🚀 **TriplePlay-Sentinel Collector**
- Core da aplicação
- API REST para Zabbix
- Dashboard web integrado
- Processamento SSH para MikroTik

#### 2. 📦 **Redis Cache**
- Cache distribuído de alta performance
- Persistência de dados
- Otimização de consultas SSH

## 🚀 Setup Completo (2 comandos!)

### Produção - Deploy Rápido
```bash
# 1. Clone e configure
git clone <repo-url> && cd TriplePlay-Sentinel
cp .env.example .env

# 2. Start containers
docker-compose up --build -d

# ✅ Sistema online em http://localhost:5000
```

### Desenvolvimento
```bash
# Com logs em tempo real
docker-compose up --build

# Background
docker-compose up --build -d

# Parar
docker-compose down
```

## ⚙️ Configuração

### Arquivo `.env`
```bash
# Cache Redis
REDIS_PASSWORD=

# Segurança (opcional)
ENABLE_AUTH=false
API_KEY=

# Performance
CACHE_TTL=30
LOG_LEVEL=INFO
```

### Variáveis de Ambiente
```yaml
# No docker-compose.yml
environment:
  COLLECTOR_HOST: 0.0.0.0
  COLLECTOR_PORT: 5000
  REDIS_ENABLED: true
  REDIS_HOST: redis
  CACHE_TTL: 30
  SSH_TIMEOUT: 30
  MAX_WORKERS: 10
```

## 🔍 Verificação

### Status dos Containers
```bash
# Ver status
docker-compose ps

# Health check
curl http://localhost:5000/api/health

# Logs
docker-compose logs -f sentinel-collector
```

### Teste Completo
```bash
# Teste de ping via API
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

## 📊 Monitoramento

### Dashboard Web
- **URL**: http://localhost:5000/dashboard
- **Funcionalidades**:
  - Status do sistema
  - Estatísticas de cache
  - Teste manual de conectividade
  - Métricas de performance

### API Endpoints
```bash
# Health check
GET /api/health

# Estatísticas  
GET /api/stats

# Teste de conectividade
POST /api/test

# Teste de conexão SSH
POST /api/connection-test
```

### Logs e Debug
```bash
# Logs da aplicação
docker-compose logs -f sentinel-collector

# Logs do Redis
docker-compose logs -f redis

# Acesso direto ao container
docker exec -it tripleplay-sentinel-collector /bin/bash
```

## 🔧 Troubleshooting

### Container não inicia
```bash
# Verificar logs
docker-compose logs sentinel-collector

# Rebuild forçado
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Redis não conecta
```bash
# Testar Redis
docker exec -it tripleplay-redis redis-cli ping

# Verificar network
docker network ls
docker inspect tripleplay-sentinel
```

### Performance Issues
```bash
# Verificar recursos
docker stats

# Ajustar limits no docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
```

## 🚀 Produção

### Configurações Recomendadas
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  sentinel-collector:
    restart: always
    environment:
      LOG_LEVEL: WARNING
      CACHE_TTL: 60
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
          
  redis:
    restart: always
    command: >
      redis-server 
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --requirepass ${REDIS_PASSWORD}
```

### Deploy Produção
```bash
# Override para produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Backup Redis
docker exec tripleplay-redis redis-cli BGSAVE
```

## 📋 Manutenção

### Backup e Restore
```bash
# Backup logs
docker cp tripleplay-sentinel-collector:/app/logs ./backup/

# Backup Redis data
docker exec tripleplay-redis redis-cli BGSAVE
docker cp tripleplay-redis:/data/dump.rdb ./backup/
```

### Updates
```bash
# Pull nova versão
git pull

# Rebuild e restart
docker-compose down
docker-compose up --build -d
```

### Limpeza
```bash
# Remover containers parados
docker-compose down --remove-orphans

# Limpar volumes (CUIDADO!)
docker-compose down -v

# Limpar imagens antigas
docker image prune -a
```

---

## 🎯 Próximos Passos

1. ✅ Sistema online
2. ⚙️ Configure credenciais MikroTik no Zabbix
3. 📥 Importe template Zabbix (`templates/zabbix/`)
4. 🔧 Configure items de monitoramento
5. 📊 Acesse dashboard em http://localhost:5000/dashboard

**Sistema pronto para produção!** 🚀